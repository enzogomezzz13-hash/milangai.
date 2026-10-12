
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
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "Sos MilangAI, un asistente útil. "
                                "Respondé en español natural y claro."
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

