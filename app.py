import streamlit as st
import pandas as pd
import sqlite3
import io
import hashlib

# --- CONFIGURACAO GERAL DA PAGINA ---
st.set_page_config(page_title="LIMS Biobank Pro", page_icon="🔬", layout="wide")

# Estilizacao CSS - Interface Premium Azul Classico
st.markdown("""
    <style>
    .main { background-color: #f4f6f9; }
    div[data-testid="stSidebar"] { background-color: #0e1e2f !important; }
    div[data-testid="stSidebar"] .stMarkdown, div[data-testid="stSidebar"] label { color: #ffffff !important; }
    .stButton>button {
        background-color: #1a73e8; color: white; border-radius: 6px;
        padding: 8px 20px; border: none; font-weight: 600; width: 100%;
    }
    .stButton>button:hover { background-color: #1557b0; color: white; }
    .card {
        background-color: white; padding: 20px; border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05); margin-bottom: 15px;
        border-top: 4px solid #1a73e8; text-align: center;
    }
    .card-title { color: #5f6368; font-size: 14px; font-weight: 600; text-transform: uppercase; margin-bottom: 5px; }
    .card-value { color: #202124; font-size: 26px; font-weight: bold; }
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
    if cursor.fetchone()[0] == 0:
        hash_adm = crypto_pass("lab123")
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
            <h1 style='color: #1a73e8; font-weight: 800;'>🔬 LIMS BIOBANK</h1>
            <p style='color: #5f6368; font-size: 14px;'>Controle de Monitoramento Microbiologico</p>
        </div>
    """, unsafe_allow_html=True)
    
    campo_usuario = st.text_input("Usuario:", placeholder="Ex: admin", key="log_user").strip()
    campo_senha = st.text_input("Senha:", type="password", placeholder="••••••••", key="log_pass")
    botao_entrar = st.button("Entrar no Sistema")
    
    if botao_entrar:
        hash_digitado = crypto_pass(campo_senha)
        cursor.execute("SELECT nome_completo FROM usuarios WHERE usuario = ? AND senha_hash = ?", (campo_usuario, hash_digitado))
        res_user = cursor.fetchone()
        if res_user:
            st.session_state["logado"] = True
            st.session_state["nome_usuario"] = res_user[0]
            st. those_are_fine = True
            st.rerun()
        else:
            st.error("Usuario ou senha incorretos.")
    st.markdown("<p style='text-align: center; color: #9aa0a6; font-size: 12px;'>Padrao: admin / lab123</p>", unsafe_allow_html=True)
    st.stop()

# =========================================================================
#  SISTEMA AUTENTICADO
# =========================================================================

st.sidebar.markdown("""
    <div style='text-align: center; padding: 10px 0; border-bottom: 1px solid #2c3e50;'>
        <h3 style='color: #ffffff; margin: 0; font-weight: 700;'>🧪 Biobank Pro</h3>
        <span style='color: #2cc770; font-size: 12px;'>● Servidor Online</span>
    </div>
    <br>
""", unsafe_allow_html=True)

st.sidebar.markdown(f"👤 **Analista:**\n`{st.session_state['nome_usuario']}`")

opcao = st.sidebar.radio("Navegacao:", [
    "📊 Dashboard & Consultas", "📥 Importar Planilha (CSV)", 
    "➕ Registrar Contaminacao", "👥 Gerenciar Analistas", "🚪 Sair"
])

