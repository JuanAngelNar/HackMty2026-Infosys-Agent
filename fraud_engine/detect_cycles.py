import pandas as pd
import networkx as nx
import os

def find_money_laundering_rings(tx_file):
    print("🔎 Iniciando auditoría forense de transacciones...")
    
    # 1. Cargar los datos de transacciones de AML Sim
    try:
        df = pd.read_csv(tx_file)
        print(f"Cargadas {len(df)} transacciones bancarias.")
    except Exception as e:
        print(f"Error al cargar transacciones: {e}")
        return

    # 2. Construir el grafo dirigido (quién le manda a quién)
    # Ajusta los nombres 'SENDER_ACCOUNT_ID' y 'RECEIVER_ACCOUNT_ID' si tu CSV los llama diferente
    try:
        G = nx.from_pandas_edgelist(
            df, 
            source='ACCOUNT_ID', 
            target='COUNTER_PARTY_ACCOUNT_NUM', 
            create_using=nx.DiGraph()
        )
        print(f"Grafo financiero construido: {G.number_of_nodes()} cuentas, {G.number_of_edges()} transferencias.")
    except KeyError:
        print("Revisa los nombres de las columnas en tu archivo tx.csv")
        return

    # 3. Detectar ciclos (dinero que se mueve en círculos)
    print("⏳ Buscando esquemas de round-tripping...")
    cycles = list(nx.simple_cycles(G))
    
    # Filtrar para encontrar anillos sospechosos (ej. A -> B -> C -> A)
    fraud_rings = [ring for ring in cycles if len(ring) > 2]
    
    print(f"\n🚨 ¡ALERTA ROJA! Se detectaron {len(fraud_rings)} posibles esquemas circulares.")
    
    # Mostrar el primer caso como evidencia para el archivo del caso
    if fraud_rings:
        print("\nEjemplo de rastro de evidencia encontrado:")
        print(" -> ".join(map(str, fraud_rings[0])) + f" -> {fraud_rings[0][0]}")

if __name__ == "__main__":
    tx_path = os.path.join('data_ingestion', 'tx.csv')
    find_money_laundering_rings(tx_path)


