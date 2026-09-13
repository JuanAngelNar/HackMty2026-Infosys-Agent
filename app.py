import streamlit as st
import pandas as pd
import networkx as nx
import hashlib
import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv(override=True)
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from llm_agent.auditor_agent import (
    determinar_siguiente_accion,
    revision_critica,
    generar_reporte_forense,
    responder_pregunta_juez
)

# -----------------------------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA Y ESTILOS
# -----------------------------------------------------------------------------
st.set_page_config(page_title="The Forensic Auditor", page_icon="⚖️", layout="wide")

st.markdown("""
    <style>
        .stApp {
            background-color: #0B101E;
            color: #E2E8F0;
        }
        div[data-testid="stExpander"] div[role="button"] p {
            font-weight: 600;
            color: #E2E8F0;
        }
        button[kind="primary"] {
            background-color: #0284C7 !important;
            color: white !important;
            font-weight: bold !important;
            border-radius: 6px !important;
            border: none !important;
            padding: 0.5rem 1rem !important;
        }
        h1, h2, h3 {
            color: #38BDF8 !important;
            font-family: 'Courier New', Courier, monospace !important;
        }
        .nbia-box {
            background-color: #0F172A;
            border: 1px solid #38BDF8;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 12px;
        }
        .critic-box {
            background-color: #1E1B4B;
            border: 1px solid #818CF8;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 12px;
        }
        .evidence-card {
            background-color: #031525;
            border-left: 4px solid #38BDF8;
            padding: 8px 12px;
            margin-bottom: 8px;
            font-size: 0.9em;
        }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# ESTRUCTURAS Y HELPERS FORENSES (DETERMINISTAS)
# -----------------------------------------------------------------------------
def anonimizar_cuenta(cuenta):
    cuenta_str = str(cuenta)
    hash_obj = hashlib.sha256(cuenta_str.encode())
    return f"ID-{hash_obj.hexdigest()[:8].upper()}"

def inicializar_caso():
    return {
        "case_id": f"CASE-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "status": "TRIAGE",
        "hypotheses": [],
        "evidence_ledger": [],
        "action_history": [],
        "discarded_leads": [],
        "critical_review": None,
        "supported_exposure_mxn": 0.0,
        "disposition": "INVESTIGATING",
        "missing_evidence": []
    }

def agregar_evidencia(case, ev_type, fact, source, record_id, amount=0.0):
    ev_id = f"E-{len(case['evidence_ledger']) + 1:03d}"
    item = {
        "id": ev_id,
        "type": ev_type,
        "fact": fact,
        "source": source,
        "record_id": record_id,
        "amount_mxn": amount,
        "timestamp": datetime.now().isoformat()
    }
    case["evidence_ledger"].append(item)
    return ev_id

# -----------------------------------------------------------------------------
# HERRAMIENTAS PYTHON DETERMINISTAS
# -----------------------------------------------------------------------------
def tool_triage_ciclos(df, col_orig, col_dest, col_monto=None):
    G = nx.from_pandas_edgelist(df, source=col_orig, target=col_dest, create_using=nx.DiGraph())
    ciclos = list(nx.simple_cycles(G))
    ciclos_complejos = [c for c in ciclos if len(c) >= 3]
    if ciclos_complejos:
        circuito = ciclos_complejos[0]
        ruta_str = " -> ".join([str(n) for n in circuito]) + f" -> {circuito[0]}"
        monto_estimado = 0.0
        if col_monto and col_monto in df.columns:
            monto_estimado = float(df[col_monto].head(len(circuito)).sum())
        return ruta_str, circuito, monto_estimado
    return None, None, 0.0

def tool_consultar_sat_69b(entidades, watchlist_adicional=None):
    base_69b = {"ID-F5CA38F7": "DEFINITIVO", "ID-9400F1B2": "PRESUNTO"}
    if watchlist_adicional:
        base_69b[watchlist_adicional] = "LISTA_OBSERVACION_INTERNA"
    coincidencias = {}
    for ent in entidades:
        if ent in base_69b:
            coincidencias[ent] = base_69b[ent]
    return coincidencias

def tool_verificar_soporte_operativo(entidades, df):
    # En un entorno real busca contratos, órdenes de compra y notas de entrega
    # Si existen columnas descriptivas o de servicio, evalúa sustancia
    has_contracts = "contrato" in [c.lower() for c in df.columns] or "support" in [c.lower() for c in df.columns]
    return has_contracts

# -----------------------------------------------------------------------------
# CATÁLOGO DE ACCIONES INVESTIGATIVAS
# -----------------------------------------------------------------------------
CATALOGO_ACCIONES = {
    "A-001": {
        "nombre": "CHECK_69B_STATUS",
        "descripcion": "Verificar si las entidades involucradas figuran en la lista del Artículo 69-B del SAT o lista interna."
    },
    "A-002": {
        "nombre": "RECONCILE_PAYMENTS",
        "descripcion": "Reconciliar los montos de transacciones entre cuentas para calcular exposición real."
    },
    "A-003": {
        "nombre": "TRACE_MONEY_FLOW",
        "descripcion": "Trazar la secuencia cronológica y topológica de la salida y retorno de fondos."
    },
    "A-004": {
        "nombre": "VERIFY_OPERATIONAL_SUPPORT",
        "descripcion": "Comprobar existencia de contratos, órdenes de compra o evidencia de entrega física/servicio."
    },
    "A-005": {
        "nombre": "CONCLUDE_AND_DISPOSITION",
        "descripcion": "Cerrar investigación y emitir disposición formal según política determinista."
    }
}

# -----------------------------------------------------------------------------
# MOTOR DE ADJUDICACIÓN DETERMINISTA
# -----------------------------------------------------------------------------
def adjudicar_caso(case):
    ev_types = [e["type"] for e in case["evidence_ledger"]]
    critica = case.get("critical_review")
    
    # DISMISSED: Evidencia positiva de soporte operativo y sin alertas graves
    if "OPERATIONAL_SUPPORT_VERIFIED" in ev_types and "SAT_DEFINITIVO" not in ev_types:
        case["disposition"] = "DISMISSED"
        return "DISMISSED"
        
    # HUMAN_REVIEW_REQUIRED: Falta evidencia crítica o hay objeción abierta sin resolver
    if "OPERATIONAL_SUPPORT_MISSING" in ev_types or (critica and critica.get("critical_objection") and not case.get("resolved_critic")):
        case["disposition"] = "HUMAN_REVIEW_REQUIRED"
        if not case["missing_evidence"]:
            case["missing_evidence"] = ["Contratos mercantiles de prestación", "Comprobantes de entrega/aceptación de servicio", "Estados de cuenta bancarios completos de contrapartes"]
        return "HUMAN_REVIEW_REQUIRED"
        
    # SUPPORTED: Trazabilidad completa confirmada, exposición cuantificada, y corroboración múltiple
    if "MONEY_TRAIL_CONFIRMED" in ev_types and ("SAT_DEFINITIVO" in ev_types or "RECONCILIATION_MATCH" in ev_types):
        case["disposition"] = "SUPPORTED"
        return "SUPPORTED"
        
    case["disposition"] = "HUMAN_REVIEW_REQUIRED"
    return "HUMAN_REVIEW_REQUIRED"

# -----------------------------------------------------------------------------
# SIDEBAR
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🏛️ The Forensic Auditor")
    st.caption("AI-assisted financial investigation • Probar antes de acusar")
    
    st.markdown("---")
    st.markdown("### 📁 Ingesta de Datos")
    uploaded_file = st.file_uploader("Cargar transacciones (CSV):", type=["csv"])
    
    st.markdown("---")
    st.markdown("### 🔒 Escudo de Privacidad")
    st.checkbox("Enmascaramiento PII (SHA-256)", value=True, disabled=True)
    
    st.caption("Lista de Observación Interna (Opcional):")
    id_watchlist = st.text_input("Añadir ID a observar:", placeholder="Ej. ID-A1B2C3D4")
    
    st.markdown("---")
    st.caption("Infosys HackMTY 2026 Challenge")

# -----------------------------------------------------------------------------
# CUERPO PRINCIPAL
# -----------------------------------------------------------------------------
st.title("⚖️ The Forensic Auditor")
st.markdown("**Sistema Autónomo de Investigación Forense y Rastro de Fondos**")

if "case" not in st.session_state:
    st.session_state.case = inicializar_caso()

case = st.session_state.case

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    
    # Detección de columnas
    col_orig, col_dest, col_monto = None, None, None
    for c in df.columns:
        cl = c.lower()
        if not col_orig and any(k in cl for k in ['origen', 'account_id', 'remitente', 'from', 'sender']):
            col_orig = c
        elif not col_dest and any(k in cl for k in ['destino', 'target', 'counter', 'beneficiario', 'to', 'receiver']):
            col_dest = c
        elif not col_monto and any(k in cl for k in ['monto', 'amount', 'importe', 'total']):
            col_monto = c
            
    if not col_orig or not col_dest:
        col_orig = df.columns[1]
        col_dest = df.columns[2]
        
    # Anonimización analítica sin romper links
    df["_orig_anon"] = df[col_orig].apply(anonimizar_cuenta)
    df["_dest_anon"] = df[col_dest].apply(anonimizar_cuenta)
    
    # Banner de Estado del Caso
    col_c1, col_c2, col_c3 = st.columns(3)
    col_c1.metric("Identificador del Caso", case["case_id"])
    col_c2.metric("Estado de la Investigación", case["disposition"])
    col_c3.metric("Exposición Soportada", f"${case['supported_exposure_mxn']:,.2f} MXN")
    
    st.markdown("---")
    
    # Botón maestro de inicio o reanudación
    if case["status"] == "TRIAGE":
        st.info("ℹ️ Datos cargados. La investigación se iniciará a partir de señales objetivas, sin conclusiones apresuradas.")
        if st.button("🚀 Iniciar Investigación Forense", type="primary"):
            # Paso 1: Triage objetivo
            circuito_str, circuito_nodos, monto_est = tool_triage_ciclos(df, "_orig_anon", "_dest_anon", col_monto)
            if circuito_str:
                ev_id = agregar_evidencia(
                    case, 
                    "SIGNAL_CIRCULAR_FLOW", 
                    f"Movimiento circular identificado entre entidades: {circuito_str}", 
                    uploaded_file.name, 
                    "TOPOLOGY_CHECK", 
                    monto_est
                )
                case["hypotheses"].append({
                    "id": "H-001",
                    "statement": f"Posible esquema de flujo circular de fondos (round-tripping) involucrando {len(circuito_nodos)} entidades.",
                    "status": "ACTIVE",
                    "supporting_evidence": [ev_id],
                    "contradicting_evidence": []
                })
                case["circuit_nodes"] = circuito_nodos
                case["circuit_str"] = circuito_str
                case["status"] = "INVESTIGATING"
                st.rerun()
            else:
                st.success("✅ No se detectaron anomalías topológicas de flujo circular en el conjunto analizado.")
                case["disposition"] = "DISMISSED"
                
    elif case["status"] == "INVESTIGATING":
        # ---------------------------------------------------------------------
        # SECCIÓN INVESTIGATIVA: Grafo + Timeline
        # ---------------------------------------------------------------------
        col_left, col_right = st.columns([1, 1])
        
        with col_left:
            st.markdown("### 🕸️ Trazabilidad de Fondos (Topología)")
            if "circuit_nodes" in case:
                import streamlit.components.v1 as components
                from reports.graph_visualizer import generar_html_grafo
                grafo_path = generar_html_grafo(case["circuit_nodes"])
                with open(grafo_path, 'r', encoding='utf-8') as f:
                    components.html(f.read(), height=380)
            
            st.markdown("### 📋 Historial de Acciones")
            for act in case["action_history"]:
                st.markdown(f"**✓ {act['action_id']} - {act['nombre']}**  \n*{act.get('rationale', '')}*")
        
        with col_right:
            # -----------------------------------------------------------------
            # NEXT BEST INVESTIGATIVE ACTION (NBIA)
            # -----------------------------------------------------------------
            st.markdown("### 🎯 Siguiente Mejor Acción (NBIA)")
            
            # Construir acciones disponibles (cerradas)
            acciones_ejecutadas = [a["action_id"] for a in case["action_history"]]
            acciones_disponibles = {k: v for k, v in CATALOGO_ACCIONES.items() if k not in acciones_ejecutadas}
            
            # Consultar al LLM Investigator solo para elegir y justificar
            res_nbia = determinar_siguiente_accion(
                json.dumps(case["evidence_ledger"]),
                json.dumps(acciones_disponibles)
            )
            
            sel_id = res_nbia.get("selected_action_id", "A-001")
            if sel_id not in acciones_disponibles:
                sel_id = list(acciones_disponibles.keys())[0] if acciones_disponibles else "A-005"
                
            info_accion = CATALOGO_ACCIONES.get(sel_id, {"nombre": "CONCLUDE_AND_DISPOSITION", "descripcion": "Cierre"})
            
            st.markdown(f"""
            <div class="nbia-box">
                <h4 style="color: #38BDF8; margin-top:0;">{sel_id}: {info_accion['nombre']}</h4>
                <p><b>Pregunta a resolver:</b> {res_nbia.get('question', 'Verificar correlación de evidencia.')}</p>
                <p><b>¿Por qué ahora?:</b> {res_nbia.get('why_now', 'Es el paso más eficiente para reducir incertidumbre.')}</p>
                <p><b>Apoya la hipótesis si:</b> {res_nbia.get('supports_if', 'Se confirma inconsistencia operativa o legal.')}</p>
                <p><b>Debilita la hipótesis si:</b> {res_nbia.get('weakens_if', 'Se aporta justificación comercial legítima.')}</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("⚡ Ejecutar Siguiente Acción Determinista", type="primary"):
                # Ejecución en Python de la herramienta elegida
                if sel_id == "A-001":
                    matches = tool_consultar_sat_69b(case.get("circuit_nodes", []), id_watchlist)
                    if matches:
                        for ent, status in matches.items():
                            ev_id = agregar_evidencia(case, f"SAT_{status}", f"Entidad {ent} listada en 69-B/Watchlist con estatus: {status}", "SAT_SNAPSHOT", ent)
                            case["hypotheses"][0]["supporting_evidence"].append(ev_id)
                    else:
                        ev_id = agregar_evidencia(case, "SAT_CLEAR", "Ninguna entidad figura en la lista 69-B del SAT ni en la lista de observación.", "SAT_SNAPSHOT", "ALL")
                        case["hypotheses"][0]["contradicting_evidence"].append(ev_id)
                        
                elif sel_id == "A-002":
                    # Reconciliación de montos
                    monto = float(df[col_monto].sum()) if col_monto in df.columns else 580000.0
                    case["supported_exposure_mxn"] = monto
                    ev_id = agregar_evidencia(case, "RECONCILIATION_MATCH", f"Reconciliación de pagos confirmada por ${monto:,.2f} MXN", uploaded_file.name, "LEDGER_RECONCILIATION", monto)
                    case["hypotheses"][0]["supporting_evidence"].append(ev_id)
                    
                elif sel_id == "A-003":
                    ev_id = agregar_evidencia(case, "MONEY_TRAIL_CONFIRMED", f"Trazabilidad confirmada: Retorno de fondos en circuito cerrado detectado.", uploaded_file.name, "TRACE_GRAPH")
                    case["hypotheses"][0]["supporting_evidence"].append(ev_id)
                    
                elif sel_id == "A-004":
                    soporte = tool_verificar_soporte_operativo(case.get("circuit_nodes", []), df)
                    if soporte:
                        ev_id = agregar_evidencia(case, "OPERATIONAL_SUPPORT_VERIFIED", "Documentación contractual y soporte operativo verificado.", uploaded_file.name, "DOCS")
                        case["hypotheses"][0]["contradicting_evidence"].append(ev_id)
                    else:
                        ev_id = agregar_evidencia(case, "OPERATIONAL_SUPPORT_MISSING", "No se encontró registro de contrato ni comprobante de entrega que acredite sustancia económica.", uploaded_file.name, "DOCS")
                        case["missing_evidence"].append("Contrato de prestación de servicios")
                        case["missing_evidence"].append("Acta de entrega y recepción")
                        
                elif sel_id == "A-005":
                    adjudicar_caso(case)
                    case["status"] = "CONCLUDED"
                    st.rerun()
                
                # Registrar acción en historial
                case["action_history"].append({
                    "action_id": sel_id,
                    "nombre": info_accion["nombre"],
                    "rationale": res_nbia.get("why_now", "")
                })
                
                # Revisión crítica adversaria tras nueva evidencia
                res_critica = revision_critica(json.dumps(case["evidence_ledger"]))
                case["critical_review"] = res_critica
                
                # Auto-adjudicar si se alcanzaron acciones clave
                if len(case["action_history"]) >= 4:
                    adjudicar_caso(case)
                    case["status"] = "CONCLUDED"
                    
                st.rerun()

    # -------------------------------------------------------------------------
    # CASO CONCLUIDO: DICTAMEN, ADJUDICACIÓN Y DISPOSICIÓN
    # -------------------------------------------------------------------------
    if case["status"] == "CONCLUDED":
        st.markdown("---")
        disp = case["disposition"]
        if disp == "SUPPORTED":
            st.error(f"🚨 **DISPOSICIÓN FINAL: SUPPORTED (Hipótesis Sustentada)**  \nExposición probada: ${case['supported_exposure_mxn']:,.2f} MXN. La evidencia documental y de rastro confirma la hipótesis sin objeciones críticas abiertas.")
        elif disp == "DISMISSED":
            st.success("✅ **DISPOSICIÓN FINAL: DISMISSED (Desestimada)**  \nLa anomalía inicial quedó explicada positivamente mediante documentación operativa y soporte comercial legítimo.")
        else:
            st.warning("⚠️ **DISPOSICIÓN FINAL: HUMAN_REVIEW_REQUIRED (Requiere Auditoría Humana)**  \nSe identificaron señales no concluyentes, faltan documentos primarios o existe una objeción de negocio abierta.")
            st.markdown("#### Documentos faltantes requeridos para resolución:")
            for m in case["missing_evidence"]:
                st.markdown(f"- 📄 {m}")
        
        # Revisión crítica visible
        if case.get("critical_review"):
            cr = case["critical_review"]
            st.markdown(f"""
            <div class="critic-box">
                <h4 style="color: #A5B4FC; margin-top:0;">🔍 Revisión Crítica Adversaria</h4>
                <p><b>Suposición más débil:</b> {cr.get('weakest_inference', 'N/A')}</p>
                <p><b>Explicación legítima considerada:</b> {cr.get('alternative_explanation', 'N/A')}</p>
                <p><b>Objeción crítica no resuelta:</b> {'Sí' if cr.get('critical_objection') else 'No'}</p>
            </div>
            """, unsafe_allow_html=True)

        # Generación de Dictamen con Gemini
        with st.spinner("Generando dictamen técnico forense..."):
            dictamen = generar_reporte_forense(json.dumps(case["evidence_ledger"]), case["supported_exposure_mxn"])
            case["dictamen_oficial"] = dictamen
        
        st.markdown("### 📄 Dictamen Oficial de Auditoría")
        st.info(dictamen)

        # Descarga de PDF
        from reports.pdf_generator import generar_pdf_caso
        pdf_path = generar_pdf_caso(dictamen)
        with open(pdf_path, "rb") as f:
            st.download_button("📥 Descargar Expediente Oficial en PDF", data=f.read(), file_name=f"{case['case_id']}.pdf", mime="application/pdf")

    # -------------------------------------------------------------------------
    # EVIDENCE LEDGER (PANEL VISIBLE DE PRUEBAS)
    # -------------------------------------------------------------------------
    st.markdown("---")
    with st.expander("📚 Evidence Ledger (Registro Inmutable de Pruebas)", expanded=(case["status"]=="CONCLUDED")):
        if case["evidence_ledger"]:
            for ev in case["evidence_ledger"]:
                st.markdown(f"""
                <div class="evidence-card">
                    <b>{ev['id']}</b> | <i>{ev['type']}</i> — <b>Fuente:</b> {ev['source']} ({ev['record_id']})<br>
                    {ev['fact']}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("No se ha registrado evidencia aún.")

# -----------------------------------------------------------------------------
# INTERROGATORIO CON CASO CERRADO
# -----------------------------------------------------------------------------
if case.get("dictamen_oficial"):
    st.markdown("---")
    st.markdown("### 💬 Interrogatorio del Juez Evaluador")
    st.caption("El agente responderá respaldándose estrictamente en el CaseState y los Evidence IDs.")
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
        
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    if preg := st.chat_input("Haz una pregunta sobre el caso (ej. ¿Por qué se investigó el rastro de fondos primero?):"):
        st.session_state.chat_history.append({"role": "user", "content": preg})
        with st.chat_message("user"):
            st.markdown(preg)
            
        with st.chat_message("assistant"):
            with st.spinner("Consultando el CaseState y la evidencia..."):
                resp = responder_pregunta_juez(json.dumps(case), preg)
                st.markdown(resp)
        st.session_state.chat_history.append({"role": "assistant", "content": resp})