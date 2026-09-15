import streamlit as st
import pandas as pd
import sqlite3
import io
import hashlib

# --- CONFIGURACAO GERAL DA PAGINA ---
st.set_page_config(page_title="LIMS Biobank Pro", page_icon="🔬", layout="wide")

# Estilizacao CSS para deixar a interface limpa e profissional no celular
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
    if cursor.fetchone() == 0:
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
            st.session_state["nome_usuario"] = res_user
            st.rerun()
        else:
            st.error("Usuario ou senha incorretos.")
    st.markdown("<p style='text-align: center; color: #9aa0a6; font-size: 12px;'>Padrao: admin / lab123</p>", unsafe_allow_html=True)
    st.stop()

# =========================================================================
#  SISTEMA FIXO (SEM COMPLICACAO NO CELULAR)
# =========================================================================

st.sidebar.markdown("👤 **Analista Ativo:**\n`" + str(st.session_state['nome_usuario']) + "`")
if st.sidebar.button("🚪 Sair do Sistema"):
    st.session_state["logado"] = False
    st.session_state["nome_usuario"] = ""
    st.rerun()

# --- TELA UNICA PRINCIPAL ---
st.markdown("<h2 style='color: #1a73e8;'>➕ Lancamento de Amostra Contaminada</h2>", unsafe_allow_html=True)
st.write("Preencha as informacoes abaixo para registrar o isolado no biobanco.")

st.markdown("#### 📍 Dados Básicos da Coleta")
codigo = st.text_input("Codigo Unico (Ex: B4-040):", key="c_cod").strip()
area = st.text_input("Area / Setor da Ocorrencia:", key="c_are")
ponto_coleta = st.text_input("Ponto de Coleta Amostrado:", key="c_pnt")
metodo = st.text_input("Metodo Analitico / Meio:", key="c_met")
data_coleta = st.date_input("Data da Coleta", key="c_dat").strftime("%Y%m%d")
    
st.markdown("<br>#### ☣ Quantificacao e Classificacao da Carga Microbiana", unsafe_allow_html=True)
contagem_ufc = st.number_input("Contagem Absoluta de UFC (Colonias):", min_value=0, value=0, step=1, key="c_ufc")
nivel_risco = st.selectbox("Classificacao do Limite:", ["Nivel de Alerta", "Nivel de Acao (Critico)"], key="c_rsk")
tipo_contaminante = st.selectbox("Grupo Biologico:", ["N/A", "Bacteria", "Fungo Filamentoso (Bolor)", "Levedura"], key="c_typ")
identificacao_micro = st.text_input("Identificacao Taxonomica / Genero (Se houver):", key="c_mic")
status_acao = st.selectbox("Status da Acao Corretiva:", ["Em Investigacao", "Acao Concluida (Sanitizacao)", "Lote Descartado"], key="c_stt")

st.markdown("<br>#### 🧫 Avaliacao de Morfologia Microbiologica", unsafe_allow_html=True)
forma = st.selectbox("Forma da Colonia:", ["N/A", "Punctiform", "Circular", "Irregular"], key="c_for")
margem = st.selectbox("Margem da Colonia:", ["N/A", "Round", "Wavy", "Lobulated"], key="c_mar")
pigmento = st.text_input("Pigmentacao / Cor:", key="c_pig")
gram = st.selectbox("Classificacao Gram:", ["N/A", "Gram-Positiva (+)", "Gram-Negativa (-)"], key="c_grm")
catalase = st.selectbox("Catalase:", ["N/A", "Positiva (+)", "Negativa (-)"], key="c_cat")
oxidase = st.selectbox("Oxidase:", ["N/A", "Positiva (+)", "Negativa (-)"], key="c_oxi")
resultado_final = st.text_input("Conclusao / Resultado Final:", key="c_res")

st.markdown("<br>", unsafe_allow_html=True)
botao_cadastro = st.button("Salvar no Biobanco")

if botao_cadastro:
    if not codigo:
        st.error("O campo 'Codigo Unico' e estritamente obrigatorio.")
    else:
        try:
            cursor.execute("INSERT INTO monitoramento (codigo, area, ponto_coleta, metodo, data_coleta, analista, contagem_ufc, nivel_risco, tipo_contaminante, identificacao_micro, status_acao, forma, margem, pigmento, coloracao_gram, catalase, oxidase, resultado_final) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (codigo, area, ponto_coleta, metodo, data_coleta, str(st.session_state["nome_usuario"]), contagem_ufc, nivel_risco, tipo_contaminante, identificacao_micro, status_acao, forma, margem, pigmento, gram, catalase, oxidase, resultado_final))
            conn.commit()
            st.success(f"Amostra {codigo} salva com sucesso!")
        except Exception as e:
            st.error("Erro: Este codigo ja existe na base de dados.")

st.markdown("<hr><h3 style='color: #1a73e8;'>📊 Banco de Dados Atual</h3>", unsafe_allow_html=True)
df_todos = pd.read_sql_query("SELECT * FROM monitoramento ORDER BY id DESC", conn)
if not df_todos.empty:
    st.dataframe(df_todos, use_container_width=True, hide_index=True)
else:
    st.info("Nenhuma amostra cadastrada ainda.")

conn.close()
