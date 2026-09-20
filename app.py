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
            id INTEGER PRIMARY KEY AUTOINCREMENT, codigo TEXT UNIQUE NOT NULL, origem TEXT, area TEXT, 
            ponto_coleta TEXT, metodo TEXT, data_coleta TEXT, analista TEXT, contagem_ufc INTEGER, 
            nivel_risco TEXT, tipo_contaminante TEXT, identificacao_micro TEXT, status_acao TEXT, 
            forma TEXT, margem TEXT, pigmento TEXT, coloracao_gram TEXT, catalase TEXT, oxidase TEXT, resultado_final TEXT
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
#  VISTAS DAS PÁGINAS DO SISTEMA
# =========================================================================

def render_login():
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
                    st.session_state["nome_usuario"] = str(res_user[0])
                    st.toast("Autenticação autorizada!", icon="🔑")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Credenciais de segurança incorretas.")
                    
        st.html("<div style='text-align: center; margin-top: 25px; border-top: 1px solid #334155; padding-top: 15px;'><p style='color: #64748b; font-size: 11px; margin: 0;'>Padrão de Fábrica: admin / lab133</p></div></div>")

def render_painel_amostras():
    st.markdown("""
        <div class='top-bar'>
            <span style='font-size: 20px; font-weight: 700; color: #f8fafc;'>📋 Gerenciamento Geral de Amostras</span>
            <span style='color: #10b981; font-size: 13px; font-weight: 600;'>● Rede Criptografada Ativa</span>
        </div>
    """, unsafe_allow_html=True)
    
    df_dados = pd.read_sql_query("SELECT * FROM monitoramento ORDER BY id DESC", conn)
    total_amostras = len(df_dados)
    alertas_risco = len(df_dados[df_dados['nivel_risco'].str.contains("Alerta|Crítico|Alta", case=False, na=False)]) if total_amostras > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'<div class="metric-card"><div class="metric-title">Amostras Custodiadas</div><div class="metric-value">{total_amostras} <span style="font-size:14px; color:#64748b;">vials</span></div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card" style="border-left: 4px solid #ef4444;"><div class="metric-title" style="color: #ef4444;">Níveis de Risco / Alerta</div><div class="metric-value" style="color: #ef4444;">{alertas_risco} <span style="font-size:14px;">críticas</span></div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card" style="border-left: 4px solid #10b981;"><div class="metric-title">Analistas Ativos</div><div class="metric-value">{df_dados["analista"].nunique() if total_amostras > 0 else 0}</div></div>', unsafe_allow_html=True)
    
    st.write("")
    st.subheader("DataGrid do Ecossistema Criogênico", divider="blue")
    
    if total_amostras > 0:
        st.dataframe(df_dados, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma amostra localizada na infraestrutura local do banco SQLite.")

def render_cadastrar_amostra():
    st.markdown("""
        <div class='top-bar'>
            <span style='font-size: 20px; font-weight: 700; color: #f8fafc;'>➕ Adicionar Novo Registro Microbiológico</span>
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
            tipo_contaminante = st.text_input("Classificação do Contaminante:")

        btn_salvar = st.form_submit_button("💾 Salvar Registro no Banco de Dados")
        
        if btn_salvar:
            if not codigo or not起源:
                st.error("Campos Obrigatórios: Código de Barras ID e Origem devem ser preenchidos.")
            else:
                try:
                    cursor.execute("""
                        INSERT INTO monitoramento (codigo, origem, area, ponto_coleta, metodo, data_coleta, analista, contagem_ufc, nivel_risco, tipo_contaminante, status_acao)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Ativo')
                    """, (codigo, origem, area, ponto_coleta, metodo, data_coleta, analista, contagem_ufc, nivel_risco, tipo_contaminante))
                    conn.commit()
                    st.success("Cadastrado com sucesso!")
                    time.sleep(0.5)
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Esse Código já existe.")

def log_out_process():
    st.session_state["logado"] = False
    st.session_state["nome_usuario"] = ""
    st.rerun()

