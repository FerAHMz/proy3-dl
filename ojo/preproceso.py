"""Preprocesamiento del mensaje: normalización, ocultamiento de datos personales y
extracción de señales objetivas (enlaces, dominios, montos, pedidos de códigos, urgencia)."""
import re
import unicodedata

# Dominios oficiales de marcas e instituciones que suelen ser suplantadas en Guatemala.
DOMINIOS_OFICIALES = {
    "banrural.com.gt", "bi.com.gt", "bam.com.gt", "gytcontinental.com.gt", "bancoindustrial.com.gt",
    "tigo.com.gt", "claro.com.gt", "sat.gob.gt", "portal.sat.gob.gt", "igssgt.org", "renap.gob.gt",
    "pnc.gob.gt", "mides.gob.gt", "eegsa.com", "energuate.com", "cargoexpreso.com", "guatex.com",
    "muniguate.com", "netflix.com", "amazon.com", "uvg.edu.gt",
    # dominios cortos que usan los propios bancos y operadoras en sus SMS
    "bi.gt", "bac.gt", "tgo.gt", "bancoindustrial.com", "nexabanco.com",
}
MARCAS = ["banrural", "bi-", "bienlinea", "bam", "gyt", "continental", "tigo", "claro", "sat", "renap",
          "igss", "pnc", "mides", "eegsa", "energuate", "cargoexpreso", "guatex", "netflix", "amazon",
          "aduana", "bono", "gob"]
ACORTADORES = {"bit.ly", "tinyurl.com", "cutt.ly", "is.gd", "t.co", "ow.ly", "rebrand.ly", "shorturl.at", "t.ly",
               "lnk.ink", "urlr.me"}
# Plataformas de SMS masivos que usan las marcas registradas en Guatemala para su publicidad.
PLATAFORMAS_MARCAS = {"tgor.me"}
TLD_SOSPECHOSOS = {"xyz", "top", "click", "online", "site", "info", "live", "shop", "icu", "buzz", "club", "sbs",
                   "cam", "help"}
# Marcas e instituciones que las estafas por SMS imitan desde números celulares comunes.
NOMBRES_EMPRESAS = (r"banrural|banco industrial|\bbi\b|\bbam\b|\bbac\b|promerica|\bvisa\b|tigo|claro|emetra|\bpmt\b|"
                    r"\bpnc\b|guatex|correos|cargo expreso|avianca|\bsat\b|igss|amazon|netflix")

RE_URL = re.compile(r"(?:https?://)?(?:[a-z0-9-]+\.)+[a-z]{2,}(?:/[^\s,]*)?", re.IGNORECASE)
RE_MONTO = re.compile(r"(?:Q|\$|US\$)\s?\d[\d,]*(?:\.\d+)?|\d[\d,]*\s?quetzales", re.IGNORECASE)
RE_TELEFONO_GT = re.compile(r"(?<![\d-])(?:\+?502[\s-]?)?\d{4}[\s-]?\d{4}(?![\d-])")
RE_INTERNACIONAL = re.compile(r"\+(?!502)\d{8,15}|wa\.me/(?!502)\d{8,15}")
RE_CUENTA = re.compile(r"\b\d{1,2}-\d{3}-\d{4,6}-\d\b|\b\d{10,12}\b")
RE_TARJETA = re.compile(r"\b(?:\d[ -]?){15}\d\b")
RE_DPI = re.compile(r"\b\d{4}\s\d{5}\s\d{4}\b")
RE_CORREO = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b")

PALABRAS = {
    "urgencia": r"urgent|inmediat|hoy mismo|\bhoy\b|último aviso|ultimo aviso|próximas? \d+|antes de que|en las próximas|vence|evite|suspendid|bloquead|desactivad|cancelaci|media hora|24 horas",
    "pide_codigo": r"c[oó]digo|\bpin\b|token|contraseña|\bclave\b|cvv|16 d[ií]gitos|usuario",
    "pide_pago": r"deposit|pag(a|ar|ue|ás)\b|transfer|cubrir|comisi[oó]n|seguro de|impuesto|arancel|liberar|anticipo|garant[ií]a",
    "premio": r"ganaste|ganador|ganado|premio|sorteo|felicidades|enhorabuena|seleccionad",
    "amenaza": r"no la vuelve|no lo vuelve|consecuencias|sabemos d[oó]nde|mara\b|tenemos a",
    "secreto": r"no le digas|no le diga|no me llames|no cuelgue|no avis|no le avise|no se lo digas",
    "ganancia_facil": r"garantizad|rendimiento|duplic|multiplic|veces tu inversi|ganancias|diarios?\b.*Q|Q\d+ al d[ií]a|por cada rese",
    "numero_nuevo": r"n[uú]mero nuevo|otro n[uú]mero|cambi[eé] de n[uú]mero|celular de una amiga|tel[eé]fono de una amiga|se me cay[oó] el cel",
}


def normalizar(texto: str) -> str:
    """Normaliza Unicode y espacios sin cambiar el contenido del mensaje."""
    texto = unicodedata.normalize("NFKC", texto or "")
    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


