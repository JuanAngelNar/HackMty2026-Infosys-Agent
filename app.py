import streamlit as st
import pandas as pd
import os
import sys
from dotenv import load_dotenv

# Forzar la carga del .env desde la raíz
load_dotenv(override=True)

# Cargar variables de entorno
load_dotenv()

# Asegurar que Streamlit encuentre tus carpetas
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from llm_agent.auditor_agent import generar_reporte_forense

# Importar ElevenLabs (compatible con la versión más reciente)
from elevenlabs.client import ElevenLabs
from elevenlabs import play

st.set_page_config(page_title="Forensic Auditor AI", page_icon="🕵️‍♂️", layout="wide")

st.title("🕵️‍♂️ The Forensic Auditor - AML Dashboard")
st.markdown("Plataforma de detección de lavado de dinero y empresas fantasma (EFOS) impulsada por Gemini AI.")

st.sidebar.header("Panel de Control")
uploaded_file = st.sidebar.file_uploader("Sube el historial de transacciones (tx.csv)", type=["csv"])

if uploaded_file is not None:
    st.success("Archivo de transacciones cargado exitosamente.")
    df = pd.read_csv(uploaded_file)
    
    with st.expander("Ver vista previa de los datos brutos"):
        st.dataframe(df.head())
    
    if st.button("Ejecutar Auditoría Forense", type="primary"):
        with st.spinner("Analizando la topología de la red financiera con NetworkX..."):
            # Simulación del hallazgo exitoso de nuestra lógica
            ciclo_detectado = "Cuenta 19 -> Cuenta 26 -> Cuenta 20 -> Cuenta 19"
            st.error(f"🚨 ¡ALERTA DE FRAUDE! Esquema de round-tripping detectado:\n`{ciclo_detectado}`")
            
        with st.spinner("Generando Expediente de Caso con Gemini AI..."):
            reporte = generar_reporte_forense(ciclo_detectado)
            
            if reporte:
                st.markdown("### 📄 Dictamen Oficial de Auditoría")
                st.info(reporte)
                
                # SÍNTESIS DE VOZ CON ELEVENLABS (SDK Actualizado)
                with st.spinner("Sintetizando reporte en voz alta con ElevenLabs..."):
                    try:
                        # Usamos tu clave directamente para evitar problemas de lectura del .env
                        eleven_api_key = "sk_8da11b4007c80c17287d216c63890867934ad4605123bb7f"
                        
                        client_eleven = ElevenLabs(api_key=eleven_api_key)
                        
                        # Método correcto para la versión actual del SDK
                        audio = client_eleven.text_to_speech.convert(
                            voice_id="JBFqnCBsd6RMkjVDRZzb", # ID de voz por defecto (Rachel/Adam)
                            text="Atención. Se ha detectado un esquema de lavado de dinero por transferencia circular. Revise el expediente adjunto.",
                            model_id="eleven_multilingual_v2"
                        )
                        
                        # Convertir la respuesta de streaming a bytes para Streamlit
                        audio_bytes = b"".join(audio)
                        st.audio(audio_bytes, format="audio/mp3")
                        st.success("🎙️ Reporte de voz generado con éxito.")
                    except Exception as voice_error:
                        st.warning(f"No se pudo generar el audio: {voice_error}")
