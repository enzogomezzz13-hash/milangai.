
import streamlit as st
from groq import Groq
from supabase import create_client

st.set_page_config(
    page_title="MilangAI",
    page_icon="🐱",
    layout="centered"
)

st.title("🐱 MilangAI")
st.caption("Tu pequeño centro de inteligencia artificial")

SYSTEM_PROMPT = """
Tu nombre es MilangAI.
Si te preguntan cómo te llamás, respondé:
'Me llamo MilangAI'.
Nunca digas que tu nombre es 'Sos MilangAI'.
Sos un asistente de inteligencia artificial útil,
amigable y creativo.
Respondé en español argentino natural.
Entendé las instrucciones por su significado,
no las repitas como si fueran tu presentación.
"""


def conectar_supabase():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )


def obtener_usuario(cliente):
    sesion = st.session_state.get("sesion")

    if not sesion:
        return None

    try:
        respuesta = cliente.auth.set_session(
            sesion["access_token"],
            sesion["refresh_token"]
        )

        nueva_sesion = respuesta.session

        if nueva_sesion:
            st.session_state.sesion = {
                "access_token": nueva_sesion.access_token,
                "refresh_token": nueva_sesion.refresh_token
            }

        return cliente.auth.get_user().user

    except Exception:
        st.session_state.pop("sesion", None)
        return None


def cerrar_sesion():
    st.session_state.pop("sesion", None)
    st.session_state.pop("chat_id", None)
    st.session_state.pop("historial", None)
    st.rerun()


def crear_chat(db, usuario_id):
    respuesta = db.table("chats").insert({
        "user_id": usuario_id,
        "titulo": "Nuevo chat"
    }).execute()

    chat = respuesta.data[0]
    st.session_state.chat_id = chat["id"]
    st.session_state.historial = []
    st.rerun()


def guardar_mensaje(db, usuario_id, chat_id, rol, contenido):
    db.table("mensajes").insert({
        "user_id": usuario_id,
        "chat_id": chat_id,
        "rol": rol,
        "contenido": contenido
    }).execute()


def cargar_mensajes(db, chat_id):
    respuesta = (
        db.table("mensajes")
        .select("rol, contenido")
        .eq("chat_id", chat_id)
        .order("creado_en")
        .execute()
    )

    return [
        {"role": m["rol"], "content": m["contenido"]}
        for m in respuesta.data
    ]


try:
    db = conectar_supabase()
    usuario = obtener_usuario(db)

except Exception as error:
    st.error(
        "No se pudo conectar con Supabase. "
        "Revisá los Secrets de Streamlit."
    )
    st.stop()


# Pantalla de acceso
if usuario is None:
    st.subheader("Iniciar sesión o crear cuenta")

    modo = st.radio(
        "Elegí una opción",
        ["Iniciar sesión", "Crear cuenta"],
        horizontal=True
    )

    with st.form("formulario_acceso"):
        email = st.text_input("Correo electrónico")
        password = st.text_input(
            "Contraseña",
            type="password"
        )

        enviar = st.form_submit_button(
            modo,
            use_container_width=True
        )

   
    if enviar:
        try:
            if not email.strip() or not password:
                st.error("Completá el correo y la contraseña.")

            elif modo == "Crear cuenta":
                resultado = db.auth.sign_up({
                    "email": email.strip(),
                    "password": password
                })

                if resultado.session:
                    st.session_state.sesion = {
                        "access_token": resultado.session.access_token,
                        "refresh_token": resultado.session.refresh_token
                    }
                    st.rerun()
                else:
                    st.success(
                        "Cuenta creada. Revisá tu correo "
                        "si Supabase solicita confirmación. "
                        "Después iniciá sesión."
                    )

            else:
                resultado = db.auth.sign_in_with_password({
                    "email": email.strip(),
                    "password": password
                })

                st.session_state.sesion = {
                    "access_token": resultado.session.access_token,
                    "refresh_token": resultado.session.refresh_token
                }
                st.rerun()

        except Exception as error:
            st.error(f"Error de autenticación: {error}")

    st.stop()



# Chat del usuario autenticado
st.caption(f"Sesión: {usuario.email}")

if st.button("Cerrar sesión"):
    cerrar_sesion()

usuario_id = usuario.id

try:
    respuesta = (
        db.table("chats")
        .select("id, titulo, creado_en")
        .eq("user_id", usuario_id)
        .order("creado_en", desc=True)
        .execute()
    )
    chats = respuesta.data


