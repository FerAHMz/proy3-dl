"""Evaluación de Ojo Chapín sobre el conjunto propio.

Uso:
    python -m ojo.evaluar --iter B1 B2 L1 L2 L3 L4 L5 --split test
    python -m ojo.evaluar --recuperacion

Cada iteración se guarda como una fila en resultados/iteraciones.csv y sus predicciones en
resultados/predicciones/<id>.jsonl.
"""
import argparse
import json
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd

from .baselines import clasificar_reglas, entrenar_tfidf, tfidf_validacion_cruzada
from .config import EVALUACION_PATH, REALES_PATH, RESULTADOS
from .llm import VERSIONES
from .pipeline import analizar
from .recuperacion import buscar
from .preproceso import normalizar

ITERACIONES = {
    "B1": {"desc": "Baseline sin LLM, reglas sobre las señales extraídas", "tipo": "reglas"},
    "B2": {"desc": "Baseline sin LLM, TF-IDF + regresión logística (validación cruzada de 5 folds)", "tipo": "tfidf"},
    "L1": {"desc": "Haiku 5.5, prompt simple sin sistema (responde SI o NO)", "version": "v1"},
    "L2": {"desc": "L1 + prompt de sistema con criterios y salida JSON estructurada", "version": "v2"},
    "L3": {"desc": "L2 + señales extraídas en el preprocesamiento", "version": "v3"},
    "L4": {"desc": "L3 + RAG con los 3 patrones más parecidos (e5-small, coseno)", "version": "v4"},
    "L5": {"desc": "L4 + 5 ejemplos few-shot del conjunto de desarrollo", "version": "v5"},
    "L6": {"desc": "L5 con criterio más estricto para 'sospechoso' en el prompt de sistema (v6)", "version": "v6"},
    "L7": {"desc": "L6 con el razonamiento del modelo apagado", "version": "v6", "razonamiento": "apagado"},
    "L8": {"desc": "L6 con effort medium en lugar de low", "version": "v6", "effort": "medium"},
}
INYECCION = {"t27", "t28"}


def cargar(split: str) -> list[dict]:
    ruta = REALES_PATH if split == "reales" else EVALUACION_PATH
    filas = [json.loads(l) for l in ruta.read_text(encoding="utf-8").splitlines() if l.strip()]
    return [f for f in filas if split == "todo" or f["split"] == split]


def metricas(casos: list[dict], preds: list[dict]) -> dict:
    y = np.array([c["es_estafa"] for c in casos])
    alerta = np.array([p["veredicto"] in ("estafa", "sospechoso") for p in preds]).astype(int)
    estricto = np.array([p["veredicto"] == "estafa" for p in preds]).astype(int)

    def prf(pred):
        tp = int(((pred == 1) & (y == 1)).sum()); fp = int(((pred == 1) & (y == 0)).sum())
        fn = int(((pred == 0) & (y == 1)).sum()); tn = int(((pred == 0) & (y == 0)).sum())
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
        return {"exactitud": (tp + tn) / len(y), "precision": prec, "recall": rec, "f1": f1,
                "tasa_falsas_alarmas": fp / (fp + tn) if fp + tn else 0.0, "fp": fp, "fn": fn}

    m = prf(alerta)
    m["f1_estricto"] = prf(estricto)["f1"]
    con_tipo = [(c, p) for c, p in zip(casos, preds) if c["es_estafa"] and "tipo" in p]
    m["exactitud_tipo"] = (np.mean([p["tipo"] == c["tipo"] for c, p in con_tipo]) if con_tipo else np.nan)
    validos = [p["json_valido"] for p in preds if p.get("json_valido") is not None]
    m["json_valido"] = np.mean(validos) if validos else np.nan
    m["inyeccion_detectada"] = sum(1 for c, p in zip(casos, preds)
                                   if c["id"] in INYECCION and p["veredicto"] in ("estafa", "sospechoso"))
    for campo in ["latencia_s", "tokens_entrada", "tokens_salida", "costo_usd"]:
        valores = [p[campo] for p in preds if campo in p]
        m[f"{campo}_prom"] = float(np.mean(valores)) if valores else np.nan
    lat = [p["latencia_s"] for p in preds if "latencia_s" in p]
    m["latencia_p95_s"] = float(np.percentile(lat, 95)) if lat else np.nan
    m["costo_total_usd"] = float(np.sum([p.get("costo_usd", 0) for p in preds]))
    m["respaldo"] = sum(1 for p in preds if p.get("modo_respaldo"))
    return m


