from llm_agent.auditor_agent import generar_reporte_forense, responder_pregunta_juez
import streamlit as st
import pandas as pd
import hashlib
import os
import sys
from dotenv import load_dotenv
import networkx as nx
import openai
import anthropic

def anonimizar_cuenta(cuenta):
    """
    Convierte un número de cuenta real en un hash seguro y anónimo de 8 caracteres.
    """
    cuenta_str = str(cuenta)
    # Aplicamos criptografía SHA-256
    hash_obj = hashlib.sha256(cuenta_str.encode())
    # Tomamos solo los primeros 8 caracteres para que sea visualmente limpio
    return f"ID-{hash_obj.hexdigest()[:8].upper()}"

def detectar_esquema_circular(dataframe, col_origen='Origen', col_destino='Destino'):
    """
    Lee un DataFrame, construye un grafo dirigido y busca ciclos cerrados.
    """
    # 1. Construir el grafo dinámicamente desde el CSV
    G = nx.from_pandas_edgelist(dataframe, source=col_origen, target=col_destino, create_using=nx.DiGraph())
    
    # 2. El algoritmo matemático busca todos los ciclos posibles
    ciclos = list(nx.simple_cycles(G))
    
    # 3. Filtramos para buscar esquemas de al menos 3 cuentas (A -> B -> C -> A)
    ciclos_complejos = [c for c in ciclos if len(c) >= 3]
    
    if ciclos_complejos:
        # Tomamos el esquema más grande o el primero que encuentre
        fraude = ciclos_complejos[0]
        
        # Lo formateamos bonito para el reporte y el agente
        ruta_str = " -> ".join([str(cuenta) for cuenta in fraude])
        ruta_str += f" -> {fraude[0]}" # Cerramos el ciclo
        
        return ruta_str, fraude
    return None, None

def investigador_claude(ciclo_detectado):
    """Llama a Claude 3 Haiku para armar la acusación inicial."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key: 
        return "⚠️ Error: No se encontró ANTHROPIC_API_KEY en el entorno."
    
    try:
        client = anthropic.Anthropic(api_key=api_key)
        prompt = f"Actúa como un Investigador Forense implacable. Analiza este esquema matemático de transferencias detectado: {ciclo_detectado}. Redacta una acusación formal y contundente explicando por qué es un claro esquema de lavado de dinero (máximo 2 párrafos)."
        
        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    except Exception as e:
        return f"Error en Claude: {str(e)}"

def abogado_defensor_chatgpt(acusacion):
    """Llama a gpt-4o-mini para refutar a Claude."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key: 
        return "⚠️ Error: No se encontró OPENAI_API_KEY en el entorno."
    
    try:
        client = openai.OpenAI(api_key=api_key)
        prompt = f"El Investigador acusa este esquema: {acusacion}. Actúa como abogado defensor corporativo. Refuta su argumento y busca 2 justificaciones legales y lógicas de por qué este flujo de dinero es completamente normal (ej. pago de filiales). Sé conciso (máximo 2 párrafos)."
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error en ChatGPT: {str(e)}"

def juez_supremo_gemini(acusacion, defensa):
    """Llama a Gemini Flash para dar el veredicto final."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Error de API Key."
    
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        
        prompt = f"""
        Investigador (Claude): {acusacion}
        
        Defensor (ChatGPT): {defensa}
        
        Actúa como el Juez Supremo de Auditoría. Evalúa objetivamente ambos argumentos y da un veredicto final, imparcial y definitivo. ¿Es fraude o un falso positivo justificable? (Máximo 2 párrafos).
        """
        
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Error al generar respuesta del Juez: {str(e)}"

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
st.markdown("""
    <style>
        /* Fondo principal oscuro de ciberseguridad */
        .stApp {
            background-color: #0B101E;
        }
        
        /* Cajas de métricas y expansores */
        div[data-testid="stExpander"] div[role="button"] p {
            font-weight: 600;
            color: #E2E8F0;
        }
        
        /* Botón de acción principal (Ejecutar Auditoría) */
        button[kind="primary"] {
            background-color: #D32F2F !important;
            color: white !important;
            font-weight: bold !important;
            border-radius: 6px !important;
            border: none !important;
            padding: 0.5rem 1rem !important;
            transition: all 0.3s ease;
        }
        button[kind="primary"]:hover {
            background-color: #B71C1C !important;
            box-shadow: 0 4px 12px rgba(211, 47, 47, 0.4);
        }
        
        /* Encabezados y títulos */
        h1, h2, h3 {
            color: #64B5F6 !important;
            font-family: 'Courier New', Courier, monospace !important;
        }
        
        /* Notificaciones de éxito (Verde Neón) */
        div[data-testid="stAlert"] {
            background-color: rgba(46, 125, 50, 0.2);
            border-left: 4px solid #4CAF50;
            color: #E8F5E9;
        }
    </style>
