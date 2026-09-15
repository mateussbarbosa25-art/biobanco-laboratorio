import streamlit as st
import pandas as pd
import sqlite3
import io
import hashlib

# --- CONFIGURACAO BIOBANCO DE CONTAMINACAO ---
st.set_page_config(
    page_title="LIMS Biobank - Contamination Control", 
    page_icon="⚠️", 
    layout="wide"
)

# Estilizacao CSS - Identidade Visual de Biossegurança e Controle de Riscos
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    div[data-testid="stSidebar"] { background-color: #1e293b !important; }
    div[data-testid="stSidebar"] .stMarkdown, div[data-testid="stSidebar"] label { color: #ffffff !important; }
    .stButton>button {
        background-color: #dc2626;
        color: white;
        border-radius: 6px;
        padding: 8px 20px;
        border: none;
        font-weight: 600;
        width: 100%;
    }
    .stButton>button:hover { background-color: #991b1b; color: white; }
    .card-danger {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        margin-bottom: 15px;
        border-top: 4px solid #dc2626;
        text-align: center;
    }
    .card-title { color: #64748b; font-size: 13px; font-weight: 600; text-transform: uppercase; margin-bottom: 5px; }
    .card-value { color: #0f172a; font-size: 26px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

def crypto_pass(texto_senha):
    return hashlib.sha256(texto_senha.encode('utf-8')).hexdigest()

def db_start():
    conn = sqlite3.connect('biobanco_laboratorio.db')
    cursor = conn.cursor()
    cursor.execute('''
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
        oxidase TEXT
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT UNIQUE NOT NULL,
        senha_hash TEXT NOT NULL,
        nome_completo TEXT
    )
    ''')
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone() == 0:
        hash_adm = crypto_pass("lab123")
        cursor.execute("INSERT INTO usuarios (usuario, senha_hash, nome_completo) VALUES (?, ?, ?)", 
                       ("admin", hash_adm, "Administrador Geral"))
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
            <h1 style='color: #dc2626; font-weight: 800;'>⚠️ BIOBANK CONTAMINATION LOG</h1>
            <p style='color: #475569; font-size: 14px;'>Repositorio Restrito de Amostras e Isolas Contaminados</p>
        </div>
    """, unsafe_allow_html=True)
    
    campo_usuario = st.text_input("Usuario:", placeholder="Ex: admin", key="log_user").strip()
    campo_senha = st.text_input("Senha:", type="password", placeholder="••••••••", key="log_pass")
    botao_entrar = st.button("Autenticar no Servidor")
    
    if botao_entrar:
        hash_digitado = crypto_pass(campo_senha)
        cursor.execute("SELECT nome_completo FROM usuarios WHERE usuario = ? AND senha_hash = ?", (campo_usuario, hash_digitado))
        res_user = cursor.fetchone()
        
        if res_user:
            st.session_state["logado"] = True
            st.session_state["nome_usuario"] = res_user
            st.rerun()
        else:
            st.error("Acesso negado: Credenciais invalidas.")
            
    st.markdown("<p style='text-align: center; color: #94a3b8; font-size: 12px;'>Controle de Acesso: admin / lab123</p>", unsafe_allow_html=True)
    st.stop()

# =========================================================================
#  SISTEMA AUTENTICADO
# =========================================================================

st.sidebar.markdown("""
    <div style='text-align: center; padding: 10px 0; border-bottom: 1px solid #334155;'>
        <h3 style='color: #ffffff; margin: 0; font-weight: 700;'>☣️ LIMS Biobank</h3>
        <span style='color: #ef4444; font-size: 12px; font-weight: bold;'>● Monitoramento de Riscos</span>
    </div>
    <br>
""", unsafe_allow_html=True)

st.sidebar.markdown(f"👤 **Analista Fiscal:**\n`{st.session_state['nome_usuario']}`")

opcao = st.sidebar.radio("Navegacao:", [
    "📊 Painel de Ocorrencias", 
    "📥 Carga Batch de Planilha", 
    "➕ Registrar Contaminacao",
    "👥 Operadores Cadastrados",
    "🚪 Fechar Sessao"
])

# --- ABA 1: PAINEL DE OCORRENCIAS ---
if opcao == "📊 Painel de Ocorrencias":
    st.markdown("<h2 style='color: #dc2626; font-weight: 700;'>📊 Painel de Monitoramento de Contaminações</h2>", unsafe_allow_html=True)
    
    df_todos = pd.read_sql_query("SELECT * FROM monitoramento ORDER BY id DESC", conn)
    total_amostras = len(df_todos)
    
    # Calculo de Ocorrências Críticas (Nível de Ação Ultrapassado)
    criticos = len(df_todos[df_todos['nivel_risco'] == 'Nivel de Acao (Critico)']) if total_amostras > 0 else 0
    em_analise = len(df_todos[df_todos['status_acao'] == 'Em Investigacao']) if total_amostras > 0 else 0
    
    # Cards de Indicadores Visuais de Risco
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(f"<div class='card-danger'><div class='card-title'>Total de Isolas Retidos</div><div class='card-value'>🧫 {total_amostras}</div></div>", unsafe_allow_html=True)
    with m2:
        st.markdown(f"<div class='card-danger'><div class='card-title'>Desvios Criticos</div><div class='card-value' style='color:#dc2626;'>🚨 {criticos}</div></div>", unsafe_allow_html=True)
    with m3:
        st.markdown(f"<div class='card-danger'><div class='card-title'>Em Investigacao</div><div class='card-value' style='color:#f59e0b;'>⏳ {em_analise}</div></div>", unsafe_allow_html=True)
    
    # Grafico de Distribuição de Contaminantes por Setor
    if total_amostras > 0 and 'area' in df_todos.columns:
        df_valid = df_todos[df_todos['area'].notna() & (df_todos['area'] != '')]
        if not df_valid.empty:
            st.subheader("📈 Frequencia de Contaminacao por Setor / Area")
            st.bar_chart(df_valid['area'].value_counts(), color="#dc2626")
    
    st.markdown("<hr>", unsafe_allow_html=True)
    st.subheader("🔍 Localizador Rapido de Carga Microbiana")
    busca = st.text_input("", placeholder="Digite o codigo da amostra contaminada (Ex: B4-001)...", key="search_box").strip()
    
    if busca:
        df_busca = pd.read_sql_query("SELECT * FROM monitoramento WHERE codigo LIKE ?", conn, params=[f"%{busca}%"])
        if not df_busca.empty:
            st.success("Registro localizado na base de segurança!")
            st.dataframe(df_busca, use_container_width=True, hide_index=True)
        else:
            st.warning("Nenhum desvio encontrado para este codigo.")
            
    st.subheader("📋 Repositorio Central de Amostras Contaminadas")
    if total_amostras > 0:
        st.dataframe(df_todos, use_container_width=True, hide_index=True)
        
        csv_buffer = io.StringIO()
        df_todos.to_csv(csv_buffer, index=False)
        st.download_button(
            label="📥 Exportar Relatorio Geral de Desvios (CSV)",
            data=csv_buffer.getvalue(),
            file_name="relatorio_contaminacoes_biobanco.csv",
            mime="text/csv"
        )
    else:
        st.info("Nenhum desvio ou contaminacao registrado no banco de dados.")

# --- ABA 2: IMPORTAR CSV ---
elif opcao == "📥 Carga Batch de Planilha":
    st.markdown("<h2 style='color: #dc2626;'>📥 Importacao em Lote de Ocorrencias</h2>", unsafe_allow_html=True)
    
    arquivo_upload = st.file_uploader("Escolha a planilha consolidada (.CSV):", type=["csv"])
    if arquivo_upload:
        try:
            conteudo = arquivo_upload.read().decode("utf-8")
            df_csv = pd.read_csv(io.StringIO(conteudo))
            linhas_inseridas = 0
            
            for index, linha in df_csv.iterrows():
                codigo_amostra = str(linha.get('CODE', 'nan')).strip()
                area = str(linha.get('AREA', ''))
                ponto_coleta = str(linha.get('COLLECTION POINT', ''))
                metodo = str(linha.get('METHOD', ''))
                data_coleta = str(linha.get('DATA', ''))
                ufc = int(linha.get('RESULTADO FINAL', 0)) if str(linha.get('RESULTADO FINAL', '')).isdigit() else 0
                
                # Regra automatica de Risco baseada na presenca de UFC
                risco = "Nivel de Alerta" if ufc < 5 else "Nivel de Acao (Critico)"
                
                if codigo_amostra and codigo_amostra != 'nan' and codigo_amostra.startswith('B4-'):
                    try:
                        cursor.execute('''
                        INSERT INTO monitoramento (codigo, area, ponto_coleta, metodo, data_coleta, contagem_ufc, nivel_risco, status_acao, analista)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (codigo_amostra, area, ponto_coleta, metodo, data_coleta, ufc, risco, "Em Investigacao", st.session_state["nome_usuario"]))
                        linhas_inseridas += 1
                    except:
                        pass
            conn.commit()
            st.success(f"Processamento concluido: {linhas_inseridas} amostras de desvios importadas.")
        except Exception as e:
            st.error(f"Erro na leitura dos dados: {e}")