def correr_iteracion(it: str, casos: list[dict], hilos: int = 6) -> list[dict]:
    cfg = ITERACIONES[it]
    if cfg.get("tipo") == "reglas":
        preds = []
        for c in casos:
            t0 = time.perf_counter()
            r = clasificar_reglas(c["texto"], c["remitente"])
            preds.append({**r, "latencia_s": time.perf_counter() - t0, "costo_usd": 0.0})
        return preds
    if cfg.get("tipo") == "tfidf":
        textos = [f"remitente {c['remitente']} {normalizar(c['texto'])}" for c in casos]
        if len({c["es_estafa"] for c in casos}) < 2:
            # Conjunto de reales (solo estafas): se entrena con los 80 mensajes etiquetados.
            entrenamiento = cargar("todo")
            pred = entrenar_tfidf([f"remitente {c['remitente']} {normalizar(c['texto'])}" for c in entrenamiento],
                                  [c["es_estafa"] for c in entrenamiento]).predict(textos)
        else:
            pred = tfidf_validacion_cruzada(textos, [c["es_estafa"] for c in casos])
        return [{"veredicto": "estafa" if p else "seguro", "costo_usd": 0.0} for p in pred]

    if VERSIONES[cfg["version"]]["rag"]:
        buscar("precarga")   # carga el modelo de embeddings una vez, antes de los hilos

    def uno(c):
        return analizar(c["texto"], c["remitente"], version=cfg["version"],
                        effort=cfg.get("effort", "low"), razonamiento=cfg.get("razonamiento", "adaptativo"))

    with ThreadPoolExecutor(max_workers=hilos) as ex:
        return list(ex.map(uno, casos))


def guardar(it: str, casos: list[dict], preds: list[dict], m: dict, split: str):
    carpeta = RESULTADOS / "predicciones" / split
    carpeta.mkdir(parents=True, exist_ok=True)
    with open(carpeta / f"{it}.jsonl", "w", encoding="utf-8") as f:
        for c, p in zip(casos, preds):
            fila = {"id": c["id"], "es_estafa": c["es_estafa"], "tipo_real": c["tipo"],
                    **{k: v for k, v in p.items() if k not in ("patrones", "enlaces")}}
            if p.get("patrones"):
                fila["patrones"] = [q["id"] for q in p["patrones"]]
            f.write(json.dumps(fila, ensure_ascii=False) + "\n")
    ruta = RESULTADOS / "iteraciones.csv"
    tabla = pd.read_csv(ruta) if ruta.exists() else pd.DataFrame()
    fila = {"id": it, "descripcion": ITERACIONES[it]["desc"], "split": split, "n": len(casos), **m}
    tabla = tabla[~((tabla["id"] == it) & (tabla["split"] == split))] if len(tabla) else tabla
    tabla = pd.concat([tabla, pd.DataFrame([fila])], ignore_index=True).sort_values(["split", "id"])
    tabla.to_csv(ruta, index=False)


def evaluar_recuperacion():
    """Recall@k y MRR de la recuperación de patrones para dos modelos de embeddings."""
    from .recuperacion import construir_indice, cargar_modelo, _prefijos
    casos = [c for c in cargar("test") + cargar("reales") if c["es_estafa"]]
    filas = []
    for modelo in ["sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", "intfloat/multilingual-e5-small"]:
        vec, ids = construir_indice(modelo, guardar=False)
        pq, _ = _prefijos(modelo)
        rr, h1, h3 = [], 0, 0
        for c in casos:
            q = cargar_modelo(modelo).encode([pq + normalizar(c["texto"])], normalize_embeddings=True)[0]
            orden = [str(ids[i]) for i in np.argsort(-(vec @ q))]
            pos = orden.index(c["tipo"]) + 1
            rr.append(1 / pos); h1 += pos <= 1; h3 += pos <= 3
        filas.append({"modelo_embeddings": modelo, "dimension": vec.shape[1], "n": len(casos),
                      "recall@1": h1 / len(casos), "recall@3": h3 / len(casos), "mrr": float(np.mean(rr))})
    RESULTADOS.mkdir(exist_ok=True)
    pd.DataFrame(filas).to_csv(RESULTADOS / "recuperacion.csv", index=False)
    print(pd.DataFrame(filas).to_string(index=False))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--iter", nargs="*", default=[])
    ap.add_argument("--split", default="test")
    ap.add_argument("--recuperacion", action="store_true")
    args = ap.parse_args()
    if args.recuperacion:
        evaluar_recuperacion()
    casos = cargar(args.split)
    for it in args.iter:
        t0 = time.perf_counter()
        preds = correr_iteracion(it, casos)
        m = metricas(casos, preds)
        guardar(it, casos, preds, m, args.split)
        print(f"{it}: F1 {m['f1']:.3f} | exactitud {m['exactitud']:.3f} | precisión {m['precision']:.3f} | "
              f"recall {m['recall']:.3f} | falsas alarmas {m['tasa_falsas_alarmas']:.3f} | "
              f"latencia {m['latencia_s_prom']:.2f}s | costo total ${m['costo_total_usd']:.4f} "
              f"| respaldo {m['respaldo']} | {time.perf_counter() - t0:.0f}s")


if __name__ == "__main__":
    main()
