"""Baselines sin LLM para comparar: un sistema de reglas y TF-IDF con regresión logística."""
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline, make_union

from .preproceso import extraer_senales

# Pesos de cada señal en el sistema de reglas (ajustados solo con el conjunto de desarrollo).
PESOS = {"pide_codigo": 1, "pide_pago": 1, "urgencia": 1, "premio": 2, "amenaza": 2, "secreto": 2,
         "ganancia_facil": 2, "numero_nuevo": 2, "cuenta_bancaria": 1, "numero_internacional": 1}
UMBRAL = 3


def puntaje_reglas(texto: str, remitente: str = "nose") -> int:
    s = extraer_senales(texto, remitente)
    puntaje = sum(peso for clave, peso in PESOS.items() if s.get(clave))
    for e in s["enlaces"]:
        puntaje += 3 if (e["imita_marca"] or e["archivo_apk"]) else 0
        puntaje += 2 if (e["acortador"] or e["tld_sospechoso"]) else 0
        puntaje -= 2 if e["oficial"] else 0
    puntaje -= 2 if remitente in ("contacto", "empresa") else 0
    return puntaje


def clasificar_reglas(texto: str, remitente: str = "nose") -> dict:
    p = puntaje_reglas(texto, remitente)
    veredicto = "estafa" if p >= UMBRAL else ("sospechoso" if p >= UMBRAL - 1 else "seguro")
    return {"veredicto": veredicto, "puntaje": p}


def entrenar_tfidf(textos: list[str], y: list[int]):
    """TF-IDF de palabras y n-gramas de caracteres + regresión logística."""
    modelo = make_pipeline(
        make_union(TfidfVectorizer(lowercase=True, ngram_range=(1, 2)),
                   TfidfVectorizer(lowercase=True, analyzer="char_wb", ngram_range=(2, 5))),
        LogisticRegression(max_iter=2000, C=4.0),
    )
    return modelo.fit(textos, y)


def tfidf_validacion_cruzada(textos: list[str], y: list[int], k: int = 5, semilla: int = 42) -> np.ndarray:
    """Predicciones fuera de muestra de TF-IDF (palabras y n-gramas de caracteres) + regresión logística."""
    y = np.array(y)
    pred = np.zeros(len(y), dtype=int)
    skf = StratifiedKFold(n_splits=k, shuffle=True, random_state=semilla)
    for tr, te in skf.split(textos, y):
        modelo = entrenar_tfidf([textos[i] for i in tr], y[tr])
        pred[te] = modelo.predict([textos[i] for i in te])
    return pred
