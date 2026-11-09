# ============================================================
# AGENTE NIHILUS - INTERFAZ WEB CON STREAMLIT
# ============================================================
 
import os
import json
import uuid
import base64
import streamlit as st
from pathlib import Path
 
from dotenv import load_dotenv
from groq import Groq
from datetime import datetime
from zoneinfo import ZoneInfo
from basic_memory import BasicMemory
from intermediate_tools import IntermediateTools
 
# [SUPABASE] Importación opcional: si el paquete no está, la app sigue funcionando.
try:
    from supabase import create_client
    SUPABASE_DISPONIBLE = True
except ImportError:
    create_client = None
    SUPABASE_DISPONIBLE = False
 
# ============================================================
# CONFIGURACION
# ============================================================
 
load_dotenv()
# Logo del agente (debe estar en la misma carpeta que este archivo).
LOGO_PATH = Path(__file__).parent / "Nihilus.png"
 
st.set_page_config(
    page_title="Agente Nihilus",
    page_icon=str(LOGO_PATH) if LOGO_PATH.exists() else "📊",
    layout="centered",
    initial_sidebar_state="expanded"
)
 
# ============================================================
# [SUPABASE] CONEXION Y GUARDADO DE CONVERSACIONES
# ============================================================
 
TABLA_CONVERSACIONES = "conversaciones_nihilus"
 
 
def obtener_secreto(nombre, default=""):
    """Lee primero Streamlit Secrets y, si no existe, la variable de entorno (.env)."""
    try:
        valor = st.secrets.get(nombre, None)
        if valor:
            return str(valor).strip()
    except Exception:
        pass
    return (os.getenv(nombre) or default).strip()
 
 
api_key = obtener_secreto("GROQ_API_KEY")
# [GROQ 2] Segunda clave de respaldo (opcional).
api_key2 = obtener_secreto("GROQ_API_KEY2")
 
 
@st.cache_resource
def _crear_cliente_supabase(url, key):
    # Si lanza excepción, Streamlit NO cachea el fallo y reintenta.
    return create_client(url, key)
 
 
def init_supabase():
    """Devuelve (cliente, error). Nunca imprime la clave."""
    if not SUPABASE_DISPONIBLE:
        return None, "Falta instalar el paquete 'supabase' (agrégalo a requirements.txt)."
 
    # Limpia comillas, espacios y rutas sobrantes (/rest/v1) de la URL.
    url = obtener_secreto("SUPABASE_URL").strip().strip('"').strip("'").rstrip("/")
    for sufijo in ("/rest/v1", "/rest"):
        if url.endswith(sufijo):
            url = url[: -len(sufijo)].rstrip("/")
 
    key = obtener_secreto("SUPABASE_KEY").strip().strip('"').strip("'")
 
    if not url or not key:
        return None, "Faltan SUPABASE_URL o SUPABASE_KEY."
 
    try:
        return _crear_cliente_supabase(url, key), None
    except Exception as error:
        return None, f"No se pudo crear el cliente: {error}"
 
 
supabase, error_supabase = init_supabase()
 
 
def guardar_en_supabase(pregunta, respuesta):
    if supabase is None:
        return False, error_supabase or "Supabase no conectado"
 
    try:
        supabase.table(TABLA_CONVERSACIONES).insert({
            "session_id": st.session_state.get("session_id"),
            "pregunta": str(pregunta),
            "respuesta": str(respuesta),
        }).execute()
        return True, None
    except Exception as error:
        print(f"ERROR SUPABASE (conversaciones): {error}")
        return False, str(error)
 
# ============================================================
# ESTILOS VISUALES 
# ============================================================
 
