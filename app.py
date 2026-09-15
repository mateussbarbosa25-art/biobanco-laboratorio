import streamlit as st
import pandas as pd
import sqlite3
import io
import hashlib

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Biobanco Restrito", layout="wide")

# --- FUNÇÕES DE SEGURANÇA E BANCO ---
def gerar_hash(senha):
    """Criptografa a senha para salvar no banco de dados com segurança."""
    return hashlib.sha256(senha.encode('utf-8')).hexdigest()

def inicializar_banco():
    """Cria as tabelas de dados e de usuários cadastrados se não existirem."""
    conn = sqlite3.connect('biobanco_laboratorio.db')
    cursor = conn.cursor()
    
    # Tabela de Amostras
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS monitoramento (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT UNIQUE NOT NULL,
        ponto TEXT,
        origem TEXT,
        area TEXT,
        amostra TEXT,
        ponto_coleta TEXT,
        amostragem TEXT,
        metodo TEXT,
        frequencia TEXT,
        analista TEXT,
        data_coleta TEXT,
        resultado_final TEXT
    )
    ''')
    
    # Tabela de Usuários (Login)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT UNIQUE NOT NULL,
        senha_hash TEXT NOT NULL,
        nome_completo TEXT
    )
    ''')
    
    # Cria o primeiro usuário administrador padrão caso a tabela esteja limpa
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        senha_padrao_hash = gerar_hash("lab123")
        cursor.execute("INSERT INTO usuarios (usuario, senha_hash, nome_completo) VALUES (?, ?, ?)", 
                       ("admin", senha_padrao_hash, "Administrador Geral"))
        
    conn.commit()
    return conn, cursor

def verificar_login(usuario, senha):
    """Valida se o usuário e a senha existem e batem com o banco de dados."""
    conn = sqlite3.connect('biobanco_laboratorio.db')
    cursor = conn.cursor()
    hash_senha = gerar_hash(senha)
    cursor.execute("SELECT nome_completo FROM usuarios WHERE usuario = ? AND senha_hash = ?", (usuario.strip(), hash_senha))
    resultado = cursor.fetchone()
    conn.close()
    return resultado[0] if resultado else None

# Inicializa as tabelas do sistema
conn, cursor = inicializar_banco()

# --- GERENCIAMENTO DE SESSÃO DO STREAMLIT ---
if "logado" not in st.session_state:
    st.session_state["logado"] = False
if "nome_usuario" not in st.session_state:
    st.session_state["nome_usuario"] = ""

# --- TELA DE LOGIN INTERFACES ---
if not st.session_state["logado"]:
    st.title("🔒 Login - Sistema de Biobanco")
    st.markdown("Insira suas credenciais cadastradas para acessar o painel de monitoramento do laboratório.")
    
    with st.form("formulario_login"):
        campo_usuario = st.text_input("Usuário:", placeholder="Ex: admin").strip()
        campo_senha = st.text_input("Senha:", type="password", placeholder="••••••••")
        botao_entrar = st.form_submit_button("Entrar no Sistema")
        
        if botao_entrar:
            nome_autenticado = verificar_login(campo_usuario, campo_senha)
            if nome_autenticado:
                st.session_state["logado"] = True
                st.session_state["nome_usuario"] = nome_autenticado
                st.success(f"Bem-vindo, {nome_autenticado}!")
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos. Verifique os dados inseridos.")
                
    st.info("💡 Acesso inicial? Utilize o usuário **admin** e a senha **lab123**. Altere logo após entrar.")
    st.stop()

# =========================================================================
#  A PARTIR DAQUI O USUÁRIO JÁ ESTÁ AUTENTICADO (SISTEMA LIBERADO)
# =========================================================================

# Cabeçalho do sistema logado
st.title("🔬 Controle Interno de Biobanco")
st.sidebar.markdown(f"👤 **Operador:** {st.session_state['nome_usuario']}")

# --- MENU DE NAVEGAÇÃO LATERAL ---
opcao = st.sidebar.radio("Navegação do Painel:", [
    "📋 Consultar e Buscar Amostras", 
    "📥 Upload de Planilha CSV", 
    "➕ Novo Cadastro Manual",
    "⚙️ Gerenciar Usuários",
    "🚪 Encerrar Sessão"
])

# Conexão ativa para as abas
conn = sqlite3.connect('biobanco_laboratorio.db')
cursor = conn.cursor()

