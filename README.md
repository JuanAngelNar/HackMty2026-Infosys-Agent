# Infosys Agent

Agente forense de inteligencia artificial para investigar registros financieros, rastrear relaciones entre transacciones y organizar archivos de casos para revisión humana.

## Módulos

- `data_ingestion/`: ingestión de XML, listas del SAT y otras fuentes financieras.
- `fraud_engine/`: modelado de redes y rastreo del flujo de dinero.
- `llm_agent/`: lógica del agente, análisis y generación de expedientes.
- `frontend/`: aplicación web de revisión construida con Streamlit.

## Inicio rápido

1. Crea un entorno virtual e instala las dependencias de `requirements.txt`.
2. Copia `.env.example` a `.env` y agrega las API keys localmente.
3. Coloca los datos de entrada en `data_ingestion/`.
4. Ejecuta la interfaz con `streamlit run frontend/app.py` cuando exista el punto de entrada.

Los datos financieros y los secretos deben permanecer fuera del repositorio. Revisa todos los hallazgos antes de tomar decisiones operativas o legales.
