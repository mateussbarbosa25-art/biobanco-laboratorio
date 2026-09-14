import sqlite3
import csv
import io

# 1. Conexão com o banco de dados
conn = sqlite3.connect('biobanco_laboratorio.db')
cursor = conn.cursor()

# 2. Criação da tabela estruturada conforme sua planilha
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
    margem TEXT
)
''')
conn.commit()

# 3. FUNÇÃO 1: Importar os dados da planilha automaticamente
def importar_planilha_csv(conteudo_csv):
    """
    Lê os dados brutos da planilha CSV e insere na tabela de monitoramento.
    Ignora linhas de cabeçalho e linhas vazias.
    """
    f = io.StringIO(conteudo_csv.strip())
    leitor = csv.reader(f)
    
    linhas_inseridas = 0
    lendo_dados_reais = False
    
    for linha in leitor:
        # Detecta onde começam os registros reais (abaixo do segundo cabeçalho)
        if len(linha) > 0 and linha[1] == 'CODE':
            lendo_dados_reais = True
            continue
            
        if lendo_dados_reais and len(linha) >= 13:
            codigo = linha[1].strip()
            # Valida se a linha realmente tem um código válido (Ex: B4-001)
            if codigo and codigo.startswith('B4-'):
                ponto = linha[2].strip()
                origem = linha[3].strip()
                area = linha[4].strip()
                amostra = linha[5].strip()
                ponto_coleta = linha[6].strip()
                amostragem = linha[7].strip()
                metodo = linha[8].strip()
                frequencia = linha[9].strip()
                analista = linha[10].strip()
                data_coleta = linha[11].strip()
                resultado = linha[12].strip()
                
                try:
                    cursor.execute('''
                    INSERT INTO monitoramento (
                        codigo, ponto, origem, area, amostra, ponto_coleta, 
                        amostragem, metodo, frequencia, analista, data_coleta, resultado_final
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (codigo, ponto, origem, area, amostra, ponto_coleta, amostragem, metodo, frequencia, analista, data_coleta, resultado))
                    linhas_inseridas += 1
                except sqlite3.IntegrityError:
                    # Se o código já existir, ele pula para não duplicar
                    continue
                    
    conn.commit()
    print(f"Sucesso: {linhas_inseridas} registros importados da planilha para o banco de dados!")

# 4. FUNÇÃO 2: Buscar histórico da amostra pelo Código
def buscar_amostra(codigo_busca):
    """
    Busca uma amostra no banco pelo código (Ex: B4-001) e exibe organizada na tela.
    """
    cursor.execute("SELECT * FROM monitoramento WHERE codigo = ?", (codigo_busca.strip(),))
    resultado = cursor.fetchone()
    
    if resultado:
        print(f"\n--- HISTÓRICO DA AMOSTRA: {codigo_busca} ---")
        print(f"ID no Banco: {resultado[0]}")
        print(f"Origem:      {resultado[3] if resultado[3] else 'Não informado'}")
        print(f"Área:        {resultado[4] if resultado[4] else 'Não informado'}")
        print(f"Sala/Amostra:{resultado[5] if resultado[5] else 'Não informado'}")
        print(f"Ponto Coleta:{resultado[6] if resultado[6] else 'Não informado'}")
        print(f"Método:      {resultado[8] if resultado[8] else 'Não informado'}")
        print(f"Frequência:  {resultado[9] if restriction := resultado[9] else 'Não informado'}")
        print(f"Analista:    {resultado[10] if resultado[10] else 'Não informado'}")
        print(f"Data Coleta: {resultado[11] if resultado[11] else 'Não informado'}")
        print(f"Resultado:   {resultado[12] if resultado[12] else 'Pendente/Análise'}")
        print("-" * 35)
    else:
        print(f"\nAmostra com o código '{codigo_busca}' não foi encontrada no sistema.")


# --- ÁREA DE TESTE AUTOMÁTICO ---
# Simulação dos dados textuais da sua planilha para alimentar o banco de dados
dados_sua_planilha = """
,CODE,PONTO,ORIGIN,AREA,SAMPLE,COLLECTION POINT,SAMPLING,METHOD,FREQUÊNCIA,ANALISTA,DATA,RESULTADO FINAL 
,B4-001,,Environmental Monitoring,Laboratory,Inoculation Room,Laminar Flow FLA001,Swab,Petrifilm AC,Mensal,Natalia,20260826,
,B4-002,,,,,,,,Mensal,Natalia,20260826,
,B4-035,,,,,,,,Semanal,,,
"""

# Executa a importação automática do texto acima
importar_planilha_csv(dados_sua_planilha)

# Executa uma busca de teste para ver o resultado estruturado
buscar_amostra("B4-001")

# Fecha o banco de dados
conn.close()
