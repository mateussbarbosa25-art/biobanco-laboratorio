import streamlit as st
import pandas as pd
import sqlite3
import io
import hashlib

st.set_page_config(page_title="Biobanco Restrito", layout="wide")

def crypto_pass(texto_senha):
    return hashlib.sha256(texto_senha.encode('utf-8')).hexdigest()

def db_start():
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
        resultado_final TEXT,
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
    if cursor.fetchone()[0] == 0:
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

if not st.session_state["logado"]:
    st.title("🔒 Login - Sistema de Biobanco")
    
    with st.form("formulario_login"):
        campo_usuario = st.text_input("Usuario:", placeholder="Ex: admin").strip()
        campo_senha = st.text_input("Senha:", type="password", placeholder="••••••••")
        botao_entrar = st.form_submit_button("Entrar no Sistema")
        
        if botao_entrar:
            hash_digitado = crypto_pass(campo_senha)
            cursor.execute("SELECT nome_completo FROM usuarios WHERE usuario = ? AND senha_hash = ?", (campo_usuario, hash_digitado))
            res_user = cursor.fetchone()
            
            if res_user:
                st.session_state["logado"] = True
                st.session_state["nome_usuario"] = res_user[0]
                st.success("Sucesso!")
                st.rerun()
            else:
                st.error("Credenciais incorretas.")
                
    st.info("💡 Usuario inicial: admin | Senha: lab123")
    st.stop()

st.title("🔬 Controle Interno de Biobanco")
st.sidebar.markdown(f"👤 **Analista:** {st.session_state['nome_usuario']}")

opcao = st.sidebar.radio("Navegacao:", [
    "📋 Consultar Amostras", 
    "📥 Importar CSV", 
    "➕ Cadastro Individual",
    "⚙️ Novo Analista",
    "🚪 Sair"
])

if opcao == "📋 Consultar Amostras":
    st.header("Historico de Monitoramento")
    busca = st.text_input("Pesquisar por Codigo (Ex: B4-001):").strip()
    
    if busca:
        df_busca = pd.read_sql_query("SELECT * FROM monitoramento WHERE codigo LIKE ?", conn, params=[f"%{busca}%"])
        if not df_busca.empty:
            st.dataframe(df_busca, use_container_width=True)
        else:
            st.warning("Nenhum registro encontrado.")
            
    st.subheader("Base Completa")
    df_todos = pd.read_sql_query("SELECT * FROM monitoramento", conn)
    st.dataframe(df_todos, use_container_width=True)

elif opcao == "📥 Importar CSV":
    st.header("Importador de Dados")
    arquivo_upload = st.file_uploader("Selecione o arquivo CSV:", type=["csv"])
    if arquivo_upload:
        try:
            conteudo = arquivo_upload.read().decode("utf-8")
            df_csv = pd.read_csv(io.StringIO(conteudo))
            linhas_inseridas = 0
            for _, linha in df_csv.iterrows():
                codigo_amostra = str(linha.get('CODE', '─')).strip()
                if codigo_amostra and codigo_amostra != 'nan' and codigo_amostra.startswith('B4-'):
                    try:
                        cursor.execute("INSERT INTO monitoramento (codigo, analista) VALUES (?, ?)", (codigo_amostra, st.session_state["nome_usuario"]))
                        linhas_inseridas += 1
                    except:
                        continue
            conn.commit()
            st.success(f"Pronto! {linhas_inseridas} amostras salvas.")
        except:
            st.error("Erro ao ler arquivo.")

elif opcao == "➕ Cadastro Individual":
    st.header("Registrar de Forma Individual")
    st.info(f"✍️ Vinculado ao analista: {st.session_state['nome_usuario']}")
    
    with st.form("form_cadastro_manual"):
        codigo = st.text_input("Codigo Absoluto (Ex: B4-040):").strip()
        origem = st.selectbox("Origem:", ["Environmental Monitoring", "Storage Tanks", "Processes"])
        area = st.text_input("Area / Setor:")
        ponto_coleta = st.text_input("Ponto de Coleta:")
        metodo = st.text_input("Metodo / Meio:")
        data_coleta = st.date_input("Data de Coleta").strftime("%Y%m%d")
        
        st.subheader("Morfologia")
        forma = st.selectbox("Forma:", ["N/A", "Punctiform", "Circular", "Irregular"])
        margem = st.selectbox("Margem:", ["N/A", "Round", "Wavy", "Lobulated"])
        pigmento = st.text_input("Cor da Colonia:")
        gram = st.selectbox("Gram:", ["N/A", "Gram-Positiva (+)", "Gram-Negativa (-)"])
        catalase = st.selectbox("Catalase:", ["N/A", "Positiva (+)", "Negativa (-)"])
        oxidase = st.selectbox("Oxidase:", ["N/A", "Positiva (+)", "Negativa (-)"])
        resultado_final = st.text_input("Laudo Final:")
            
        botao_cadastro = st.form_submit_button("Salvar no Sistema")
        if botao_cadastro:
            if not codigo:
                st.error("Codigo obrigatorio.")
            else:
                try:
                    cursor.execute('''
                    INSERT INTO monitoramento (
                        codigo, origem, area, ponto_coleta, metodo, data_coleta, analista, 
                        forma, margem, pigmento, coloracao_gram, catalase, oxidase, resultado_final
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        codigo, origem, area, ponto_coleta, metodo, data_coleta, st.session_state["nome_usuario"],
                        forma, margem, pigmento, gram, catalase, oxidase, resultado_final
                    ))
                    conn.commit()
                    st.success("Salvo com sucesso!")
                except:
                    st.error("Codigo duplicado.")

elif opcao == "⚙️ Novo Analista":
    st.header("Controle de Operadores")
    with st.form("cadastro_novo_usuario"):
        novo_user = st.text_input("Login do Analista:").strip()
        nome_real = st.text_input("Nome Completo:")
        nova_senha = st.text_input("Senha:", type="password")
        botao_usuario = st.form_submit_button("Criar Conta")
        
        if botao_usuario:
            if not novo_user or not nova_senha:
                st.error("Preencha os campos.")
            else:
                try:
                    hash_nova = crypto_pass(nova_senha)
                    cursor.execute("INSERT INTO usuarios (usuario, senha_hash, nome_completo) VALUES (?, ?, ?)", 
                                   (novo_user, hash_nova, nome_real))
                    conn.commit()
                    st.success("Conta criada!")
                except:
                    st.error("Usuario indisponivel.")

elif opcao == "🚪 Sair":
    st.session_state["logado"] = False
    st.session_state["nome_usuario"] = ""
    st.success("Desconectado.")
    st.rerun()

conn.close()
        
