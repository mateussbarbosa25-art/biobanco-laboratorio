import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Biobanco - Controle de Biossegurança",
    page_icon="☣️",
    layout="wide"
)

# --- BASE DE DADOS SIMULADA (Utilizando o session_state para manter os dados vivos na tela) ---
if "biobanco" not in st.session_state:
    st.session_state.biobanco = pd.DataFrame([
        {"ID_Amostra": "BIO-001", "Tipo": "Soroteca", "Localização": "Freezer A - Reta 2 - Caixa 1", "Status": "Seguro", "Agente_Contaminante": "Nenhum", "Ultima_Modificacao": "2026-09-10 14:00"},
        {"ID_Amostra": "BIO-002", "Tipo": "Tecido Tumor", "Localização": "Ultrafreezer B - Reta 1 - Caixa 4", "Status": "☣️ CONTAMINADA", "Agente_Contaminante": "Micoplasma", "Ultima_Modificacao": "2026-09-18 09:30"},
        {"ID_Amostra": "BIO-003", "Tipo": "DNA Extraído", "Localização": "Nitrogênio Líquido Tanque 1", "Status": "Seguro", "Agente_Contaminante": "Nenhum", "Ultima_Modificacao": "2026-09-19 11:15"},
        {"ID_Amostra": "BIO-004", "Tipo": "Plasma", "Localização": "Freezer A - Reta 3 - Caixa 2", "Status": "☣️ CONTAMINADA", "Agente_Contaminante": "Influenza A", "Ultima_Modificacao": "2026-09-20 08:00"},
    ])

if "audit_trail" not in st.session_state:
    st.session_state.audit_trail = [
        {"Data/Hora": "2026-09-18 09:30", "ID": "BIO-002", "Ação": "Flag de contaminação por Micoplasma adicionada pelo Dr. Silva."},
        {"Data/Hora": "2026-09-20 08:00", "ID": "BIO-004", "Ação": "Amostra movida e classificada com risco biológico: Influenza A."},
    ]

# --- TÍTULO DO SISTEMA ---
st.title("☣️ LIMS Biobanco - Rastreabilidade de Amostras de Risco")
st.markdown("---")

# --- NAVEGAÇÃO LATERAL (SIDEBAR) ---
st.sidebar.header("Painel de Controle")
aba = st.sidebar.radio("Selecione a Ação:", ["📊 Dashboard Geral", "🔍 Rastrear Amostra / Código de Barras", "⚠️ Sinalizar Contaminação"])

# ==========================================
# ABA 1: DASHBOARD GERAL
# ==========================================
if aba == "📊 Dashboard Geral":
    st.subheader("Visão Geral do Inventário Criogênico")
    
    # Métricas rápidas
    total_amostras = len(st.session_state.biobanco)
    contaminadas = len(st.session_state.biobanco[st.session_state.biobanco["Status"] == "☣️ CONTAMINADA"])
    seguras = total_amostras - contaminadas
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Amostras Guardadas", total_amostras)
    col2.metric("Amostras em Quarentena/Risco", contaminadas, delta="Atenção necessária", delta_color="inverse")
    col3.metric("Amostras Livres/Seguras", seguras)
    
    st.markdown("### Banco de Dados Ativo")
    st.dataframe(st.session_state.biobanco, use_container_width=True)

# ==========================================
# ABA 2: RASTREAR AMOSTRA (SIMULAÇÃO DE BARCODE)
# ==========================================
elif aba == "🔍 Rastrear Amostra / Código de Barras":
    st.subheader("Consulta de Amostras por Identificador Único")
    st.write("Digite ou simule a leitura do Código de Barras (ex: BIO-002) abaixo:")
    
    id_busca = st.text_input("ID da Amostra / Barcode:", "").strip()
    
    if id_busca:
        df = st.session_state.biobanco
        resultado = df[df["ID_Amostra"] == id_busca]
        
        if not resultado.empty:
            amostra = resultado.iloc[0]
            st.success(f"Amostra Localizada com sucesso!")
            
            # Caixa de Alerta visual em caso de contaminação
            if "CONTAMINADA" in amostra["Status"]:
                st.error(f"⚠️ **ALERTA DE SEGURANÇA:** Esta amostra está marcada como **CONTAMINADA** por **{amostra['Agente_Contaminante']}**.")
            else:
                st.info("ℹ️ Status: Amostra limpa/segura para manipulação padrão.")
                
            # Dados de Localização e Cadeia de Custódia
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown(f"**Tipo de Amostra:** {amostra['Tipo']}")
                st.markdown(f"**Coordenada Criogênica Exata:** `{amostra['Localização']}`")
            with col_b:
                st.markdown(f"**Última Atualização no LIMS:** {amostra['Ultima_Modificacao']}")
        else:
            st.warning("Nenhuma amostra encontrada com este ID.")

# ==========================================
# ABA 3: SINALIZAR CONTAMINAÇÃO
# ==========================================
elif aba == "⚠️ Sinalizar Contaminação":
    st.subheader("Gatilho de Segurança: Sinalizar Contaminação")
    st.write("Use este formulário para isolar digitalmente uma amostra e alertar a equipe de biossegurança.")
    
    df = st.session_state.biobanco
    lista_ids = df["ID_Amostra"].tolist()
    
    id_selecionado = st.selectbox("Escolha o ID da Amostra afetada:", lista_ids)
    novo_contaminante = st.text_input("Identifique o Agente Contaminante encontrado (Ex: Micoplasma, E. coli, etc.):")
    responsavel = st.text_input("Nome do Operador/Pesquisador Responsável:")
    
    if st.button("🚨 Aplicar Flag de Contaminação e Bloquear Amostra"):
        if novo_contaminante and responsavel:
            # Atualiza o DataFrame principal
            idx = df[df["ID_Amostra"] == id_selecionado].index[0]
            
            st.session_state.biobanco.at[idx, "Status"] = "☣️ CONTAMINADA"
            st.session_state.biobanco.at[idx, "Agente_Contaminante"] = novo_contaminante
            agora = datetime.now().strftime("%Y-%m-%d %H:%M")
            st.session_state.biobanco.at[idx, "Ultima_Modificacao"] = agora
            
            # Alimenta a Trilha de Auditoria (Audit Trail) obrigatória pela ISO 20387
            nova_acao = f"Amostra sinalizada como CONTAMINADA ({novo_contaminante}) por {responsavel}."
            st.session_state.audit_trail.append({
                "Data/Hora": agora,
                "ID": id_selecionado,
                "Ação": nova_acao
            })
            
            st.success(f"Amostra {id_selecionado} bloqueada e marcada no sistema com sucesso!")
        else:
            st.error("Por favor, preencha o agente contaminante e o nome do responsável.")

# --- SEÇÃO INALTERÁVEL DE AUDIT TRAIL NO RODAPÉ ---
st.markdown("---")
st.subheader("📜 Rastro de Auditoria Imutável (Audit Trail - ISO 20387)")
st.table(st.session_state.audit_trail)
