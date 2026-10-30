"""Pipeline completo: mensaje -> preprocesamiento -> señales -> recuperación -> Claude -> resultado."""
import time

import anthropic

from .baselines import clasificar_reglas
from .llm import VERSIONES, clasificar
from .preproceso import extraer_senales, normalizar, ocultar_datos_personales
from .recuperacion import buscar

VERSION_FINAL = "v6"
EFFORT_FINAL = "medium"   # L8: mejor F1 en las tres corridas de evaluación


def analizar(texto: str, remitente: str = "nose", version: str = VERSION_FINAL, effort: str = EFFORT_FINAL,
             razonamiento: str = "adaptativo") -> dict:
    """Analiza un mensaje y devuelve el veredicto, las señales, los patrones parecidos y métricas.

    Si la API falla, responde con el sistema de reglas y lo indica con modo_respaldo=True.
    """
    t0 = time.perf_counter()
    limpio = normalizar(texto)
    senales = extraer_senales(limpio, remitente)
    seguro = ocultar_datos_personales(limpio)
    patrones = buscar(limpio) if VERSIONES[version]["rag"] else []
    t_recuperacion = time.perf_counter() - t0

    try:
        resultado = clasificar(version, seguro, remitente, senales, patrones, effort, razonamiento)
        modo_respaldo = not resultado.get("ok", False)
    except (anthropic.AnthropicError, TypeError) as e:   # red, límite de uso, llave inválida o ausente
        resultado = {"ok": False, "error": f"No se pudo contactar al modelo ({type(e).__name__})"}
        modo_respaldo = True

    if modo_respaldo:
        reglas = clasificar_reglas(limpio, remitente)
        resultado.update({
            "veredicto": reglas["veredicto"], "certeza": "baja", "tipo": "otro",
            "senales": senales["alertas"][:5],
            "explicacion": "No pudimos consultar al modelo de lenguaje, así que este resultado viene de reglas "
                           "automáticas y es menos confiable. Ante la duda, verificá por otra vía antes de actuar.",
            "que_hacer": ["No compartás códigos ni datos bancarios", "Verificá llamando al número oficial"],
        })

    return {**resultado, "modo_respaldo": modo_respaldo, "alertas": senales["alertas"],
            "enlaces": senales["enlaces"], "patrones": patrones, "texto_analizado": seguro,
            "t_recuperacion_s": t_recuperacion, "t_total_s": time.perf_counter() - t0}
