from google import genai
import os
from dotenv import load_dotenv

# Cargar la llave secreta desde el archivo .env
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("Error: No se encontró la API Key. Revisa tu archivo .env")
    exit()

# Configurar el nuevo cliente de la IA
client = genai.Client(api_key=api_key)

def generar_reporte_forense(evidencia_ciclo):
    print("🤖 Agente Gemini analizando la evidencia...")
    
    prompt = f"""
    Actúa como un Auditor Forense Senior. 
    Tu sistema de detección ha encontrado el siguiente rastro de transacciones sospechosas que indica un esquema circular de fraude (round-tripping):
    Ruta del dinero: {evidencia_ciclo}
    
    Redacta un "Archivo de Caso" (Case File) muy breve, profesional y directo.
    Debes incluir:
    1. Resumen del esquema detectado.
    2. Rastro de evidencia documentada.
    3. Conclusión y recomendación.
    
    REGLA ESTRICTA: Eres un auditor basado en hechos. No acuses de fraude a ninguna empresa externa si no tienes más datos, limítate a señalar la irregularidad contable en el flujo de dinero.
    """
    
    try:
        # Nueva sintaxis para interactuar con la IA
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt
        )
        print("\n" + "="*50)
        print("📄 ARCHIVO DE CASO GENERADO")
        print("="*50)
        print(response.text)
        return response.text
    except Exception as e:
        print(f"Error de conexión con la IA: {e}")
        return None

if __name__ == "__main__":
    ciclo_detectado = "Cuenta 19 -> Cuenta 26 -> Cuenta 20 -> Cuenta 19"
    generar_reporte_forense(ciclo_detectado)