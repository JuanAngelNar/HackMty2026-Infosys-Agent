import networkx as nx
from pyvis.network import Network
import os

def generar_html_grafo(ciclo_nodos, filename="grafo_fraude.html"):
    # 1. Creamos el grafo dirigido
    G = nx.DiGraph()
    
    # 2. Agregamos los nodos dinámicamente según lo que encontró el algoritmo
    for i, nodo in enumerate(ciclo_nodos):
        if i == 0:
            G.add_node(str(nodo), title="Cuenta Origen (Sospechosa)", color="#FF4B4B", size=25)
        else:
            G.add_node(str(nodo), title=f"Cuenta Intermediaria {i}", color="#1f77b4", size=15)
            
    # 3. Agregamos las aristas cerrando el ciclo automáticamente
    for i in range(len(ciclo_nodos)):
        origen = str(ciclo_nodos[i])
        destino = str(ciclo_nodos[(i + 1) % len(ciclo_nodos)]) # El último conecta con el primero
        G.add_edge(origen, destino, color="#FF4B4B", weight=2)

    # 4. Configuramos el lienzo interactivo
    filepath = os.path.join("reports", filename)
    os.makedirs("reports", exist_ok=True)
    
    net = Network(height="400px", width="100%", directed=True, bgcolor="#0E1117", font_color="white")
    net.force_atlas_2based()
    net.from_nx(G)
    net.save_graph(filepath)
    
    return filepath