CUSTOM_CSS = """
<style>
    /* ---------- Paleta ---------- */
    :root {
        --bg: #0b1220;
        --panel: #111a2e;
        --panel-2: #16223b;
        --border: #24324f;
        --text: #e6edf7;
        --muted: #8fa0bd;
        --accent: #2dd4bf;
        --accent-2: #38bdf8;
        --gold: #fbbf24;
    }
 
    /* ---------- Fondo general ---------- */
    .stApp {
        background:
            radial-gradient(1200px 500px at 50% -10%, #12305a33, transparent),
            var(--bg);
        color: var(--text);
    }
 
    /* Ocultar menú/pie de Streamlit para una vista más limpia */
    #MainMenu, footer { visibility: hidden; }
    header[data-testid="stHeader"] { background: transparent; }
 
    /* ---------- Contenedor central ---------- */
    .block-container {
        max-width: 860px;
        padding-top: 2rem;
        padding-bottom: 6rem;
    }
 
    /* ---------- Encabezado ---------- */
    .nihilus-hero {
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 20px 24px;
        margin-bottom: 18px;
        background: linear-gradient(135deg, var(--panel) 0%, var(--panel-2) 100%);
        border: 1px solid var(--border);
        border-radius: 18px;
        box-shadow: 0 8px 28px rgba(0, 0, 0, 0.35);
    }
    .nihilus-logo {
        font-size: 2rem;
        width: 64px; height: 64px;
        display: flex; align-items: center; justify-content: center;
        border-radius: 14px;
        overflow: hidden;
        flex-shrink: 0;
        background: linear-gradient(135deg, var(--accent), var(--accent-2));
        box-shadow: 0 4px 14px rgba(45, 212, 191, 0.35);
    }
    .nihilus-logo img {
        width: 100%; height: 100%;
        object-fit: cover;
        display: block;
    }
    .nihilus-title {
        font-size: 1.8rem; font-weight: 700; line-height: 1.1;
        color: var(--text); margin: 0;
    }
    .nihilus-sub {
        color: var(--muted); font-size: 0.95rem; margin-top: 4px;
    }
 
    /* ---------- Tarjetas de bienvenida ---------- */
    .welcome-card {
        background: var(--panel);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 16px 18px;
        height: 100%;
    }
    .welcome-card h4 {
        margin: 0 0 6px 0; font-size: 1rem; color: var(--accent);
    }
    .welcome-card p {
        margin: 0; font-size: 0.88rem; color: var(--muted);
    }
    .section-label {
        color: var(--muted); font-size: 0.8rem;
        letter-spacing: 0.08em; text-transform: uppercase;
        margin: 22px 0 8px 2px;
    }
 
    /* ---------- Mensajes del chat ---------- */
    [data-testid="stChatMessage"] {
        background: var(--panel);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 14px 18px;
        margin-bottom: 12px;
    }
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
        background: var(--panel-2);
        border-color: #2f4166;
    }
    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] li {
        font-size: 1rem; line-height: 1.6;
    }
 
    /* Tablas dentro de las respuestas */
    [data-testid="stChatMessage"] table {
        width: 100%; border-collapse: collapse; margin: 8px 0;
        font-size: 0.92rem;
    }
    [data-testid="stChatMessage"] th {
        background: #1b2a47; color: var(--accent);
        text-align: left; padding: 8px 10px;
        border-bottom: 1px solid var(--border);
    }
    [data-testid="stChatMessage"] td {
        padding: 7px 10px; border-bottom: 1px solid #1d2a45;
    }
 
    /* ---------- Barra lateral ---------- */
    [data-testid="stSidebar"] {
        background: var(--panel);
        border-right: 1px solid var(--border);
    }
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 { color: var(--text); }
 
    .side-item {
        display: flex; gap: 10px; align-items: center;
        padding: 8px 10px; margin-bottom: 6px;
        background: var(--panel-2);
        border: 1px solid var(--border);
        border-radius: 10px;
        font-size: 0.9rem; color: var(--text);
    }
 
    /* ---------- Botones ---------- */
    .stButton > button {
        width: 100%;
        background: var(--panel-2);
        color: var(--text);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 0.55rem 0.8rem;
        font-weight: 500;
        transition: all 0.15s ease;
    }
    .stButton > button:hover {
        border-color: var(--accent);
        color: var(--accent);
        background: #12304033;
        transform: translateY(-1px);
    }
 
    /* ---------- Campo de entrada ---------- */
    [data-testid="stChatInput"] {
        border-radius: 14px;
    }
    [data-testid="stChatInput"] textarea {
        font-size: 1rem;
    }
 
    /* ---------- Spinner y alertas ---------- */
    [data-testid="stSpinner"] { color: var(--accent); }
    [data-testid="stAlert"] { border-radius: 12px; }
</style>
"""
 
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
 
# Encabezado
def logo_html():
    """Devuelve la imagen Nihilus.png incrustada; si no existe, un emoji."""
    if LOGO_PATH.exists():
        datos = base64.b64encode(LOGO_PATH.read_bytes()).decode()
        return f'<img src="data:image/png;base64,{datos}" alt="Nihilus">'
    return "📊"
 
 
