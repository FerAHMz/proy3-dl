"""Configuración general de Ojo Chapín."""
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DATA = RAIZ / "data"
PROMPTS = RAIZ / "prompts"
RESULTADOS = RAIZ / "resultados"

PATRONES_PATH = DATA / "patrones.json"
EVALUACION_PATH = DATA / "evaluacion.jsonl"
REALES_PATH = DATA / "reales.jsonl"
PROPIOS_PATH = DATA / "propios.jsonl"
EXTERNO_PATH = DATA / "externos_hernandez.jsonl"
INDICE_PATH = DATA / "indice_patrones.npz"
CACHE_EJEMPLOS_PATH = DATA / "cache_ejemplos.json"

# LLM: Claude Haiku 5.5, el modelo más económico de Anthropic.
MODELO = "claude-haiku-5-5"
PRECIO_ENTRADA = 0.10 / 1_000_000   # USD por token de entrada (prompts de hasta 100K tokens)
PRECIO_SALIDA = 0.50 / 1_000_000    # USD por token de salida (incluye tokens de razonamiento)

# Embeddings locales para la recuperación de patrones (RAG).
MODELO_EMBEDDINGS = "intfloat/multilingual-e5-small"
TOP_K = 3

REMITENTES = {
    "desconocido": "Número desconocido",
    "contacto": "Contacto guardado",
    "internacional": "Número internacional",
    "empresa": "Empresa o código corto",
    "nose": "No sé",
}