# --- ABA 1: CONSULTAR E BUSCAR ---
if opcao == "📋 Consultar e Buscar Amostras":
    st.header("Histórico de Monitoramento Microbiológico")
    busca = st.text_input("Pesquisar por Código de Amostra (Ex: B4-001):").strip()
    
    if busca:
        df_busca = pd.read_sql_query("SELECT * FROM monitoramento WHERE codigo LIKE ?", conn, params=[f"%{busca}%"])
        if not df_busca.empty:
            st.success("Amostra localizada no sistema:")
            st.dataframe(df_busca, use_container_width=True)
        else:
            st.warning("Nenhum registro encontrado para este código.")
            
    st.subheader("Base de Dados Completa")
    df_todos = pd.read_sql_query("SELECT * FROM monitoramento", conn)
    if not df_todos.empty:
        st.dataframe(df_todos, use_container_width=True)
    else:
        st.info("O banco de dados está sem registros no momento.")

# --- ABA 2: UPLOAD CSV ---
elif opcao == "📥 Upload de Planilha CSV":
    st.header("Importador de Dados em Massa")
    st.markdown("Faça o upload do arquivo CSV estruturado do laboratório para processamento rápido.")
    
    arquivo_upload = st.file_uploader("Selecione o arquivo CSV:", type=["csv"])
    if arquivo_upload:
        try:
            conteudo = arquivo_upload.read().decode("utf-8")
            df_csv = pd.read_csv(io.StringIO(conteudo))
            
            linhas_inseridas = 0
            for _, linha in df_csv.iterrows():
                codigo_amostra = str(linha.get('CODE', linha.iloc[0])).strip()
                if codigo_amostra and codigo_amostra != 'nan' and codigo_amostra.startswith('B4-'):
                    try:
                        cursor.execute("INSERT INTO monitoramento (codigo) VALUES (?)", (codigo_amostra,))
                        linhas_inseridas += 1
                    except sqlite3.IntegrityError:
                        continue
            conn.commit()
            st.success(f"Processamento concluído: {linhas_inseridas} novas amostras salvas.")
        except Exception as e:
            st.error(f"Erro ao analisar o arquivo fornecido: {e}")

# --- ABA 3: CADASTRO MANUAL ---
elif opcao == "➕ Novo Cadastro Manual":
    st.header("Registrar Amostra de Forma Individual")
    with st.form("form_cadastro_manual"):
        col1, col2 = st.columns(2)
        with col1:
            codigo = st.text_input("Código Absoluto (Ex: B4-040):").strip()
            origem = st.selectbox("Origem do Monitoramento:", ["Environmental Monitoring", "Storage Tanks", "Processes"])
            area = st.text_input("Área de Coleta:")
        with col2:
            ponto_coleta = st.text_input("Ponto Crítico de Controle:")
            metodo = st.text_input("Método de Cultivo:")
            data_coleta = st.date_input("Data de Coleta").strftime("%Y%m%d")
            
        botao_cadastro = st.form_submit_button("Registrar no Sistema")
        if botao_cadastro:
            if not codigo:
                st.error("O preenchimento do campo 'Código' é obrigatório para indexação.")
            else:
                try:
                    cursor.execute('''
                    INSERT INTO monitoramento (codigo, origem, area, ponto_coleta, metodo, data_coleta, analista)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (codigo, origem, area, ponto_coleta, metodo, data_coleta, st.session_state["nome_usuario"]))
                    conn.commit()
                    st.success(f"Amostra {codigo} integrada com sucesso ao biobanco!")
                except sqlite3.IntegrityError:
                    st.error("Falha: Este código de amostra já consta no sistema.")

# --- ABA 4: GERENCIAR USUÁRIOS ---
elif opcao == "⚙️ Gerenciar Usuários":
    st.header("Controle de Operadores e Analistas")
    st.markdown("Cadastre novos profissionais para que eles possam acessar o sistema com logins individuais.")
    
    with st.form("cadastro_novo_usuario"):
        st.subheader("Cadastrar Novo Usuário")
        novo_user = st.text_input("Nome de Usuário (Login):", placeholder="Ex: natalia.silva").strip()
        nome_real = st.text_input("Nome Completo do Profissional:", placeholder="Ex: Natália Silva")
        nova_senha = st.text_input("Senha de Acesso:", type="password")
        botao_usuario = st.form_submit_button("Criar Conta")
        
        if botao_usuario:
            if not novo_user or not nova_senha:
                st.error("Campos de usuário e senha não podem ficar vazios.")
            else:
                try:
                    hash_nova = gerar_hash(nova_senha)
                    cursor.execute("INSERT INTO usuarios (usuario, senha_hash, nome_completo) VALUES (?, ?, ?)", 
                                   (novo_user, hash_nova, nome_real))
                    conn.commit()
                    st.success(f"Conta para o operador '{nome_real}' ativada com sucesso!")
                except sqlite3.IntegrityError:
                    st.error("Este nome de usuário já está em uso por outro profissional.")

# --- ABA 5: ENCERRAR SESSÃO ---
elif opcao == "🚪 Encerrar Sessão":
    st.session_state["logado"] = False
    st.session_state["nome_usuario"] = ""
    st.success("Sessão finalizada com segurança!")
    st.rerun()

conn.close()
                