# --- ABA 1: DASHBOARD & CONSULTAS ---
if opcao == "📊 Dashboard & Consultas":
    st.markdown("<h2 style='color: #1a73e8; font-weight: 700;'>📊 Painel de Controle Integrado</h2>", unsafe_allow_html=True)
    df_todos = pd.read_sql_query("SELECT * FROM monitoramento ORDER BY id DESC", conn)
    total_amostras = len(df_todos)
    
    criticos = 0
    em_analise = 0
    if total_amostras > 0:
        if 'nivel_risco' in df_todos.columns:
            criticos = len(df_todos[df_todos['nivel_risco'] == 'Nivel de Acao (Critico)'])
        if 'status_acao' in df_todos.columns:
            em_analise = len(df_todos[df_todos['status_acao'] == 'Em Investigacao'])
    
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(f"<div class='card'><div class='card-title'>Total de Amostras Retidas</div><div class='card-value'>🧬 {total_amostras}</div></div>", unsafe_allow_html=True)
    with m2:
        st.markdown(f"<div class='card'><div class='card-title'>Desvios Criticos</div><div class='card-value' style='color:#dc2626;'>🚨 {criticos}</div></div>", unsafe_allow_html=True)
    with m3:
        st.markdown(f"<div class='card'><div class='card-title'>Em Investigacao</div><div class='card-value' style='color:#f59e0b;'>⏳ {em_analise}</div></div>", unsafe_allow_html=True)
    
    if total_amostras > 0 and 'area' in df_todos.columns:
        df_valid_areas = df_todos[df_todos['area'].notna() & (df_todos['area'] != '')]
        if not df_valid_areas.empty:
            st.subheader("📈 Frequencia de Contaminacao por Area / Setor")
            st.bar_chart(df_valid_areas['area'].value_counts(), color="#1a73e8")
    
    st.markdown("<hr>", unsafe_allow_html=True)
    st.subheader("🔍 Localizador de Amostras")
    busca = st.text_input("Buscar por codigo:", placeholder="Digite o codigo da amostra contaminada (Ex: B4-001)...", key="search_box").strip()
    if busca:
        df_busca = pd.read_sql_query("SELECT * FROM monitoramento WHERE codigo LIKE ?", conn, params=[f"%{busca}%"])
        if not df_busca.empty:
            st.success("Registro localizado!")
            st.dataframe(df_busca, use_container_width=True, hide_index=True)
        else:
            st.warning("Nenhum dado encontrado para este codigo.")
            
    st.subheader("📋 Repositorio Central de Amostras Contaminadas")
    if total_amostras > 0:
        st.dataframe(df_todos, use_container_width=True, hide_index=True)
        csv_buffer = io.StringIO()
        df_todos.to_csv(csv_buffer, index=False)
        st.download_button(label="📥 Baixar Planilha Completa (Excel/CSV)", data=csv_buffer.getvalue(), file_name="relatorio_global_biobanco.csv", mime="text/csv")
    else:
        st.info("O banco de dados ainda nao possui registros cadastrados.")

# --- ABA 2: IMPORTAR CSV ---
elif opcao == "📥 Importar Planilha (CSV)":
    st.markdown("<h2 style='color: #1a73e8;'>📥 Upload de Planilha (.CSV)</h2>", unsafe_allow_html=True)
    arquivo_upload = st.file_uploader("Escolha o arquivo CSV:", type=["csv"])
    if arquivo_upload:
        try:
            conteudo = arquivo_upload.read().decode("utf-8")
            df_csv = pd.read_csv(io.StringIO(conteudo))
            linhas_inseridas = 0
            for index, linha in df_csv.iterrows():
                codigo_amostra = str(linha.get('CODE', 'nan')).strip()
                if codigo_amostra != 'nan' and codigo_amostra.startswith('B4-'):
                    area = str(linha.get('AREA', ''))
                    ponto_coleta = str(linha.get('COLLECTION POINT', ''))
                    metodo = str(linha.get('METHOD', ''))
                    data_coleta = str(linha.get('DATA', ''))
                    ufc = int(linha.get('RESULTADO FINAL', 0)) if str(linha.get('RESULTADO FINAL', '')).isdigit() else 0
                    risco = "Nivel de Alerta" if ufc < 5 else "Nivel de Acao (Critico)"
                    try:
                        cursor.execute("INSERT INTO monitoramento (codigo, area, ponto_coleta, metodo, data_coleta, contagem_ufc, nivel_risco, status_acao, analista) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (codigo_amostra, area, ponto_coleta, metodo, data_coleta, ufc, risco, "Em Investigacao", st.session_state["nome_usuario"]))
                        linhas_inseridas += 1
                    except:
                        pass
            conn.commit()
            st.success(f"Sucesso: {linhas_inseridas} registros novos importados.")
        except Exception as e:
            st.error(f"Erro no processamento: {e}")

# --- ABA 3: REGISTRAR CONTAMINACAO MANUAL ---
elif opcao == "➕ Registrar Contaminacao":
    