""", unsafe_allow_html=True)

st.title("🕵️‍♂️ The Forensic Auditor - AML Dashboard")
with st.sidebar:
    st.markdown("### ⚙️ Motor de Procesamiento")
    st.caption("Selecciona el backend de almacenamiento.")
    
    motor = st.radio(
        "Origen de datos:",
        ["Archivo CSV (Local)", "Clúster Empresarial (Tiger Data)"],
        index=0
    )
    
    if motor == "Clúster Empresarial (Tiger Data)":
        from db.tigerdata_connector import conectar_tigerdata
        if st.button("Probar Conexión a BD"):
            conectar_tigerdata()
            
    st.markdown("---")
    st.markdown("### 🔒 Cumplimiento")
    st.checkbox("Enmascaramiento PII Activo", value=True, disabled=True)
    
    st.caption("Simulador de base de datos SAT (Demo):")
    id_sospechoso = st.text_input("Agregar ID a Lista 69-B:", placeholder="Ej. ID-A1B2C3D4")
st.markdown("Plataforma de detección de lavado de dinero y empresas fantasma (EFOS) impulsada por Gemini AI.")

st.sidebar.header("Panel de Control")
uploaded_file = st.sidebar.file_uploader("Sube el historial de transacciones (tx.csv)", type=["csv"])

if uploaded_file is not None:
    st.success("Archivo de transacciones cargado exitosamente.")
    df = pd.read_csv(uploaded_file)

    # FASE 2: DETECCIÓN INTELIGENTE DE COLUMNAS
    col_origen = None
    col_destino = None

    # Buscamos palabras clave en los encabezados y "bloqueamos" cuando encontramos la primera
    for col in df.columns:
        col_lower = col.lower()
        
        # Si NO hemos encontrado el origen, buscamos. (Quitamos 'source' para evitar falsos positivos)
        if col_origen is None and any(keyword in col_lower for keyword in ['origen', 'account_id', 'remitente', 'from', 'sender']):
            col_origen = col
            
        # Si NO hemos encontrado el destino, buscamos.
        elif col_destino is None and any(keyword in col_lower for keyword in ['destino', 'target', 'counter', 'beneficiario', 'to', 'receiver']):
            col_destino = col
            
    # Fallback: Si el CSV tiene nombres muy raros, asumimos que la columna 2 y 3 son las cuentas
    if not col_origen or not col_destino:
        col_origen = df.columns[1]
        col_destino = df.columns[2]

    # FASE 1: ESCUDO DE PRIVACIDAD DINÁMICO
    # Ahora encriptamos las columnas correctas
    df[col_origen] = df[col_origen].apply(anonimizar_cuenta)
    df[col_destino] = df[col_destino].apply(anonimizar_cuenta)
        
    with st.expander("Ver vista previa de los datos brutos (Anonimizados)"):
        st.dataframe(df.head())

    st.markdown("### 🏛️ Verificación Gubernamental y Métricas")
        
        # Extraemos cuentas únicas
    nodos_totales = set(df[col_origen]).union(set(df[col_destino]))
        
        # Simulamos la lista negra y agregamos el ID del juez
    lista_negra_sat = {"ID-F5CA38F7", "ID-9400F1B2"} 
    if id_sospechoso:
        lista_negra_sat.add(id_sospechoso.strip())
            
    coincidencias_sat = nodos_totales.intersection(lista_negra_sat)
        
        # Mostramos tarjetas de estilo financiero (st.columns)
    col1, col2, col3 = st.columns(3)
    col1.metric(label="Transacciones Procesadas", value=f"{len(df)} txs")
    col2.metric(label="Entidades Únicas", value=f"{len(nodos_totales)}")
    col3.metric(label="Riesgo SAT (69-B)", value="ALTO" if coincidencias_sat else "BAJO", delta="- Fraude Detectado" if coincidencias_sat else "Limpio", delta_color="inverse")
        
    if coincidencias_sat:
        st.error(f"🚨 **¡ALERTA CRÍTICA SAT 69-B!** Entidades boletinadas detectadas (EFOS): {', '.join(coincidencias_sat)}")
    else:
        st.success("✅ Verificación completada: Ninguna entidad en este lote está boletinada por el SAT.")
            
    st.markdown("---")
        
    if st.button("Ejecutar Auditoría Forense", type="primary"):
        with st.spinner("Analizando la topología de la red financiera con NetworkX..."):
            ciclo_detectado, lista_nodos = detectar_esquema_circular(df, col_origen=col_origen, col_destino=col_destino)
            
        if ciclo_detectado:
            st.error(f"🚨 ¡ALERTA DE FRAUDE! Esquema de round-tripping detectado matemáticamente:\n`{ciclo_detectado}`")
            
            # --- VISUALIZACIÓN DEL GRAFO ---
            import streamlit.components.v1 as components
            from reports.graph_visualizer import generar_html_grafo
            
            st.markdown("### 🕸️ Topología de la Red Transaccional")
            grafo_path = generar_html_grafo(lista_nodos)
            
            # Leemos el HTML generado y lo inyectamos en Streamlit
            with open(grafo_path, 'r', encoding='utf-8') as f:
                html_source = f.read()
            components.html(html_source, height=415)
            
            # GENERACIÓN DE REPORTE CON IA
            with st.spinner("Generando Expediente de Caso con Anthropic..."):
                reporte = generar_reporte_forense(ciclo_detectado)
                st.session_state['reporte_generado'] = reporte
                st.session_state['ciclo_detectado'] = ciclo_detectado
            
            if reporte:
                st.markdown("### 📄 Dictamen Oficial de Auditoría")
                st.info(reporte)
                
                # SÍNTESIS DE VOZ
                with st.spinner("Sintetizando reporte en voz alta con ElevenLabs..."):
                    try:
                        import os
                        eleven_api_key = os.getenv("ELEVENLABS_API_KEY") 
                        
                        if not eleven_api_key:
                            st.error("Falta la API Key de ElevenLabs en el entorno.")
                        else:
                            from elevenlabs.client import ElevenLabs
                            client_eleven = ElevenLabs(api_key=eleven_api_key)
                            audio = client_eleven.text_to_speech.convert(
                                voice_id="JBFqnCBsd6RMkjVDRZzb",
                                text="Attention. A money laundering scheme involving circular transfers has been detected. Please review the attached file.",
                                model_id="eleven_multilingual_v2"
                            )
                            audio_bytes = b"".join(audio)
                            st.audio(audio_bytes, format="audio/mp3", autoplay = True)
                            st.success("🎙️ Reporte de voz generado con éxito.")
                    except Exception as voice_error:
                        st.warning(f"No se pudo generar el audio: {voice_error}")

                # GENERACIÓN DE PDF Y DESCARGA
                from reports.pdf_generator import generar_pdf_caso
                pdf_path = generar_pdf_caso(reporte)
                
                with open(pdf_path, "rb") as pdf_file:
                    pdf_bytes = pdf_file.read()
                
                st.download_button(
                    label="📥 Descargar Expediente en PDF",
                    data=pdf_bytes,
                    file_name="expediente_forense.pdf",
                    mime="application/pdf"
                )
        else:
            st.success("✅ Auditoría completada: No se detectaron esquemas de lavado de dinero circular en esta base de datos.")


# MÓDULO DE INTERROGATORIO (PREGUNTA SORPRESA)
if 'reporte_generado' in st.session_state:
    st.markdown("---")
    st.markdown("### ⚖️ Tribunal de IAs (Debate Multi-Agente)")
    st.caption("Orquestación Multi-LLM en vivo: Claude vs ChatGPT vs Gemini")
    
    if st.button("Convocar Tribunal de Auditoría", icon="🏛️"):
        # Usamos el ciclo que guardamos en memoria en el Paso 1
        ciclo_memoria = st.session_state['ciclo_detectado'] 
        
        with st.spinner("Investigador Claude (3-Haiku) armando el caso..."):
            acusacion_claude = investigador_claude(ciclo_memoria)
            
        with st.spinner("Abogado ChatGPT (gpt-4o-mini) preparando la defensa..."):
            defensa_gpt = abogado_defensor_chatgpt(acusacion_claude)
            
        with st.spinner("Juez Gemini evaluando el veredicto final..."):
            veredicto_gemini = juez_supremo_gemini(acusacion_claude, defensa_gpt)
            
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"🔵 **Investigador (Claude 3):**\n\n{acusacion_claude}")
        with col2:
            st.warning(f"🔴 **Defensor Corporativo (ChatGPT):**\n\n{defensa_gpt}")
            
        st.success(f"🟢 **Juez Supremo (Gemini Flash):**\n\n{veredicto_gemini}")
    st.markdown("---")
    st.markdown("### ⚖️ Interrogatorio del Juez")
    st.caption("Hazle una pregunta sorpresa al agente sobre su razonamiento o las pistas descartadas.")
    
    # Inicializar el historial del chat
    if "messages" not in st.session_state:
        st.session_state.messages = []
        
    # Mostrar el historial
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
    # Input de la pregunta
    if pregunta_juez := st.chat_input("Ej: ¿Por qué estás tan seguro de no investigar los otros pagos?"):
        # Mostrar la pregunta del usuario
        st.session_state.messages.append({"role": "user", "content": pregunta_juez})
        with st.chat_message("user"):
            st.markdown(pregunta_juez)
            
        # Generar y mostrar la respuesta de la IA
        with st.chat_message("assistant"):
            with st.spinner("El agente está analizando su dictamen para responder..."):
                respuesta = responder_pregunta_juez(st.session_state['reporte_generado'], pregunta_juez)
                st.markdown(respuesta)
        # Guardar respuesta en el historial
        st.session_state.messages.append({"role": "assistant", "content": respuesta})