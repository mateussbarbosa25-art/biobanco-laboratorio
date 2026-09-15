import streamlit as st
import pandas as pd
import sqlite3
import io

# Configuração da página web
st.set_page_config(page_title="Biobanco Digital - Laboratorio", layout="wide")
st.title("🔬 Sistema de Gestao do Biobanco")

# Conectando ou criando o banco de dados local
def conectar_banco():
    conn = sqlite3.connect('biobanco_laboratorio.db')
    cursor = conn.cursor()
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
    conn.commit()
    return conn, cursor

conn, cursor = conectar_banco()

# --- MENU LATERAL ---
opcao = st.sidebar.radio("Selecione uma Acao:", ["📋 Ver e Buscar Amostras", "📥 Importar Planilha CSV", "➕ Cadastrar Nova Amostra"])

# --- ABA 1: VER E BUSCAR AMOSTRAS ---
if opcao == "📋 Ver e Buscar Amostras":
    st.header("Consultar Historico de Monitoramento")
    busca = st.text_input("Digite o codigo da amostra para buscar (Ex: B4-001):")
    
    if busca:
        df_busca = pd.read_sql_query("SELECT * FROM monitoramento WHERE codigo LIKE ?", conn, params=[f"%{busca}%"])
        if not df_busca.empty:
            st.success("Amostra encontrada!")
            st.dataframe(df_busca)
        else:
            st.warning("Nenhuma amostra encontrada com este codigo.")
            
    st.subheader("Todos os Registros no Banco de Dados")
    df_todos = pd.read_sql_query("SELECT * FROM monitoramento", conn)
    if not df_todos.empty:
        st.dataframe(df_todos)
    else:
        st.info("O banco de dados esta vazio. Use as outras abas para adicionar dados.")

# --- ABA 2: IMPORTAR PLANILHA CSV ---
elif opcao == "📥 Importar Planilha CSV":
    st.header("Importacao Automatica da Planilha")
    arquivo_upload = st.file_uploader("Escolha o arquivo CSV da sua planilha:", type=["csv"])
    
    if arquivo_upload is not None:
        try:
            conteudo = arquivo_upload.read().decode("utf-8")
            f = io.StringIO(conteudo.strip())
            linhas_inseridas = 0
            lendo_dados_reais = False
            
            for linha in f:
                dados_linha = [item.strip() for item in linha.split(',')]
                if "CODE" in dados_linha:
                    lendo_dados_reais = True
                    continue
                if lendo_dados_reais and len(dados_linha) >= 12:
                    dados_limpos = [d for d in dados_linha if d != '']
                    if dados_limpos and dados_limpos.startswith('B4-'):
                        try:
                            cursor.execute('''
                            INSERT INTO monitoramento (codigo, origem, area, amostra, ponto_coleta, amostragem, metodo, frequencia, analista, data_coleta, resultado_final)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (dados_limpos, dados_linha, dados_linha, dados_linha, dados_linha, dados_linha, dados_linha, dados_linha, dados_linha, dados_linha, dados_linha))
                            linhas_inseridas += 1
                        except sqlite3.IntegrityError:
                            continue
            conn.commit()
            st.success(f"Sucesso! {linhas_inseridas} novas amostras cadastradas.")
        except Exception as e:
            st.error(f"Erro ao processar o arquivo: {e}")

# --- ABA 3: CADASTRAR NOVA AMOSTRA MANUAl ---
elif opcao == "➕ Cadastrar Nova Amostra":
    st.header("Formulario de Cadastro Manual")
    with st.form("form_cadastro"):
        col1, col2 = st.columns(2)
        with col1:
            codigo = st.text_input("Codigo (Ex: B4-040):")
            origem = st.selectbox("Origem:", ["Environmental Monitoring", "Storage Tanks", "Processes"])
            area = st.text_input("Area (Ex: Laboratory):")
            amostra = st.text_input("Sala / Tipo de Amostra:")
        with col2:
            ponto_coleta = st.text_input("Ponto de Coleta:")
            metodo = st.text_input("Metodo Utilizado:")
            analista = st.text_input("Analista Responsavel:")
            data_coleta = st.date_input("Data da Coleta:").strftime("%Y%m%d")
            
        botao_salvar = st.form_submit_button("Salvar Amostra no Biobanco")
        if botao_salvar:
            if not codigo:
                st.error("O campo 'Codigo' e obrigatorio!")
            else:
                try:
                    cursor.execute('''
                    INSERT INTO monitoramento (codigo, origem, area, amostra, ponto_coleta, metodo, analista, data_coleta)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (codigo, origem, area, amostra, ponto_coleta, metodo, analista, data_coleta))
                    conn.commit()
                    st.success(f"Amostra {codigo} cadastrada com sucesso!")
                except sqlite3.IntegrityError:
                    st.error(f"O codigo {codigo} ja esta cadastrado.")

conn.close()
            
