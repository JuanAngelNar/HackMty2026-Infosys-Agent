import os
import json
import openai

def _llamar_openai_json(prompt):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key: 
        return None
    
    # 🔥 FRENO DE EMERGENCIA: Si en 5 segundos no responde, cortamos la llamada.
    client = openai.OpenAI(api_key=api_key, timeout=5.0) 
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": prompt}]
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"⚠️ Alerta de Red (OpenAI omitido por latencia): {e}")
        return None

def determinar_siguiente_accion(estado_caso_str, acciones_disponibles_str):
    prompt = f"""
    Eres un Investigador Financiero Forense IA.
    ESTADO DEL CASO: {estado_caso_str}
    ACCIONES DISPONIBLES: {acciones_disponibles_str}
    
    Elige exactamente UNA acción. Responde ÚNICAMENTE en JSON:
    {{
      "selected_action_id": "ID de la accion",
      "question": "Pregunta a resolver",
      "why_now": "Por qué es el mejor paso",
      "supports_if": "Qué apoya el fraude",
      "weakens_if": "Qué prueba legitimidad"
    }}
    """
    res = _llamar_openai_json(prompt)
    
    # 🔥 MODO BLINDADO: Si el LLM falla o tarda, Python inyecta el siguiente paso lógico.
    if not res or "error" in res:
        try:
            acciones_dict = json.loads(acciones_disponibles_str)
            fallback_id = list(acciones_dict.keys())[0] if acciones_dict else "A-005"
        except:
            fallback_id = "A-005"
            
        return {
            "selected_action_id": fallback_id,
            "question": "Continuar con el protocolo de verificación estructurada.",
            "why_now": "El sistema ha activado el protocolo de contingencia por latencia de red para asegurar la continuidad de la auditoría.",
            "supports_if": "Se confirman discrepancias en los registros locales.",
            "weakens_if": "Los documentos soportan la transacción."
        }
    return res

def revision_critica(estado_caso_str):
    prompt = f"""
    Eres un Revisor Adversario. Encuentra la debilidad en la hipótesis actual.
    ESTADO: {estado_caso_str}
    Responde en JSON:
    {{"weakest_inference": "...", "alternative_explanation": "...", "missing_evidence": ["..."], "critical_objection": true}}
    """
    res = _llamar_openai_json(prompt)
    
    if not res or "error" in res:
        return {
            "weakest_inference": "Asumir fraude únicamente por la estructura del movimiento.",
            "alternative_explanation": "Podría tratarse de un ajuste técnico de caja o una operación intercompañía legítima.",
            "missing_evidence": ["Contratos mercantiles", "Estados de cuenta de la contraparte"],
            "critical_objection": True
        }
    return res

def generar_reporte_forense(estado_caso_str, exposicion_mxn):
    api_key = os.getenv("OPENAI_API_KEY")
    # Para el PDF final le damos 8 segundos
    client = openai.OpenAI(api_key=api_key, timeout=8.0) 
    
    prompt = f"Actúa como un Sistema Experto Forense. Redacta el dictamen de este caso: {estado_caso_str}. Exposición: ${exposicion_mxn}. Usa formato Markdown."
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception:
        return f"**DICTAMEN TÉCNICO DE CONTINGENCIA**\n\n**1. Resumen:** Se completó la investigación automatizada de la topología transaccional.\n**2. Exposición:** ${exposicion_mxn:,.2f} MXN.\n**3. Disposición:** HUMAN_REVIEW_REQUIRED.\n*(Nota: Reporte generado en modo local por interrupción de conexión con el motor LLM).*."

def responder_pregunta_juez(estado_caso_str, pregunta):
    api_key = os.getenv("OPENAI_API_KEY")
    client = openai.OpenAI(api_key=api_key, timeout=8.0)
    prompt = f"Responde esta pregunta del juez basado SOLO en el caso: {estado_caso_str}. Pregunta: {pregunta}"
    try:
        response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
        return response.choices[0].message.content
    except Exception:
        return "El sistema se encuentra temporalmente sin conexión con el servidor de inferencia. Sin embargo, toda la evidencia recabada está disponible en el Ledger inmutable en pantalla."