def ocultar_datos_personales(texto: str) -> str:
    """Oculta números de tarjeta, DPI y correos antes de enviar el mensaje al LLM."""
    texto = RE_TARJETA.sub("[NÚMERO DE TARJETA]", texto)
    texto = RE_DPI.sub("[DPI]", texto)
    texto = RE_CORREO.sub("[CORREO]", texto)
    return texto


def _dominio_base(dominio: str) -> str:
    partes = dominio.lower().split(".")
    if len(partes) >= 3 and partes[-2] in {"com", "gob", "org", "edu", "net"} and partes[-1] == "gt":
        return ".".join(partes[-3:])
    return ".".join(partes[-2:])


def analizar_enlaces(texto: str) -> list[dict]:
    enlaces = []
    for m in RE_URL.finditer(texto):
        url = m.group(0).rstrip(".")
        dominio = re.sub(r"^https?://", "", url, flags=re.IGNORECASE).split("/")[0].lower()
        if dominio.replace(".", "").isdigit() or "." not in dominio:
            continue
        base = _dominio_base(dominio)
        oficial = dominio in DOMINIOS_OFICIALES or base in DOMINIOS_OFICIALES or dominio.endswith(".gob.gt")
        tld = dominio.rsplit(".", 1)[-1]
        imita = (not oficial) and any(marca in dominio for marca in MARCAS)
        enlaces.append({
            "url": url, "dominio": dominio, "oficial": oficial,
            "acortador": dominio in ACORTADORES,
            "plataforma_marcas": dominio in PLATAFORMAS_MARCAS,
            "tld_sospechoso": tld in TLD_SOSPECHOSOS,
            "imita_marca": imita,
            "archivo_apk": url.lower().endswith(".apk"),
            "whatsapp_externo": dominio == "wa.me",
        })
    return enlaces


def extraer_senales(texto: str, remitente: str = "nose") -> dict:
    """Extrae señales objetivas del mensaje que luego se le pasan al LLM y se muestran al usuario."""
    t = normalizar(texto)
    enlaces = analizar_enlaces(t)
    categorias = {nombre: bool(re.search(patron, t, re.IGNORECASE)) for nombre, patron in PALABRAS.items()}
    senales = {
        "enlaces": enlaces,
        "montos": RE_MONTO.findall(t),
        "telefonos": RE_TELEFONO_GT.findall(t),
        "numero_internacional": bool(RE_INTERNACIONAL.search(t)) or remitente == "internacional",
        "cuenta_bancaria": bool(RE_CUENTA.search(t)),
        "remitente": remitente,
        "desconocido_como_empresa": remitente == "desconocido" and bool(re.search(NOMBRES_EMPRESAS, t, re.IGNORECASE)),
        **categorias,
    }
    senales["alertas"] = resumir_alertas(senales)
    return senales


def resumir_alertas(s: dict) -> list[str]:
    """Convierte las señales en frases cortas para el prompt y la interfaz."""
    alertas = []
    for e in s["enlaces"]:
        if e["imita_marca"]:
            alertas.append(f"El enlace {e['dominio']} parece imitar a una marca o institución pero no es su dominio oficial")
        if e["acortador"]:
            alertas.append(f"Usa un enlace acortado ({e['dominio']}) que esconde el destino real")
        if e["plataforma_marcas"]:
            alertas.append(f"El enlace {e['dominio']} es de la plataforma de SMS masivos que usan muchas marcas en "
                           "Guatemala para su publicidad, por sí solo no indica estafa")
        if e["tld_sospechoso"] and not e["imita_marca"]:
            alertas.append(f"El dominio {e['dominio']} usa una terminación poco común (.{e['dominio'].rsplit('.', 1)[-1]})")
        if e["archivo_apk"]:
            alertas.append("Pide descargar una aplicación (.apk) fuera de la tienda oficial")
        if e["whatsapp_externo"]:
            alertas.append("Lleva a un chat de WhatsApp con un número extranjero")
        if e["oficial"]:
            alertas.append(f"El enlace {e['dominio']} corresponde a un dominio oficial")
    nombres = {
        "pide_codigo": "Menciona códigos, contraseñas, tokens o datos de tarjeta",
        "pide_pago": "Pide un pago, depósito o transferencia",
        "urgencia": "Usa lenguaje de urgencia o amenaza de bloqueo",
        "premio": "Habla de un premio o sorteo",
        "amenaza": "Contiene amenazas",
        "secreto": "Pide no avisar o no llamar a nadie",
        "ganancia_facil": "Promete ganancias fáciles o garantizadas",
        "numero_nuevo": "Dice escribir desde un número nuevo o prestado",
    }
    alertas += [texto for clave, texto in nombres.items() if s.get(clave)]
    if s["cuenta_bancaria"]:
        alertas.append("Incluye un número de cuenta bancaria")
    if s["desconocido_como_empresa"]:
        alertas.append("Un número desconocido escribe a nombre de una empresa o institución, que normalmente "
                       "envían sus SMS con su nombre como remitente")
    if s["numero_internacional"]:
        alertas.append("Viene de un número internacional o pide escribir a uno")
    return alertas
