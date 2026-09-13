import os
import json
from google import genai

def _llamar_gemini_json(prompt, max_retries=2):
    """Función helper para llamar a Gemini y asegurar que devuelva JSON válido."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"error": "No se encontró GEMINI_API_KEY"}
    
    client = genai.Client(api_key=api_key)
    
    for intento in range(max_retries):
        try:
            response = client.models.generate_content(
                model='gemini-3.6-flash',
                contents=prompt
            )
            
            # Limpiamos el texto por si Gemini le pone formato markdown de código (```json ... ```)
            texto_limpio = response.text.strip()
            if texto_limpio.startswith("```json"):
                texto_limpio = texto_limpio[7:-3].strip()
            elif texto_limpio.startswith("```"):
                texto_limpio = texto_limpio[3:-3].strip()
                
            return json.loads(texto_limpio)
        except Exception as e:
            if intento == max_retries - 1:
                return {"error": f"Fallo al procesar JSON con Gemini: {str(e)}"}

def determinar_siguiente_accion(estado_caso_str, acciones_disponibles_str):
    """
    Decide la Siguiente Mejor Acción Investigativa (NBIA) basada en la evidencia actual.
    """
    prompt = f"""
    Eres un Investigador Financiero Forense IA.
    Tu responsabilidad NO es probar un fraude, sino determinar la acción investigativa 
    que más reduzca la incertidumbre entre explicaciones opuestas.
    
    ESTADO DEL CASO (Evidencia confirmada):
    {estado_caso_str}
    
    ACCIONES DISPONIBLES:
    {acciones_disponibles_str}
    
    Elige exactamente UNA acción de la lista de disponibles.
    NO inventes evidencia, IDs, ni transacciones. Usa solo los datos proporcionados.
    
    Responde ÚNICAMENTE con un objeto JSON con esta estructura exacta:
    {{
      "selected_action_id": "ID de la accion elegida",
      "question": "¿Qué pregunta crítica responde esta acción?",
      "why_now": "¿Por qué es el mejor paso a seguir en este momento?",
      "supports_if": "¿Qué resultado apoyaría la hipótesis de fraude?",
      "weakens_if": "¿Qué resultado debilitaría la hipótesis o probaría legitimidad?"
    }}
    """
    return _llamar_gemini_json(prompt)

def revision_critica(estado_caso_str):
    """
    Actúa como un Auditor Adversario intentando probar que el sistema se equivoca.
    """
    prompt = f"""
    Eres un Revisor de Auditoría Forense Adversario.
    Tu objetivo es encontrar la debilidad en la hipótesis de fraude actual e identificar 
    una explicación comercial legítima para los datos observados.
    
    ESTADO DEL CASO (Evidencia confirmada):
    {estado_caso_str}
    
    NO inventes hechos. Usa solo la evidencia listada.
    
    Responde ÚNICAMENTE con un objeto JSON con esta estructura exacta:
    {{
      "weakest_inference": "La inferencia o suposición más débil en la hipótesis actual",
      "alternative_explanation": "La mejor explicación comercial legítima (ej. subcontratación válida)",
      "missing_evidence": ["Evidencia 1 que falta", "Evidencia 2 que falta"],
      "critical_objection": true o false (booleano)
    }}
    """
    return _llamar_gemini_json(prompt)

def generar_reporte_forense(estado_caso_str, exposicion_mxn):
    """
    Genera el dictamen final objetivo.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    
    prompt = f"""
    Actúa como un Sistema Experto Forense en AML.
    Redacta el "Resumen de Auditoría Automatizada" basado ÚNICAMENTE en este estado:
    {estado_caso_str}
    
    Exposición confirmada: ${exposicion_mxn} MXN.
    
    Secciones requeridas:
    1. **Resumen Ejecutivo:** Señal detectada objetivamente.
    2. **Rastro de Evidencia:** Lista los IDs de evidencia que sustentan el caso.
    3. **Explicaciones Alternativas Consideradas:** Qué se revisó para no dar un falso positivo.
    4. **Conclusión Técnica:** (SUPPORTED, DISMISSED, o HUMAN_REVIEW_REQUIRED).
    
    Mantén un tono objetivo y analítico. Formato Markdown. NO acuses de delitos legales.
    """
    response = client.models.generate_content(model='gemini-3.6-flash', contents=prompt)
    return response.text

def responder_pregunta_juez(estado_caso_str, pregunta):
    """
    Responde al juez basándose SÓLO en los hechos confirmados del caso.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    
    prompt = f"""
    Eres The Forensic Auditor, un agente IA desarrollado para el HackMTY 2026.
    Responde la pregunta del juez usando SOLO los hechos de este caso:
    {estado_caso_str}
    
    Pregunta del juez: "{pregunta}"
    
    Reglas:
    - Máximo 2 párrafos concisos.
    - Cita los números de Evidencia (ej. E-001) si existen.
    - Si no tienes la evidencia para responder, di: "La investigación actual no contiene evidencia suficiente para responder eso."
    - NO inventes datos.
    """
    response = client.models.generate_content(model='gemini-3.6-flash', contents=prompt)
    return response.text