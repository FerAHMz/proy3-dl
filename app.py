"""Ojo Chapín: detector de estafas en mensajes de WhatsApp y SMS para Guatemala.

Ejecutar con:
    streamlit run app.py
"""
import html

import pandas as pd
import streamlit as st

from ojo.baselines import clasificar_reglas
from ojo.config import MODELO, REMITENTES, RESULTADOS
from ojo.ejemplos import EJEMPLOS, cargar_cache, clave
from ojo.preproceso import extraer_senales, normalizar
from ojo.recuperacion import buscar, cargar_patrones

st.set_page_config(page_title="Ojo Chapín · ¿Es estafa?", page_icon=":material/shield:", layout="wide")

MAX_CARACTERES = 3000
NOMBRES_TIPO = {p["id"]: p["nombre"] for p in cargar_patrones()} | {"ninguno": "Ninguno", "otro": "Otro tipo"}
ESTILOS = {
    "estafa": {"etiqueta": "Alto riesgo", "titulo": "Es una estafa",
               "sub": "No respondás, no abrás enlaces y no deposités nada.", "color": "#A4161A", "fondo": "#FBF1F1"},
    "sospechoso": {"etiqueta": "Riesgo medio", "titulo": "Mensaje sospechoso",
                   "sub": "Verificá por otra vía antes de hacer cualquier cosa.", "color": "#9A5B00", "fondo": "#FBF6EC"},
    "seguro": {"etiqueta": "Sin riesgo aparente", "titulo": "Parece legítimo",
               "sub": "No encontramos señales de estafa en este mensaje.", "color": "#1E6B45", "fondo": "#F0F7F3"},
}

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=Source+Serif+4:opsz,wght@8..60,500;8..60,600&display=swap');
:root { --tinta: #1A1F2B; --suave: #5B6170; --linea: #DDDAD2; --marca: #1D3557; --papel: #FFFFFF; }
html, body, [class*="css"], .stMarkdown, .stButton button, textarea, input { font-family: 'IBM Plex Sans', -apple-system, 'Segoe UI', sans-serif; }
header[data-testid="stHeader"] { display: none; }
.block-container { padding-top: 1.6rem; max-width: 1160px; }
div[data-testid="stVerticalBlockBorderWrapper"] { background: var(--papel); border-radius: 6px; border-color: var(--linea); }
div.stButton > button { border-radius: 4px; font-weight: 500; letter-spacing: .01em; }
textarea { border-radius: 4px !important; }

.barra { display: flex; justify-content: space-between; align-items: baseline; border-bottom: 2px solid var(--tinta);
         padding-bottom: .55rem; margin-bottom: 1.6rem; }
.marca { font-family: 'Source Serif 4', Georgia, serif; font-size: 1.35rem; font-weight: 600; color: var(--tinta); letter-spacing: .01em; }
.marca span { color: var(--suave); font-family: 'IBM Plex Sans', sans-serif; font-size: .82rem; font-weight: 400; margin-left: .7rem; }
.institucion { font-size: .78rem; color: var(--suave); text-transform: uppercase; letter-spacing: .08em; }
.intro h1 { font-family: 'Source Serif 4', Georgia, serif; font-weight: 600; font-size: 2.5rem; color: var(--tinta);
            margin: 0; padding: 0; line-height: 1.15; }
.intro p { color: var(--suave); font-size: 1.05rem; max-width: 640px; margin: .5rem 0 .9rem 0; }
.datos { display: flex; gap: 0; margin-bottom: 1.6rem; font-size: .82rem; color: var(--suave); }
.datos div { padding: 0 1rem; border-left: 1px solid var(--linea); }
.datos div:first-child { padding-left: 0; border-left: none; }
.datos b { color: var(--tinta); font-weight: 600; }

.rotulo { font-size: .72rem; font-weight: 600; text-transform: uppercase; letter-spacing: .1em; color: var(--suave);
          margin: 1.1rem 0 .45rem 0; }
.rotulo.primero { margin-top: 0; }
.veredicto { border-left: 5px solid; padding: 1rem 1.2rem; margin-bottom: .4rem; border-radius: 2px; }
.veredicto .etiqueta { font-size: .72rem; font-weight: 600; text-transform: uppercase; letter-spacing: .1em; }
.veredicto .titulo { font-family: 'Source Serif 4', Georgia, serif; font-size: 2rem; font-weight: 600; line-height: 1.2; margin: .15rem 0; }
.veredicto .sub { color: var(--tinta); font-size: .98rem; }
.meta { display: flex; gap: 1.6rem; border-bottom: 1px solid var(--linea); padding: .7rem 0; font-size: .88rem; }
.meta .k { color: var(--suave); font-size: .72rem; text-transform: uppercase; letter-spacing: .08em; display: block; }
.meta .v { color: var(--tinta); font-weight: 600; }
.senal { border-left: 2px solid var(--marca); padding: .15rem 0 .15rem .7rem; margin-bottom: .4rem; font-size: .94rem; }
.paso { display: flex; gap: .8rem; padding: .45rem 0; border-bottom: 1px solid #ECEAE4; font-size: .95rem; }
.paso:last-child { border-bottom: none; }
.paso .n { font-family: 'Source Serif 4', Georgia, serif; font-weight: 600; color: var(--marca); min-width: 1.2rem; }
.vacio { padding: 2.2rem 1.6rem; color: var(--suave); }
.vacio h3 { font-family: 'Source Serif 4', Georgia, serif; color: var(--tinta); font-weight: 600; font-size: 1.35rem; margin: 0 0 .4rem 0; padding: 0; }
.vacio ol { margin: .8rem 0 0 1.1rem; padding: 0; font-size: .93rem; }
.vacio li { margin-bottom: .35rem; }

section[data-testid="stSidebar"] { border-right: 1px solid var(--linea); }
section[data-testid="stSidebar"] h4 { font-size: .72rem; font-weight: 600; text-transform: uppercase; letter-spacing: .1em;
                                       color: var(--suave); margin: 1.2rem 0 .4rem 0; padding: 0; }
.metricas { display: grid; grid-template-columns: 1fr 1fr; border-top: 1px solid var(--linea); border-left: 1px solid var(--linea); }
.metrica { padding: .55rem .65rem; border-right: 1px solid var(--linea); border-bottom: 1px solid var(--linea); background: var(--papel); }
.metrica .v { font-family: 'Source Serif 4', Georgia, serif; font-size: 1.3rem; font-weight: 600; color: var(--tinta); }
.metrica .e { font-size: .72rem; color: var(--suave); }
.pie { color: var(--suave); font-size: .8rem; margin-top: 2.4rem; padding-top: .8rem; border-top: 1px solid var(--linea); }
</style>
""", unsafe_allow_html=True)


@st.cache_resource(show_spinner="Preparando el modelo de búsqueda de patrones...")
def precargar():
    buscar("precarga")   # carga el modelo de embeddings e índice una sola vez
    return True


@st.cache_data
def metricas_finales():
    ruta = RESULTADOS / "iteraciones.csv"
    if not ruta.exists():
        return None
    tabla = pd.read_csv(ruta)
    return tabla[tabla["split"] == "test"].set_index("id")


def usar_ejemplo(e):
    st.session_state.texto = e["texto"]
    st.session_state.remitente = e["remitente"]
    st.session_state.pendiente = True


def leer_captura():
    archivo = st.session_state.get("captura")
    if archivo is None:
        st.session_state.aviso = "Primero subí una captura."
        return
    try:
        from ojo.llm import transcribir_imagen
        r = transcribir_imagen(archivo.getvalue(), archivo.type)
        st.session_state.texto = r["texto"]
        st.session_state.pendiente = bool(r["texto"].strip())
        if not r["texto"].strip():
            st.session_state.aviso = "No encontramos texto en la captura. Probá con otra imagen o pegá el mensaje."
    except Exception:
        st.session_state.aviso = "No pudimos leer la captura en este momento. Pegá el texto del mensaje."


def resultado_sin_conexion(texto: str, remitente: str) -> dict:
    """Usa el resultado guardado de un ejemplo o, si no hay, el sistema de reglas."""
    guardado = cargar_cache().get(clave(texto, remitente))
    if guardado:
        return {**guardado, "desde_cache": True}
    s = extraer_senales(texto, remitente)
    reglas = clasificar_reglas(texto, remitente)
    return {"veredicto": reglas["veredicto"], "certeza": "baja", "tipo": "otro", "senales": s["alertas"][:5],
            "explicacion": "Estamos sin conexión con el modelo, así que este resultado viene de reglas automáticas "
                           "y es menos confiable. Ante la duda, verificá por otra vía antes de actuar.",
            "que_hacer": ["No compartás códigos ni datos bancarios", "Verificá llamando al número oficial"],
            "modo_respaldo": True, "patrones": [], "alertas": s["alertas"]}


def analizar_mensaje(texto: str, remitente: str, sin_conexion: bool) -> dict:
    if sin_conexion:
        return resultado_sin_conexion(texto, remitente)
    from ojo.pipeline import analizar
    r = analizar(texto, remitente)
    if r.get("modo_respaldo"):
        guardado = cargar_cache().get(clave(texto, remitente))
        if guardado:
            return {**guardado, "desde_cache": True}
    return r


def mostrar_resultado(r: dict):
    estilo = ESTILOS.get(r.get("veredicto"), ESTILOS["sospechoso"])
    tipo = r.get("tipo", "otro")
    st.markdown(f"""
    <div class="veredicto" style="border-color:{estilo['color']};background:{estilo['fondo']}">
      <div class="etiqueta" style="color:{estilo['color']}">{estilo['etiqueta']}</div>
      <div class="titulo" style="color:{estilo['color']}">{estilo['titulo']}</div>
      <div class="sub">{estilo['sub']}</div>
    </div>""", unsafe_allow_html=True)
    meta = f'<div><span class="k">Certeza</span><span class="v">{html.escape(r.get("certeza", "baja").capitalize())}</span></div>'
    if r.get("veredicto") != "seguro" and tipo != "ninguno":
        meta += f'<div><span class="k">Tipo de estafa</span><span class="v">{html.escape(NOMBRES_TIPO.get(tipo, "Otro tipo"))}</span></div>'
    st.markdown(f'<div class="meta">{meta}</div>', unsafe_allow_html=True)

    if r.get("modo_respaldo") and not r.get("desde_cache"):
        st.warning("No pudimos consultar al modelo de lenguaje. Este resultado viene de reglas automáticas y es menos confiable.")
    if r.get("desde_cache"):
        st.caption("Resultado guardado previamente (modo sin conexión).")

    st.markdown('<div class="rotulo">Explicación</div>', unsafe_allow_html=True)
    st.write(r.get("explicacion", ""))

    if r.get("senales"):
        st.markdown('<div class="rotulo">Señales encontradas</div>', unsafe_allow_html=True)
        st.markdown("".join(f'<div class="senal">{html.escape(x)}</div>' for x in r["senales"]), unsafe_allow_html=True)

    if r.get("que_hacer"):
        st.markdown('<div class="rotulo">Qué hacer</div>', unsafe_allow_html=True)
        st.markdown("".join(f'<div class="paso"><div class="n">{i}.</div><div>{html.escape(p)}</div></div>'
                            for i, p in enumerate(r["que_hacer"], 1)), unsafe_allow_html=True)

    with st.expander("Detalle técnico del análisis"):
        if r.get("patrones"):
            st.markdown("**Patrones de estafa conocidos más parecidos** (búsqueda por embeddings y similitud coseno)")
            for p in r["patrones"]:
                st.progress(max(0.0, min(1.0, p["similitud"])), text=f"{p['nombre']} · similitud {p['similitud']:.2f}")
        if r.get("alertas"):
            st.markdown("**Señales detectadas automáticamente en el preprocesamiento**")
            for a in r["alertas"]:
                st.markdown(f"- {a}")
        if "tokens_entrada" in r:
            st.markdown("**Detalles técnicos**")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Modelo", "Haiku 5.5")
            c2.metric("Tiempo", f"{r.get('t_total_s', r.get('latencia_s', 0)):.1f} s")
            c3.metric("Tokens", f"{r['tokens_entrada']} + {r['tokens_salida']}")
            c4.metric("Costo", f"${r['costo_usd']:.4f}")


precargar()
for clave_estado, inicial in [("texto", ""), ("remitente", "desconocido"), ("resultado", None),
                              ("pendiente", False), ("aviso", None)]:
    st.session_state.setdefault(clave_estado, inicial)

with st.sidebar:
    st.markdown("#### Sobre Ojo Chapín")
    st.write("Te ayuda a reconocer estafas en mensajes de WhatsApp y SMS antes de responder, con ejemplos y "
             "señales pensadas para Guatemala.")
    st.markdown("#### Cómo funciona")
    st.markdown("1. Limpiamos el mensaje y ocultamos datos personales\n"
                "2. Detectamos señales (enlaces falsos, pedidos de códigos, urgencia)\n"
                "3. Buscamos estafas conocidas parecidas con embeddings\n"
                "4. Claude Haiku 5.5 decide y explica en lenguaje sencillo")
    m = metricas_finales()
    if m is not None and "L8" in m.index:
        st.markdown("#### Resultados de la evaluación")
        st.caption("Evaluado en 60 mensajes etiquetados (30 estafas y 30 legítimos).")
        L, B = m.loc["L8"], m.loc["B2"]
        celdas = [(f"{L['f1']:.2f}", f"F1 (sin LLM: {B['f1']:.2f})"),
                  (f"{100 * L['tasa_falsas_alarmas']:.0f}%", "Falsas alarmas"),
                  (f"{L['latencia_s_prom']:.1f} s", "Tiempo por mensaje"),
                  (f"${L['costo_usd_prom']:.4f}", "Costo por mensaje")]
        st.markdown('<div class="metricas">' + "".join(
            f'<div class="metrica"><div class="v">{v}</div><div class="e">{e}</div></div>' for v, e in celdas)
            + "</div>", unsafe_allow_html=True)
    st.markdown("#### Privacidad")
    st.caption("No guardamos tus mensajes. Antes de enviarlos al modelo ocultamos números de tarjeta, DPI y correos.")
    sin_conexion = st.toggle("Modo sin conexión", help="Usa resultados guardados o reglas, sin llamar al modelo.")

st.markdown("""
<div class="barra">
  <div class="marca">Ojo Chapín<span>Verificador de mensajes sospechosos</span></div>
  <div class="institucion">UVG · CC3092 Deep Learning</div>
</div>
<div class="intro">
  <h1>¿Es estafa?</h1>
  <p>Pegá el mensaje que te llegó por WhatsApp o SMS. Te decimos si es una estafa, en qué señales nos basamos y qué hacer.</p>
</div>
<div class="datos">
  <div><b>Guatemala</b> · 20 modalidades documentadas</div>
  <div><b>~3 segundos</b> por mensaje</div>
  <div><b>Claude Haiku 5.5</b> con búsqueda de patrones</div>
</div>""", unsafe_allow_html=True)

izq, der = st.columns([1.05, 1], gap="large")

with izq:
    with st.container(border=True):
        st.markdown('<div class="rotulo primero">Mensaje recibido</div>', unsafe_allow_html=True)
        st.text_area("Mensaje", key="texto", height=170, label_visibility="collapsed",
                     placeholder="Pegá aquí el mensaje que te llegó por WhatsApp o SMS...")
        st.pills("¿Quién te lo mandó?", options=list(REMITENTES.keys()), format_func=lambda k: REMITENTES[k],
                 key="remitente", selection_mode="single")
        analizar_ya = st.button("Analizar mensaje", type="primary", use_container_width=True)
        with st.expander("Subir una captura de pantalla"):
            st.file_uploader("Captura", type=["png", "jpg", "jpeg", "webp"], key="captura", label_visibility="collapsed")
            st.button("Leer y analizar captura", on_click=leer_captura, use_container_width=True)

    st.markdown('<div class="rotulo">Mensajes de ejemplo</div>', unsafe_allow_html=True)
    columnas = st.columns(2)
    for i, e in enumerate(EJEMPLOS):
        columnas[i % 2].button(e["titulo"], on_click=usar_ejemplo, args=(e,), use_container_width=True, key=f"ej{i}")

with der:
    if st.session_state.aviso:
        st.warning(st.session_state.aviso)
        st.session_state.aviso = None
    if analizar_ya or st.session_state.pendiente:
        st.session_state.pendiente = False
        texto = normalizar(st.session_state.texto)
        remitente = st.session_state.remitente or "nose"
        if not texto:
            st.warning("Escribí o pegá un mensaje para analizarlo.")
        elif len(texto) > MAX_CARACTERES:
            st.warning(f"El mensaje es muy largo ({len(texto)} caracteres). Pegá solo el mensaje sospechoso, "
                       f"de hasta {MAX_CARACTERES} caracteres.")
        else:
            with st.spinner("Analizando el mensaje..."):
                st.session_state.resultado = analizar_mensaje(texto, remitente, sin_conexion)
    if st.session_state.resultado:
        with st.container(border=True):
            mostrar_resultado(st.session_state.resultado)
    else:
        with st.container(border=True):
            st.markdown('<div class="vacio"><h3>Resultado del análisis</h3>'
                        '<p>Todavía no has analizado ningún mensaje. Al hacerlo vas a ver aquí</p>'
                        '<ol><li>El veredicto y qué tan seguros estamos</li>'
                        '<li>Las señales concretas que encontramos en el mensaje</li>'
                        '<li>Los pasos recomendados para protegerte</li></ol></div>', unsafe_allow_html=True)

st.markdown('<div class="pie">Ojo Chapín puede equivocarse: usalo como apoyo, no como la última palabra. '
            'Si fuiste víctima de una estafa, denunciala en la PNC (110) o en el Ministerio Público. '
            f'Proyecto 3, CC3092 Deep Learning, Universidad del Valle de Guatemala · Modelo {MODELO}</div>', unsafe_allow_html=True)
