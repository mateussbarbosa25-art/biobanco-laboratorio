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

# --- ESTILIZAÇÃO CSS AVANÇADA (ZENDO NEXUS THEME) ---
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    div[data-testid="stSidebar"] { background-color: #0f172a !important; }
    div[data-testid="stSidebar"] .stMarkdown, div[data-testid="stSidebar"] label { color: #ffffff !important; }
    
    /* Top Bar */
    .top-bar {
        background-color: #ffffff; padding: 15px; border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05); margin-bottom: 20px;
        display: flex; justify-content: space-between; align-items: center;
    }
    
    /* Cards de Métricas Modernos */
    .metric-card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .metric-title {
        color: #64748b;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-value {
        color: #1e293b;
        font-size: 1.875rem;
        font-weight: 700;
        margin-top: 4px;
    }
    .status-alert {
        background-color: #7f1d1d;
        border-left: 5px solid #ef4444;
        padding: 15px;
        border-radius: 4px;
        color: #fca5a5;
    }
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
            resultado_final TEXT
        )
    """)
    
    colunas_novas = {
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

# =========================================================================
#  TELA DE LOGIN (BLOQUEIO INICIAL)
# =========================================================================
if not st.session_state["logado"]:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col_login_1, col_login_2, col_login_3 = st.columns([1, 2, 1])
    
    with col_login_2:
        st.markdown("""
            <div style='text-align: center; margin-bottom: 25px;'>
                <h1 style='color: #2563eb; font-weight: 800; letter-spacing: -1px;'>🔬 LIMS BIOBANK</h1>
                <p style='color: #64748b; font-size: 14px;'>Sistema Avançado de Gestão Microbiológica</p>
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form", border=True):
            campo_usuario = st.text_input("Usuário:", placeholder="Ex: admin").strip()
            campo_senha = st.text_input("Senha:", type="password", placeholder="••••••••")
            botao_entrar = st.form_submit_button("Entrar no Sistema", use_container_width=True)
            
            if botao_entrar:
                hash_digitado = crypto_pass(campo_senha)
                cursor.execute("SELECT nome_completo FROM usuarios WHERE usuario = ? AND senha_hash = ?", (campo_usuario, hash_digitado))
                res_user = cursor.fetchone()
                if res_user:
                    st.session_state["logado"] = True
                    st.session_state["nome_usuario"] = res_user[0]
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")
                    
        st.markdown("<p style='text-align: center; color: #94a3b8; font-size: 12px; margin-top: 10px;'>Padrão: admin / lab133</p>", unsafe_allow_html=True)
    st.stop()

# =========================================================================
#  VISTAS DAS PÁGINAS (PÁGINAS DO SISTEMA LOGADO)
# =========================================================================

def render_painel_amostras():
    st.markdown("""
        <div class='top-bar'>
            <span style='font-size: 20px; font-weight: 700; color: #1e293b;'>📋 Gerenciamento Geral de Amostras</span>
            <span style='color: #10b981; font-size: 13px; font-weight: 600;'>● Cluster Online</span>
        </div>
    """, unsafe_allow_html=True)
    
    # Atualiza dados dinamicamente do SQLite
    df_dados = pd.read_sql_query("SELECT * FROM monitoramento ORDER BY id DESC", conn)
    
    # Métricas Operacionais Avançadas
    total_amostras = len(df_dados)
    alertas_risco = len(df_dados[df_dados['nivel_risco'].str.contains("Alerta|Crítico|Alta", case=False, na=False)])
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'<div class="metric-card"><div class="metric-title">Amostras Custodiadas</div><div class="metric-value">{total_amostras} <span style="font-size:13px; color:#64748b; font-weight:normal;">vials</span></div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card" style="border-left-color: #ef4444;"><div class="metric-title" style="color: #ef4444;">Níveis de Risco / Alerta</div><div class="metric-value" style="color: #ef4444;">{alertas_risco} <span style="font-size:13px; font-weight:normal;">flags</span></div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card" style="border-left-color: #10b981;"><div class="metric-title">Analistas Ativos</div><div class="metric-value">{df_dados["analista"].nunique() if total_amostras > 0 else 0}</div></div>', unsafe_allow_html=True)
    
    st.write("")
    st.subheader("DataGrid de Amostras Cadastradas", divider="blue")
    
    # Filtro Segmentado Moderno
    filtro_risco = st.segmented_control(
        "Filtrar Malha por Nível de Risco:",
        options=["Todos", "Seguro", "Nivel de Alerta"],
        default="Todos"
    )
    
    if total_amostras > 0:
        df_filtrado = df_dados.copy()
        if filtro_risco == "Seguro":
            df_filtrado = df_filtrado[df_filtrado["nivel_risco"].str.contains("Seguro|N/A", case=False, na=False)]
        elif filtro_risco == "Nivel de Alerta":
            df_filtrado = df_filtrado[df_filtrado["nivel_risco"].str.contains("Alerta|Crítico|Alta", case=False, na=False)]
            
        st.dataframe(df_filtrado, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma amostra localizada na infraestrutura local do banco SQLite.")

def render_cadastrar_amostra():
    st.markdown("""
        <div class='top-bar'>
            <span style='font-size: 20px; font-weight: 700; color: #1e293b;'>➕ Adicionar Novo Registro Microbiológico</span>
            <span style='color: #64748b; font-size: 13px;'>Módulo de Entrada Direta</span>
        </div>
    """, unsafe_allow_html=True)
    
    with st.form("form_cadastro_amostra", border=True):
        colA, colB = st.columns(2)
        with colA:
            codigo = st.text_input("Código de Barras ID (Único):", placeholder="Ex: BIO-999")
            origem = st.text_input("Origem da Amostra:")
            area = st.text_input("Área Laboratorial:")
            ponto_coleta = st.text_input("Ponto de Coleta:")
            metodo = st.selectbox("Método de Análise:", ["Cultura Direta", "PCR Rápido", "Sequenciamento NGS", "Isolamento Placa"])
        
        with colB:
            data_coleta = st.date_input("Data de Coleta:", datetime.now()).strftime("%Y-%m-%d")
            analista = st.text_input("Analista Responsável:", value=st.session_state["nome_usuario"])
            contagem_ufc = st.number_input("Contagem UFC:", min_value=0, step=1, value=0)
            nivel_risco = st.selectbox("Nível de Risco Biológico:", ["Seguro", "Nivel de Alerta", "Risco Crítico"])
            
