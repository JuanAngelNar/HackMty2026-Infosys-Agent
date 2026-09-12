import pandas as pd
import os

def clean_sat_list(file_path):
    print("Iniciando procesamiento de la lista 69-B del SAT...")
    
    try:
        # El CSV del SAT suele tener codificación latin1 y un encabezado en las primeras filas
        df = pd.read_csv(file_path, encoding='latin1', skiprows=2)
    except Exception as e:
        print(f"Error al leer el archivo: {e}")
        return

    # Limpiar los nombres de las columnas para evitar errores por espacios invisibles
    df.columns = df.columns.str.strip()
    
    # Filtrar solo las empresas con situación "Definitiva" (fraude comprobado)
    try:
        df_clean = df[df['Situación del contribuyente'].str.contains('Definitivo', na=False, case=False)]
        
        # Seleccionar solo las columnas vitales para el cruce
        columnas_finales = ['RFC', 'Nombre del Contribuyente']
        df_final = df_clean[columnas_finales]
        
        # Generar el archivo de salida
        output_path = os.path.join('data_ingestion', 'efos_limpios.csv')
        df_final.to_csv(output_path, index=False, encoding='utf-8')
        
        print(f"¡Éxito! Se aislaron {len(df_final)} empresas fantasma confirmadas.")
        print(f"Archivo guardado en: {output_path}")
        
    except KeyError:
        print("Error: No se encontraron las columnas esperadas. Revisa los nombres en el CSV del SAT.")

if __name__ == "__main__":
    # Ruta relativa al archivo descargado
    ruta_archivo = os.path.join('data_ingestion', 'listado_69b.csv')
    clean_sat_list(ruta_archivo)

