import streamlit as st
import pandas as pd
import sqlite3
import hashlib
from datetime import datetime
import time

# --- CONFIGURAÇÃO GERAL DA PÁGINA ---
st.set_page_config(
    page_title="LIMS Biobank Pro - Nexus Edition", 
    page_icon="🔬", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILIZAÇÃO CSS AVANÇADA (NEXUS MODERN LAB THEME) ---
st.markdown("""
    <style>
    .stApp { background-color: #0f172a; }
    .login-box {
        background-color: #1e293b; padding: 40px; border-radius: 16px;
        border: 1px solid #334155; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3); margin-top: 5%;
    }
    .top-bar {
        background-color: #1e293b; padding: 15px; border-radius: 12px; border: 1px solid #334155;
        margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;
    }
    .metric-card {
        background-color: #1e293b; border-radius: 12px; padding: 20px;
        border: 1px solid #334155; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .metric-title { color: #94a3b8; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; }
    .metric-value { color: #f8fafc; font-size: 1.875rem; font-weight: 700; margin-top: 4px; }
    div[data-testid="stSidebar"] { background-color: #090d16 !important; }
    div[data-testid="stSidebar"] .stMarkdown, div[data-testid="stSidebar"] label { color: #ffffff !important; }
    div[data-testid="stForm"] { background-color: transparent !important; border: none !important; padding: 0 !important; }
    </style>
""", unsafe_allow_html=True)

# --- FUNÇÕES CORE / BANCO DE DADOS ---
def crypto_pass(texto_senha):
    return hashlib.sha256(texto_senha.encode('utf-8')).hexdigest()

def db_start():
    conn = sqlite3.connect('biobanco_laboratorio.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS monitoramento (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            codigo TEXT UNIQUE NOT NULL, 
            origem TEXT, 
            area TEXT, 
            ponto_coleta TEXT, 
            metodo TEXT, 
            data_coleta TEXT, 
            analista TEXT, 
            contagem_ufc INTEGER, 
            nivel_risco TEXT, 
            tipo_contaminante TEXT, 
            identificacao_micro TEXT, 
            status_acao TEXT, 
            forma TEXT, 
            margem TEXT, 
            pigmento TEXT, 
            coloracao_gram TEXT, 
            catalase TEXT, 
            oxidase TEXT, 
            resultado_final TEXT,
            frequencia TEXT,
            koh TEXT,
            metodo_terceirizado TEXT,
            empresa_terceira TEXT,
            data_finalizacao TEXT
        )
    """)
    
    colunas_novas = {
        "frequencia": "TEXT DEFAULT 'N/A'",
        "koh": "TEXT DEFAULT 'N/A'",
        "metodo_terceirizado": "TEXT DEFAULT 'N/A'",
        "empresa_terceira": "TEXT DEFAULT 'N/A'",
        "data_finalizacao": "TEXT DEFAULT 'N/A'",
        "contagem_ufc": "INTEGER DEFAULT 0", "nivel_risco": "TEXT DEFAULT 'N/A'",
        "tipo_contaminante": "TEXT DEFAULT 'N/A'", "identificacao_micro": "TEXT DEFAULT 'N/A'",
        "status_acao": "TEXT DEFAULT 'N/A'", "forma": "TEXT DEFAULT 'N/A'",
        "margem": "TEXT DEFAULT 'N/A'", "pigmento": "TEXT DEFAULT 'N/A'",
        "coloracao_gram": "TEXT DEFAULT 'N/A'", "catalase": "TEXT DEFAULT 'N/A'",
        "oxidase": "TEXT DEFAULT 'N/A'", "resultado_final": "TEXT DEFAULT 'N/A'"
    }
    for col, tipo in colunas_novas.items():
        try:
            cursor.execute(f"ALTER TABLE monitoramento ADD COLUMN {col} {tipo}")
        except sqlite3.OperationalError:
            pass

    cursor.execute("CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario TEXT UNIQUE NOT NULL, senha_hash TEXT NOT NULL, nome_completo TEXT)")
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone() == 0:
        hash_adm = crypto_pass("lab133")
        cursor.execute("INSERT INTO usuarios (usuario, senha_hash, nome_completo) VALUES (?, ?, ?)", ("admin", hash_adm, "Administrador Geral"))
    conn.commit()
    return conn, cursor

conn, cursor = db_start()

# --- ESTADO DE SESSÃO ---
if "logado" not in st.session_state:
    st.session_state["logado"] = False
if "nome_usuario" not in st.session_state:
    st.session_state["nome_usuario"] = ""
if "aba_atual" not in st.session_state:
    st.session_state["aba_atual"] = "📦 Painel de Amostras"

# --- DICIONÁRIOS EXTRAÍDOS DA PLANILHA ---
OPCOES_ORIGEM = ["Environmental Monitoring", "Storage Tanks", "Amostra", "Processes"]
OPCOES_AREA = ["Laboratory", "Dissolution", "Line 2", "Line 3", "Line 4", "Line 5", "SBTA 1", "SBTA 2", "Autoclave"]
OPCOES_PONTO_COLETA = [
    "Inoculation Room", "Flow Room", "Preparation", "Weighing", "Team Member", "Dissolution Room", 
    "Inoculation Anteroom", "Laminar Flow FLA001", "Laminar Flow FLA002", "Laminar Flow FLA003", 
    "Laminar Flow FLA004", "Laminar Flow FLA005", "Laminar Flow FLA006", "Dissolution Tank", 
    "Pump Outlet Filter", "Weighing Bench", "Becker", "Bucket", "Spatula", "Floor", "Wall", 
    "Hands (glove)", "Lab Coat", "Drain Dissolution", "Weighing Drain", "Hand-Washing Sink", "Feedstock", "Aseptic Salts"
]
OPCOES_METHOD = ["Petrifilm AC", "Petrifilm EB", "TSAC", "YPD", "Petrifilm YM", "Cultura Direta", "PCR Rápido", "Sequenciamento NGS"]
OPCOES_FORMA = ["Punctiform", "Circular", "Filamentous", "Irregular", "Rhizoid", "Fusiform"]
OPCOES_MARGEM = ["Round", "Wavy", "Lobulated", "Filamentous", "Spiral"]
OPCOES_RISCO = ["Seguro", "Nivel de Alerta", "Risco Crítico"]
OPCOES_FREQUENCIA = ["Mensal", "Semanal", "Diário", "N/A"]

# =========================================================================
#  FLUXO CENTRALIZADO DE RENDERIZAÇÃO
# =========================================================================

if not st.session_state["logado"]:
    col1, col2, col3 = st.columns([1, 1.8, 1])
    with col2:
        st.html("<div class='login-box'><div style='text-align: center; margin-bottom: 30px;'><span style='font-size: 42px;'>🔬</span><h1 style='color: #f8fafc; font-weight: 800; letter-spacing: -1px; margin-top: 10px; margin-bottom: 5px;'>NEXUS LIMS</h1><p style='color: #94a3b8; font-size: 14px;'>Acesso Restrito ao Biobanco de Segurança</p></div>")
        
        with st.form("login_form"):
            campo_usuario = st.text_input("Identificação do Usuário:", placeholder="Ex: admin").strip()
            campo_senha = st.text_input("Chave de Acesso:", type="password", placeholder="••••••••")
            st.markdown("<br>", unsafe_allow_html=True)
            botao_entrar = st.form_submit_button("🔒 Autenticar no Servidor", use_container_width=True)
            
            if botao_entrar:
                hash_digitado = crypto_pass(campo_senha)
                cursor.execute("SELECT nome_completo FROM usuarios WHERE usuario = ? AND senha_hash = ?", (campo_usuario, hash_digitado))
                res_user = cursor.fetchone()
                if res_user:
                    st.session_state["logado"] = True
                    st.session_state["nome_usuario"] = str(res_user[0]) if isinstance(res_user, tuple) else str(res_user)
                    st.toast("Autenticação autorizada!", icon="🔑")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Credenciais de segurança incorretas.")
                    
        st.html("<div style='text-align: center; margin-top: 25px; border-top: 1px solid #334155; padding-top: 15px;'><p style='color: #64748b; font-size: 11px; margin: 0;'>Padrão de Fábrica: admin / lab133</p></div></div>")

else:
    st.sidebar.markdown("<h3 style='color: #60a5fa; margin-top: 10px;'>🔬 NEXUS LIMS</h3>", unsafe_allow_html=True)
    st.sidebar.caption(f"Operador: {st.session_state['nome_usuario']}")
    st.sidebar.markdown("---")
    
    modulo = st.sidebar.radio(
        "📋 Módulos do Sistema", 
        ["📦 Painel de Amostras", "➕ Cadastrar Nova Amostra"],
        index=0 if st.session_state["aba_atual"] == "📦 Painel de Amostras" else 1,
        key="navegacao_radio"
    )
    st.session_state["aba_atual"] = modulo

    # --- TOP BAR ---
    st.markdown(f"""
        <div class='top-bar'>
            <span style='color: #f8fafc; font-weight: 700; font-size: 1.2rem;'>{st.session_state["aba_atual"]}</span>
            <span style='color: #94a3b8; font-size: 0.9rem;'>Nexus Edition V1.0</span>
        </div>
    """, unsafe_allow_html=True)
    
    if st.sidebar.button("🚪 Encerrar Sessão", use_container_width=True):
        st.session_state["logado"] = False
        st.session_state["nome_usuario"] = ""
        st.rerun()

    # =========================================================================
    #  MÓDULO: PAINEL DE AMOSTRAS
    # =========================================================================
    if st.session_state["aba_atual"] == "📦 Painel de Amostras":
        df_metricas = pd.read_sql_query("SELECT nivel_risco FROM monitoramento", conn)
        total_amostras = len(df_metricas)
        criticas = len(df_metricas[df_metricas['nivel_risco'] == "Risco Crítico"])
        alertas = len(df_metricas[df_metricas['nivel_risco'] == "Nivel de Alerta"])
        
        m1, m2, m3 = st.columns(3)
        m1.markdown(f"<div class='metric-card'><div class='metric-title'>Total de Amostras</div><div class='metric-value'>{total_amostras}</div></div>", unsafe_allow_html=True)
        m2.markdown(f"<div class='metric-card'><div class='metric-title'>Status de Alerta</div><div class='metric-value' style='color: #f59e0b;'>{alertas}</div></div>", unsafe_allow_html=True)
        m3.markdown(f"<div class='metric-card'><div class='metric-title'>Risco Crítico (Contaminadas)</div><div class='metric-value' style='color: #ef4444;'>{criticas}</div></div>", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
