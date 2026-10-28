"""Recuperación de patrones de estafa similares al mensaje (la parte de RAG).

Cada patrón de data/patrones.json se convierte en un documento y se representa con un
embedding de un modelo multilingüe de sentence-transformers. Los vectores se normalizan,
así que la similitud coseno es simplemente el producto punto.
"""
import json
import threading
from functools import lru_cache

import numpy as np

from .config import PATRONES_PATH, INDICE_PATH, MODELO_EMBEDDINGS, TOP_K

# El modelo de embeddings no es seguro para cargarse o usarse desde varios hilos a la vez.
_CANDADO = threading.RLock()


def cargar_patrones() -> list[dict]:
    return json.loads(PATRONES_PATH.read_text(encoding="utf-8"))


def documento_patron(p: dict) -> str:
    """Texto que se indexa por cada patrón: nombre, descripción, señales y un ejemplo."""
    return f"{p['nombre']}. {p['descripcion']} Señales: {'; '.join(p['senales'])}. Ejemplo: {p['ejemplo']}"


def _prefijos(nombre_modelo: str) -> tuple[str, str]:
    # Los modelos E5 esperan prefijos distintos para consultas y documentos.
    return ("query: ", "passage: ") if "e5" in nombre_modelo.lower() else ("", "")


@lru_cache(maxsize=2)
def cargar_modelo(nombre_modelo: str = MODELO_EMBEDDINGS):
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(nombre_modelo)


def construir_indice(nombre_modelo: str = MODELO_EMBEDDINGS, guardar: bool = True):
    """Calcula los embeddings de todos los patrones y los guarda en disco."""
    patrones = cargar_patrones()
    _, pref_doc = _prefijos(nombre_modelo)
    modelo = cargar_modelo(nombre_modelo)
    docs = [pref_doc + documento_patron(p) for p in patrones]
    vectores = modelo.encode(docs, normalize_embeddings=True, convert_to_numpy=True).astype(np.float32)
    ids = np.array([p["id"] for p in patrones])
    if guardar:
        np.savez(INDICE_PATH, vectores=vectores, ids=ids, modelo=nombre_modelo)
    return vectores, ids


@lru_cache(maxsize=2)
def cargar_indice(nombre_modelo: str = MODELO_EMBEDDINGS):
    if INDICE_PATH.exists():
        datos = np.load(INDICE_PATH, allow_pickle=False)
        ids_actuales = [p["id"] for p in cargar_patrones()]
        if str(datos["modelo"]) == nombre_modelo and list(map(str, datos["ids"])) == ids_actuales:
            return datos["vectores"], datos["ids"]
    return construir_indice(nombre_modelo, guardar=(nombre_modelo == MODELO_EMBEDDINGS))


def buscar(texto: str, k: int = TOP_K, nombre_modelo: str = MODELO_EMBEDDINGS) -> list[dict]:
    """Devuelve los k patrones más parecidos al mensaje con su similitud coseno."""
    pref_query, _ = _prefijos(nombre_modelo)
    with _CANDADO:
        vectores, ids = cargar_indice(nombre_modelo)
        q = cargar_modelo(nombre_modelo).encode([pref_query + texto], normalize_embeddings=True,
                                                convert_to_numpy=True)[0]
    sims = vectores @ q
    orden = np.argsort(-sims)[:k]
    por_id = {p["id"]: p for p in cargar_patrones()}
    return [{**por_id[str(ids[i])], "similitud": float(sims[i])} for i in orden]