st.markdown(
    f"""
    <div class="nihilus-hero">
        <div class="nihilus-logo">{logo_html()}</div>
        <div>
            <div class="nihilus-title">Agente Nihilus</div>
            <div class="nihilus-sub">
                Asistente de economía y econometría
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)
 
if not api_key:
    st.error(
        "No se encontró GROQ_API_KEY. "
        "Configúrala en Secrets (Streamlit Cloud) o en el archivo .env."
    )
    st.stop()
 
client = Groq(api_key=api_key)
# [GROQ 2] Segundo cliente (solo si existe GROQ_API_KEY2).
client2 = Groq(api_key=api_key2) if api_key2 else None
 
now = datetime.now(ZoneInfo("America/Guatemala"))
 
MEMORY_MAX_MESSAGES = 6
 
SYSTEM_PROMPT = """
Eres un asistente que habla en español. Eres un experto en economía
y econometría. Responde de manera muy breve y concisa e interpreta
los resultados obtenidos para un mejor análisis económico.
 
Herramientas disponibles:
 
1. consultar_tipo_cambio_api:
   Consulta el tipo de cambio actual de una moneda respecto al quetzal.
   Requiere el código de la moneda, por ejemplo USD.
 
2. consultar_desempleo_pais_api:
   Consulta el historial de la tasa de desempleo de un país.
   Requiere el código ISO del país, por ejemplo GT, US o MX.
 
3. consultar_info_pais_api:
   Consulta información general de un país.
   Requiere el nombre del país.
 
4. consultar_pib_pais_api:
   Consulta el historial del PIB de un país.
   Requiere el código ISO del país.
 
5. consultar_inflacion_pais_api:
   Consulta el historial de inflación de un país.
   Requiere el código ISO del país.
 
6. consultar_precio_cripto_api:
   Consulta el precio de una criptomoneda respecto a una moneda
   de referencia. Requiere el nombre de la criptomoneda.
 
Devuelve las respuestas de las herramientas tal cual.
Cuando ejecutes una herramienta, no generes texto explicativo
ni anuncies su nombre antes de realizar la llamada.
"""
 
# ============================================================
# DEFINICION DE HERRAMIENTAS PARA GROQ
# ============================================================
 
def crear_herramienta(nombre, descripcion, propiedades, requeridos):
    return {
        "type": "function",
        "function": {
            "name": nombre,
            "description": descripcion,
            "parameters": {
                "type": "object",
                "properties": propiedades,
                "required": requeridos
            }
        }
    }
 
 
TOOLS = [
    crear_herramienta(
        "consultar_tipo_cambio_api",
        "Consulta el tipo de cambio de una moneda respecto al quetzal.",
        {
            "moneda": {
                "type": "string",
                "description": "Código de moneda, por ejemplo USD"
            }
        },
        ["moneda"]
    ),
 
    crear_herramienta(
        "consultar_desempleo_pais_api",
        "Consulta el historial de desempleo de un país.",
        {
            "codigo_pais": {
                "type": "string",
                "description": "Código ISO, por ejemplo GT, US o MX"
            }
        },
        ["codigo_pais"]
    ),
 
    crear_herramienta(
        "consultar_info_pais_api",
        "Consulta información general de un país.",
        {
            "pais": {
                "type": "string",
                "description": "Nombre del país"
            }
        },
        ["pais"]
    ),
 
    crear_herramienta(
        "consultar_pib_pais_api",
        "Consulta el historial del PIB de un país.",
        {
            "codigo_pais": {
                "type": "string",
                "description": "Código ISO del país"
            }
        },
        ["codigo_pais"]
    ),
 
    crear_herramienta(
        "consultar_inflacion_pais_api",
        "Consulta el historial de inflación de un país.",
        {
            "codigo_pais": {
                "type": "string",
                "description": "Código ISO del país"
            }
        },
        ["codigo_pais"]
    ),
 
    crear_herramienta(
        "consultar_precio_cripto_api",
        "Consulta el precio de una criptomoneda.",
        {
            "criptomoneda": {
                "type": "string",
                "description": "Nombre de la criptomoneda"
            },
            "moneda_referencia": {
                "type": "string",
                "description": "Moneda de referencia, por ejemplo usd"
            }
        },
        ["criptomoneda"]
    )
]
 
# ============================================================
# EJECUCION DE LAS HERRAMIENTAS
# ============================================================
 
def ejecutar_herramienta(nombre, args):
    tools = IntermediateTools()
 
    if nombre == "consultar_tipo_cambio_api":
        return tools.consultar_tipo_cambio_api(
            moneda=args["moneda"]
        )
 
    elif nombre == "consultar_desempleo_pais_api":
        return tools.consultar_desempleo_pais_api(
            codigo_pais=args["codigo_pais"]
        )
 
    elif nombre == "consultar_info_pais_api":
        return tools.consultar_info_pais_api(
            pais=args["pais"]
        )
 
    elif nombre == "consultar_pib_pais_api":
        return tools.consultar_pib_pais_api(
            codigo_pais=args["codigo_pais"]
        )
 
    elif nombre == "consultar_inflacion_pais_api":
        return tools.consultar_inflacion_pais_api(
            codigo_pais=args["codigo_pais"]
        )
 
    elif nombre == "consultar_precio_cripto_api":
        return tools.consultar_precio_cripto_api(
            criptomoneda=args["criptomoneda"],
            moneda_referencia=args.get(
                "moneda_referencia", "usd"
            )
        )
 
    return {"error": f"Herramienta desconocida: {nombre}"}
 
 
# ============================================================
# [GROQ 2] LLAMADA AL MODELO CON RESPALDO DE SEGUNDA API KEY
# ============================================================
 
def crear_completion(client_principal, messages):
    """Intenta con la primera clave y, si falla, con GROQ_API_KEY2."""
    clientes = [client_principal]
    if client2 is not None:
        clientes.append(client2)
 
    ultimo_error = None
    for c in clientes:
        try:
            return c.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=messages,
                tools=TOOLS
            )
        except Exception as error:
            ultimo_error = error
 
    raise ultimo_error
 
 
# ============================================================
# PROCESAMIENTO DE RESPUESTAS DEL AGENTE
# ============================================================
 
def process_response(client, memory_messages, user_text):
 
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]
 
    messages.extend(memory_messages)
    messages.append({
        "role": "user",
        "content": user_text
    })
 
    while True:
 
        resp = crear_completion(client, messages)
 
        msg = resp.choices[0].message
 
        # Si no hay llamadas a herramientas, devolver respuesta.
        if not getattr(msg, "tool_calls", None):
            return msg.content or ""
 
        # Agregar al historial la solicitud de herramientas.
        messages.append({
            "role": "assistant",
            "content": None,
            "tool_calls": [
                tc.model_dump() for tc in msg.tool_calls
            ]
        })
 
        for tool_call in msg.tool_calls:
 
            nombre = tool_call.function.name
 
            args = json.loads(
                tool_call.function.arguments or "{}"
            )
 
            try:
                resultado = ejecutar_herramienta(
                    nombre, args
                )
 
            except Exception as error:
                resultado = {
                    "error": str(error)
                }
 
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(
                    resultado,
                    ensure_ascii=False,
                    default=str
                )
            })
 
 
# ============================================================
# INTERFAZ WEB STREAMLIT
# ============================================================
 
# [SUPABASE] Identificador de la conversación actual.
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
 
# Memoria e historial independientes por sesión.
if "agent_memory" not in st.session_state:
    st.session_state.agent_memory = BasicMemory(
        max_messages=MEMORY_MAX_MESSAGES
    )
 
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
 
# Consulta elegida desde los ejemplos de la pantalla de bienvenida.
if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None
 
# Barra lateral.
with st.sidebar:
    st.markdown("### ⚙️ Panel")
    st.write("Agente de economía y econometría.")
 
    st.markdown("**Indicadores disponibles**")
    st.markdown(
        """
        <div class="side-item">💱 Tipo de cambio</div>
        <div class="side-item">📈 PIB</div>
        <div class="side-item">🛒 Inflación</div>
        <div class="side-item">👷 Desempleo</div>
        <div class="side-item">🌍 Información de países</div>
        <div class="side-item">🪙 Criptomonedas</div>
        """,
        unsafe_allow_html=True
    )
 
    st.markdown("---")
 
    if st.button("🗑️ Limpiar conversación"):
        st.session_state.chat_history = []
        st.session_state.pending_prompt = None
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.agent_memory = BasicMemory(
            max_messages=MEMORY_MAX_MESSAGES
        )
        st.rerun()
 
    # [SUPABASE] Estado real de la conexión (hace una consulta de prueba).
    if supabase:
        try:
            supabase.table(TABLA_CONVERSACIONES).select("id").limit(1).execute()
            st.success("✅ Supabase conectado")
        except Exception as error:
            st.error(f"❌ Supabase: clave o tabla inválida ({error})")
    else:
        st.error(f"❌ Supabase no conectado: {error_supabase}")
 
    st.caption(
        f"Hora local: {now.strftime('%d/%m/%Y %H:%M')}"
    )
 
# Pantalla de bienvenida (solo cuando no hay conversación).
if not st.session_state.chat_history:
 
    st.markdown(
        '<div class="section-label">¿Qué puedo consultar por ti?</div>',
        unsafe_allow_html=True
    )
 
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            '<div class="welcome-card"><h4>💱 Mercados</h4>'
            '<p>Tipo de cambio frente al quetzal y precios '
            'de criptomonedas.</p></div>',
            unsafe_allow_html=True
        )
    with c2:
        st.markdown(
            '<div class="welcome-card"><h4>📈 Macroeconomía</h4>'
            '<p>PIB, inflación y desempleo con su '
            'interpretación económica.</p></div>',
            unsafe_allow_html=True
        )
    with c3:
        st.markdown(
            '<div class="welcome-card"><h4>🌍 Países</h4>'
            '<p>Información general para comparar '
            'economías.</p></div>',
            unsafe_allow_html=True
        )
 
    st.markdown(
        '<div class="section-label">Prueba con un ejemplo</div>',
        unsafe_allow_html=True
    )
 
    ejemplos = [
        "¿Cuál es el tipo de cambio del USD hoy?",
        "Muéstrame el historial de inflación de Guatemala",
        "¿Cómo ha evolucionado el PIB de México?",
        "¿Cuál es el precio de bitcoin en USD?",
    ]
 
    e1, e2 = st.columns(2)
    for i, texto in enumerate(ejemplos):
        with (e1 if i % 2 == 0 else e2):
            if st.button(texto, key=f"ejemplo_{i}"):
                st.session_state.pending_prompt = texto
                st.rerun()
 
# Mostrar el historial de conversación.
for mensaje in st.session_state.chat_history:
    avatar = "🧑‍💼" if mensaje["role"] == "user" else "📊"
    with st.chat_message(mensaje["role"], avatar=avatar):
        st.markdown(mensaje["content"])
 
# Campo de entrada del usuario.
user_text = st.chat_input(
    "Escribe tu consulta económica..."
)
 
# Si se eligió un ejemplo, usarlo como consulta.
if st.session_state.pending_prompt:
    user_text = st.session_state.pending_prompt
    st.session_state.pending_prompt = None
 
if user_text:
 
    # Mostrar y guardar el mensaje del usuario.
    st.session_state.chat_history.append({
        "role": "user",
        "content": user_text
    })
 
    with st.chat_message("user", avatar="🧑‍💼"):
        st.markdown(user_text)
 
    # [SUPABASE] Indica si la respuesta se generó sin errores.
    respuesta_ok = False
 
    # Procesar la consulta.
    with st.chat_message("assistant", avatar="📊"):
 
        with st.spinner("Nihilus está analizando..."):
 
            try:
                assistant_text = process_response(
                    client,
                    st.session_state.agent_memory.messages(),
                    user_text
                )
 
                if not assistant_text:
                    assistant_text = (
                        "No se recibió una respuesta del agente."
                    )
                else:
                    respuesta_ok = True
 
                st.markdown(assistant_text)
 
            except Exception as error:
                assistant_text = (
                    "No fue posible procesar la consulta. "
                    "Verifica la conexión, la clave de Groq "
                    "y las herramientas instaladas.\n\n"
                    f"Detalle: {error}"
                )
 
                st.error(assistant_text)
 
    # Guardar respuesta en el historial de la interfaz.
    st.session_state.chat_history.append({
        "role": "assistant",
        "content": assistant_text
    })
 
    # Actualizar la memoria del agente.
    st.session_state.agent_memory.add(
        "user", user_text
    )
 
    st.session_state.agent_memory.add(
        "assistant", assistant_text
    )
 
    # [SUPABASE] Guardar la conversación en la nube (solo respuestas correctas).
    if respuesta_ok:
        guardado, error_guardado = guardar_en_supabase(
            user_text, assistant_text
        )
        if guardado:
            st.toast("Conversación guardada en Supabase", icon="✅")
        else:
            st.warning(
                "La respuesta se generó, pero no se pudo guardar "
                f"en Supabase: {error_guardado}"
            )
 