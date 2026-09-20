import streamlit as st
import pandas as pd
import sqlite3
import io
import hashlib

# --- CONFIGURACAO GERAL DA PAGINA ---
st.set_page_config(page_title="LIMS Biobank Pro", page_icon="🔬", layout="wide")

# Estilizacao CSS Avançada - Estilo Zendo LIMS
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    div[data-testid="stSidebar"] { background-color: #0f172a !important; }
    div[data-testid="stSidebar"] .stMarkdown, div[data-testid="stSidebar"] label { color: #ffffff !important; }
    
    /* Top Bar Simulada */
    .top-bar {
        background-color: #ffffff; padding: 15px; border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05); margin-bottom: 20px;
        display: flex; justify-content: space-between; align-items: center;
    }
    
    /* Cards de Métricas Estilo LIMS */
    .metric-container { display: flex; gap: 15px; margin-bottom: 20px; flex-wrap: wrap; }
    .metric-card {
        background-color: white; border-left: 5px solid #1e40af; padding: 15px;
        border-radius: 6px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); min-width: 180px; flex: 1;
    }
    .metric-title { font-size: 11px; text-transform: uppercase; color: #64748b; font-weight: bold; }
    .metric-value { font-size: 22px; font-weight: 700; color: #1e293b; }
    
    /* Estilização de Botões e Filtros */
    .stButton>button {
        background-color: #2563eb; color: white; border-radius: 4px;
        padding: 6px 16px; border: none; font-weight: 600; font-size: 13px;
    }
    .stButton>button:hover { background-color: #1d4ed8; color: white; }
    div[data-testid="stForm"] { background-color: #ffffff; border-radius: 8px; padding: 15px; border: 1px solid #e2e8f0; }
    </style>
""", unsafe_allow_html=True)

def crypto_pass(texto_senha):
    return hashlib.sha256(texto_senha.encode('utf-8')).hexdigest()

def db_start():
    conn = sqlite3.connect('biobanco_laboratorio.db')
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS monitoramento (id INTEGER PRIMARY KEY AUTOINCREMENT, codigo TEXT UNIQUE NOT NULL, origem TEXT, area TEXT, ponto_coleta TEXT, metodo TEXT, data_coleta TEXT, analista TEXT, contagem_ufc INTEGER, nivel_risco TEXT, tipo_contaminante TEXT, identificacao_micro TEXT, status_acao TEXT, forma TEXT, margem TEXT, pigmento TEXT, coloracao_gram TEXT, catalase TEXT, oxidase TEXT, resultado_final TEXT)")
    
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

if "logado" not in st.session_state:
    st.session_state["logado"] = False
if "nome_usuario" not in st.session_state:
    st.session_state["nome_usuario"] = ""

# --- TELA DE LOGIN ---
if not st.session_state["logado"]:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
        <div style='text-align: center; margin-bottom: 20px;'>
            <h1 style='color: #2563eb; font-weight: 800; letter-spacing: -1px;'>🔬 LIMS BIOBANK</h1>
            <p style='color: #64748b; font-size: 14px;'>Sistema Avançado de Gestão Microbiológica</p>
        </div>
    """, unsafe_allow_html=True)
    
    campo_usuario = st.text_input("Usuário:", placeholder="Ex: admin", key="log_user").strip()
    campo_senha = st.text_input("Senha:", type="password", placeholder="••••••••", key="log_pass")
    botao_entrar = st.button("Entrar no Sistema")
    
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
    st.markdown("<p style='text-align: center; color: #94a3b8; font-size: 12px;'>Padrão: admin / lab133</p>", unsafe_allow_html=True)
    st.stop()

# =========================================================================
#  INTERFACE LOGADA - ESTILO ZENDO LIMS
# =========================================================================

st.sidebar.markdown(f"🔬 **Zendo Biobank**\n\n`Usuário: {st.session_state['nome_usuario']}`")
st.sidebar.markdown("---")

aba_selecionada = st.sidebar.radio(
    "📋 Módulos do Sistema",
    ["📦 Painel de Pedidos & Amostras", "➕ Cadastrar Nova Amostra"]
)

st.sidebar.markdown("---")
if st.sidebar.button("🚪 Encerrar Sessão", use_container_width=True):
    st.session_state["logado"] = False
    st.session_state["nome_usuario"] = ""
    st.rerun()

df_dados = pd.read_sql_query("SELECT * FROM monitoramento ORDER BY id DESC", conn)

# --- ABA 1: CONSOLE DE PEDIDOS ---
if aba_selecionada == "📦 Painel de Pedidos & Amostras":
    
    st.markdown("""
        <div class='top-bar'>
            <span style='font-size: 20px; font-weight: 700; color: #1e293b;'>📋 Gerenciamento Geral de Amostras</span>
            <span style='color: #64748b; font-size: 13px;'>Status: Online</span>
        </div>
    """, unsafe_allow_html=True)
    
    # Linhas corrigidas aqui:
    total_amostras = len(df_dados)
    alertas = len(df_dados[df_dados['nivel_risco'] == "Nivel de Alerta"]) if total_amostras > 0 else 0
    criticos = len(df_dados[df_dados['nivel_risco'] == "Nivel de Acao (Critico)"]) if total_amostras > 0 else 0
    
    st.markdown(f"""
        <div class='metric-container'>
            <div class='metric-card'><div class='metric-title'>Total de Pedidos</div><div class='metric-value'>{total_amostras}</div></div>
            <div class='metric-card' style='border-left-color: #eab308;'><div class='metric-title'>Em Alerta</div><div class='metric-value'>{alertas}</div></div>
            <div class='metric-card' style='border-left-color: #ef4444;'><div class='metric-title'>Críticos (Ação)</div><div class='metric-value'>{criticos}</div></div>
        </div>
    """, unsafe_allow_html=True)

    col_filtros, col_grid = st.columns([1, 3])
    
    with col_filtros:
        st.markdown("<p style='font-weight: 700; margin-bottom: 5px; color: #1e293b;'>🔍 Filtros de Busca</p>", unsafe_allow_html=True)
        with st.form("form_filtros"):
            filtro_codigo = st.text_input("Código da Amostra:")
            filtro_risco = st.selectbox("Nível de Risco:", ["Todos", "Nivel de Alerta", "Nivel de Acao (Critico)"])
            filtro_grupo = st.selectbox("Grupo Biológico:", ["Todos", "Bacteria", "Fungo Filamentoso (Bolor)", "Levedura"])
            aplicar_filtro = st.form_submit_button("Filtrar")
            
        df_filtrado = df_dados.copy()
        if filtro_codigo:
            df_filtrado = df_filtrado[df_filtrado['codigo'].str.contains(filtro_codigo, case=False)]
        if filtro_risco != "Todos":
            df_filtrado = df_filtrado[df_filtrado['nivel_risco'] == filtro_risco]
        if filtro_grupo != "Todos":
            df_filtrado = df_filtrado[df_filtrado['tipo_contaminante'] == filtro_grupo]

    with col_grid:
        st.markdown("<p style='font-weight: 700; margin-bottom: 5px; color: #1e293b;'>📊 Registros Localizados</p>", unsafe_allow_html=True)
        if not df_filtrado.empty:
            st.dataframe(df_filtrado, use_container_width=True, hide_index=True)
            
            csv_data = df_filtrado.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Exportar Seleção atual (CSV/Excel)",
                data=csv_data,
                file_name="lims_export.csv",
                mime="text/csv"
            )
        else:
            st.info("Nenhuma amostra corresponde aos critérios de filtragem selecionados.")

# --- ABA 2: FORMULÁRIO DE LANÇAMENTO ---
elif aba_selecionada == "➕ Cadastrar Nova Amostra":
    st.markdown("<h2 style='color: #2563eb;'>➕ Registro Técnico de Isolado</h2>", unsafe_allow_html=True)
    st.write("Insira as propriedades analíticas coletadas abaixo.")
    
    st.markdown("#### 📍 Informações de Rastreabilidade")
    codigo = st.text_input("Código Único da Amostra:", key="c_cod").strip()
    area = st.text_input("Setor de Coleta / Área:", key="c_are")
    ponto_coleta = st.text_input("Ponto Amostrado Específico:", key="c_pnt")
    metodo = st.text_input("Meio de Cultura / Método:", key="c_met")
    data_coleta = st.date_input("Data da Coleta", key="c_dat").strftime("%Y%m%d")
        
    st.markdown("<br>#### ☣ Análise Quantitativa e Biológica", unsafe_allow_html=True)
    contagem_ufc = st.number_input("Contagem Absoluta (UFC):", min_value=0, value=0, step=1, key="c_ufc")
    nivel_risco = st.selectbox("Classificação de Limite:", ["Nivel de Alerta", "Nivel de Acao (Critico)"], key="c_rsk")
    tipo_contaminante = st.selectbox("Grupo Biológico:", ["N/A", "Bacteria", "Fungo Filamentoso (Bolor)", "Levedura"], key="c_typ")
    
