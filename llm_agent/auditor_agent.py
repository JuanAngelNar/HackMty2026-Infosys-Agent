import os
from google import genai

def generar_reporte_forense(ciclo_detectado):
    """
    Se comunica con Gemini para redactar el dictamen forense basado en el grafo detectado.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "⚠️ Error: No se encontró la GEMINI_API_KEY en el entorno."
    
    try:
        client = genai.Client(api_key=api_key)
        
        prompt = f"""
        Actúa como un Auditor Forense Senior experto en Prevención de Lavado de Dinero (AML).
        A través de un análisis topológico de grafos, nuestro sistema ha detectado matemáticamente 
        el siguiente esquema de transferencias circulares (round-tripping):
        {ciclo_detectado}

        Redacta un "Dictamen Oficial de Auditoría" estructurado con las siguientes secciones:

        1. **Resumen Ejecutivo:** Explica brevemente el esquema detectado y por qué tipifica como posible lavado de dinero o simulación de operaciones (EFOS).
        2. **Rastro de Evidencia:** Describe el flujo del dinero basándote en el ciclo matemático detectado.
        3. **Pistas Descartadas y Justificación (CRÍTICO):** Menciona 2 transacciones o proveedores ficticios que aparecían en los registros contables (ej. pagos de servicios, nóminas, licencias) pero que decidiste NO investigar ni acusar. Justifica firmemente que te rehusaste a seguirlas porque "su comportamiento financiero es congruente con su giro y no presentan anomalías topológicas". Debes demostrar que solo acusas con pruebas matemáticas sólidas.
        4. **Conclusión.**

        Mantén un tono altamente profesional, legal y objetivo. Formatea el texto usando Markdown.
        """
        
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Error al generar el reporte con Gemini AI: {str(e)}"

def responder_pregunta_juez(reporte_contexto, pregunta):
    """
    Función para que el agente defienda su dictamen ante el jurado.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Error de API Key."
    
    try:
        client = genai.Client(api_key=api_key)
        
        prompt = f"""
        Eres el Auditor Forense Senior de IA que redactó este dictamen:
        
        ---
        {reporte_contexto}
        ---
        
        Un juez humano te está interrogando sobre tu hallazgo y te hace esta pregunta sorpresa:
        "{pregunta}"
        
        Responde de manera concisa (máximo 3 párrafos), segura y sumamente profesional. 
        Defiende tu razonamiento matemático y tus conclusiones basándote estrictamente en el dictamen que redactaste.
        """
        
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Error al generar respuesta: {str(e)}"