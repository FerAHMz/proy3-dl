"""Mensajes de ejemplo para la demo (distintos a los del conjunto de evaluación) y su caché.

Uso para regenerar la caché del modo sin conexión:
    python -m ojo.ejemplos
"""
import json

from .config import CACHE_EJEMPLOS_PATH

EJEMPLOS = [
    {"titulo": "Banco bloqueado", "remitente": "desconocido",
     "texto": "BANRURAL: Estimado cliente, su tarjeta de débito fue BLOQUEADA por seguridad. Para reactivarla ingrese "
              "sus datos en banrural-reactivacion.com antes de las 6:00 pm de hoy."},
    {"titulo": "Familiar en apuros", "remitente": "desconocido",
     "texto": "Hola abue, soy Luis, este es mi número nuevo porque me robaron el cel. Necesito que me ayudés con Q900 "
              "para pagar una multa, depositá a la cuenta de mi amigo y no le digás a mi papá porfa"},
    {"titulo": "Premio de telefónica", "remitente": "desconocido",
     "texto": "TIGO te felicita! Tu línea ganó Q10,000 en el sorteo de aniversario. Para recibirlo enviá Q250 de "
              "activación al 5512-7788 por Tigo Money."},
    {"titulo": "Paquete retenido", "remitente": "desconocido",
     "texto": "Guatex: su encomienda #GT88123 está detenida por falta de pago de Q32.00. Pague en bit.ly/guatex-pago "
              "para evitar la devolución."},
    {"titulo": "Código del banco", "remitente": "empresa",
     "texto": "BI: Tu codigo de verificacion es 556120. Nunca lo compartas, Bi jamas te lo pedira por llamada o mensaje."},
    {"titulo": "Mamá pide un favor", "remitente": "contacto",
     "texto": "Mijo, cuando salgás del trabajo pasá a la farmacia por mis pastillas de la presión, aquí te doy el pisto en la noche"},
]


def cargar_cache() -> dict:
    if CACHE_EJEMPLOS_PATH.exists():
        return json.loads(CACHE_EJEMPLOS_PATH.read_text(encoding="utf-8"))
    return {}


def clave(texto: str, remitente: str) -> str:
    return f"{remitente}::{texto.strip()}"


def generar_cache():
    from .pipeline import analizar
    cache = {}
    for e in EJEMPLOS:
        r = analizar(e["texto"], e["remitente"])
        if not r["modo_respaldo"]:
            cache[clave(e["texto"], e["remitente"])] = r
            print(f"{e['titulo']}: {r['veredicto']} ({r['certeza']})")
    CACHE_EJEMPLOS_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    generar_cache()
