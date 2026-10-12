
import streamlit as st
from groq import Groq

st.set_page_config(
    page_title="MilangAI",
    page_icon="🐱"
)

st.title("🐱 MilangAI")
st.caption("Tu pequeño centro de inteligencia artificial")

try:
    cliente = Groq(api_key=st.secrets["GROQ_API_KEY"])

    if "historial" not in st.session_state:
        st.session_state.historial = []

    for mensaje in st.session_state.historial:
        with st.chat_message(mensaje["role"]):
            st.markdown(mensaje["content"])

    pregunta = st.chat_input("Escribile a MilangAI...")

    if pregunta:
        st.session_state.historial.append({
            "role": "user",
            "content": pregunta
        })

        with st.chat_message("user"):
            st.markdown(pregunta)

        with st.chat_message("assistant"):
            with st.spinner("MilangAI está pensando..."):
                respuesta = cliente.chat.completions.create(
                    model="openai/gpt-oss-120b",
                    messages=[
                        {
                            "role": "system",
                            "content": (
    "Tu nombre es MilangAI. "
    "Si te preguntan cómo te llamás, respondé "
    "'Me llamo MilangAI'. "
    "Nunca digas que tu nombre es 'Sos MilangAI'. "
    "Sos un asistente de inteligencia artificial útil, "
    "amigable y creativo. "
    "Respondé en español argentino natural. "
    "Entendé las instrucciones por su significado, "
    "no las repitas como si fueran tu presentación."
)

                        },
                        *st.session_state.historial
                    ]
                )

                texto = respuesta.choices[0].message.content
                st.markdown(texto)

                st.session_state.historial.append({
                    "role": "assistant",
                    "content": texto
                })

except KeyError:
    st.error("Falta configurar la clave de la IA en los secretos.")
except Exception as error:
    st.error(f"No se pudo conectar con la IA: {error}")