except Exception as error:
    st.error("No se pudieron cargar tus conversaciones.")
    st.code(str(error))
    st.stop()



st.sidebar.title("💬 Mis chats")

if st.sidebar.button("➕ Nuevo chat", use_container_width=True):
    crear_chat(db, usuario_id)

if chats:
    opciones = {c["titulo"]: c["id"] for c in chats}

    # Usamos los identificadores para evitar confusiones
    # cuando dos conversaciones tienen el mismo título.
    etiquetas = {
        c["id"]: (
            c["titulo"] if c["titulo"] else "Nuevo chat"
        )
        for c in chats
    }

    ids = [c["id"] for c in chats]

    if (
        st.session_state.get("chat_id") not in ids
    ):
        st.session_state.chat_id = ids[0]

    chat_id = st.sidebar.selectbox(
        "Tus conversaciones",
        options=ids,
        format_func=lambda x: etiquetas[x],
        key="selector_chat"
    )

    if chat_id != st.session_state.get("chat_id"):
        st.session_state.chat_id = chat_id
        st.session_state.pop("historial", None)
        st.rerun()

    if st.sidebar.button(
        "🗑️ Borrar chat actual",
        use_container_width=True
    ):
        st.session_state.confirmar_borrado = True

    if st.session_state.get("confirmar_borrado", False):
        st.sidebar.warning(
            "Esta acción elimina el chat y sus mensajes."
        )

        if st.sidebar.button("Sí, borrar definitivamente"):
            try:
                db.table("chats").delete().eq(
                    "id", chat_id
                ).eq(
                    "user_id", usuario_id
                ).execute()

                st.session_state.pop("historial", None)
                st.session_state.pop("chat_id", None)
                st.session_state.pop("confirmar_borrado", None)
                st.rerun()

            except Exception:
                st.sidebar.error("No se pudo borrar el chat.")

        if st.sidebar.button("Cancelar borrado"):
            st.session_state.confirmar_borrado = False
            st.rerun()

    if "historial" not in st.session_state:
        try:
            st.session_state.historial = cargar_mensajes(
                db, chat_id
            )
        except Exception:
            st.error("No se pudo cargar el historial.")
            st.stop()

else:
    st.info("Todavía no tenés chats guardados.")
    st.session_state.historial = []

    if st.button("Crear mi primer chat"):
        crear_chat(db, usuario_id)

    st.stop()


# Mostrar conversación
for mensaje in st.session_state.historial:
    with st.chat_message(mensaje["role"]):
        st.markdown(mensaje["content"])


pregunta = st.chat_input("Escribile a MilangAI...")

if pregunta:
    historial = st.session_state.historial

    try:
        # Crear un chat automáticamente si todavía no existe.
        if not st.session_state.get("chat_id"):
            resultado = db.table("chats").insert({
                "user_id": usuario_id,
                "titulo": pregunta[:60]
            }).execute()

            st.session_state.chat_id = resultado.data[0]["id"]

        chat_id = st.session_state.chat_id

        guardar_mensaje(
            db, usuario_id, chat_id, "user", pregunta
        )

        historial.append({
            "role": "user",
            "content": pregunta
        })

        with st.chat_message("user"):
            st.markdown(pregunta)

        with st.chat_message("assistant"):
            with st.spinner("MilangAI está pensando..."):
                cliente = Groq(
                    api_key=st.secrets["GROQ_API_KEY"]
                )

                
respuesta = cliente.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        *historial
    ],
    tools=[{"type": "browser_search"}],
    citation_options="enabled"
)


                texto = respuesta.choices[0].message.content
                st.markdown(texto)

        guardar_mensaje(
            db, usuario_id, chat_id, "assistant", texto
        )

        historial.append({
            "role": "assistant",
            "content": texto
        })

        # Actualizar el título con la primera pregunta.
        chat_actual = next(
            (c for c in chats if c["id"] == chat_id),
            None
        )

        if chat_actual and chat_actual["titulo"] == "Nuevo chat":
            db.table("chats").update({
                "titulo": pregunta[:60]
            }).eq(
                "id", chat_id
            ).eq(
                "user_id", usuario_id
            ).execute()

        st.rerun()

    except Exception:
        st.error(
            "Hubo un problema al guardar o generar "
            "la respuesta. Revisá la conexión e intentá "
            "nuevamente."
        )
