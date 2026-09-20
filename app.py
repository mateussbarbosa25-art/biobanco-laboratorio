import streamlit as st
import pandas as pd
from datetime import datetime
import time

# --- CONFIGURAÇÃO DA PÁGINA (Interface Escura/Moderna por Padrão) ---
st.set_page_config(
    page_title="LIMS Biobank Nexus",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILIZAÇÃO CSS CUSTOMIZADA ---
st.markdown("""
<style>
    /* Estilização global para cartões modernos */
    .metric-card {
        background-color: #1e293b;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #334155;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .metric-title {
        color: #94a3b8;
        font-size: 0.875rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-value {
        color: #f8fafc;
        font-size: 1.875rem;
        font-weight: 700;
        margin-top: 4px;
    }
    .status-alert {
        background-color: #7f1d1d;
        border-left: 5px solid #ef4444;
        padding: 15px;
        border-radius: 4px;
        color: #fca5a5;
    }
</style>
""", unsafe_allow_html=True)

# --- ESTADO DA SESSÃO (PERSISTÊNCIA DE DADOS) ---
if "biobanco" not in st.session_state:
    st.session_state.biobanco = pd.DataFrame([
        {"ID_Amostra": "BIO-001", "Tipo": "Soroteca", "Localização": "Freezer A [R2-C1]", "Status": "✔ Seguro", "Agente_Contaminante": "Nenhum", "Ultima_Modificacao": "2026-09-10 14:00"},
        {"ID_Amostra": "BIO-002", "Tipo": "Tecido Tumor", "Localização": "Ultrafreezer B [R1-C4]", "Status": "☣ CONTAMINADA", "Agente_Contaminante": "Micoplasma", "Ultima_Modificacao": "2026-09-18 09:30"},
        {"ID_Amostra": "BIO-003", "Tipo": "DNA Extraído", "Localização": "Nitrogênio Tanque 1", "Status": "✔ Seguro", "Agente_Contaminante": "Nenhum", "Ultima_Modificacao": "2026-09-19 11:15"},
        {"ID_Amostra": "BIO-004", "Tipo": "Plasma", "Localização": "Freezer A [R3-C2]", "Status": "☣ CONTAMINADA", "Agente_Contaminante": "Influenza A", "Ultima_Modificacao": "2026-09-20 08:00"},
    ])

if "audit_trail" not in st.session_state:
    st.session_state.audit_trail = pd.DataFrame([
        {"Data/Hora": "2026-09-18 09:30", "ID": "BIO-002", "Ação": "Flag de contaminação por Micoplasma adicionada.", "Operador": "Dr. Silva"},
        {"Data/Hora": "2026-09-20 08:00", "ID": "BIO-004", "Ação": "Amostra movida e classificada com risco biológico.", "Operador": "Dra. Cristina"},
    ])

# --- FUNÇÕES DE PÁGINAS (Arquitetura Streamlit Moderna) ---
def render_dashboard():
    st.title("📊 Painel Analítico de Biossegurança")
    st.write("Monitoramento em tempo real do ecossistema criogênico.")
    
    # KPIs customizados em Grid Moderno
    total = len(st.session_state.biobanco)
    contaminadas = len(st.session_state.biobanco[st.session_state.biobanco["Status"] == "☣ CONTAMINADA"])
    seguras = total - contaminadas
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="metric-card"><div class="metric-title">Volume Total</div><div class="metric-value">{total} <span style="font-size:14px; color:#10b981;">amostras</span></div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card" style="border-color: #ef4444;"><div class="metric-title" style="color:#f87171;">Bio-Risco / Quarentena</div><div class="metric-value" style="color:#ef4444;">{contaminadas} <span style="font-size:14px;">críticas</span></div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="metric-card"><div class="metric-title">Integridade Limpa</div><div class="metric-value">{seguras} <span style="font-size:14px; color:#64748b;">vials</span></div></div>', unsafe_allow_html=True)
    
    st.subheader("Inventário Ativo de Amostras", divider="blue")
    
    # Filtro dinâmico na tabela superior
    status_filtro = st.segmented_control(
        "Filtrar visualização por status:",
        options=["Todas", "Seguro", "Contaminada"],
        default="Todas"
    )
    
    df_exibicao = st.session_state.biobanco.copy()
    if status_filtro == "Seguro":
        df_exibicao = df_exibicao[df_exibicao["Status"].str.contains("Seguro")]
    elif status_filtro == "Contaminada":
        df_exibicao = df_exibicao[df_exibicao["Status"].str.contains("CONTAMINADA")]
        
    st.dataframe(
        df_exibicao,
        use_container_width=True,
        hide_index=True,
        column_config={
            "ID_Amostra": st.column_config.TextColumn("Código de Barras ID", help="ID Único Identificador"),
            "Status": st.column_config.TextColumn("Status de Risco"),
            "Ultima_Modificacao": st.column_config.DatetimeColumn("Último Scan")
        }
    )

def render_rastreamento():
    st.title("🔍 Escaneamento & Cadeia de Custódia")
    st.write("Simulação de entrada por sensor ótico / barcode laser.")
    
    id_busca = st.text_input("📡 Aproxime o leitor ou digite o ID (Ex: BIO-002, BIO-001):", placeholder="Aguardando tag RFID / Barcode...")
    
    if id_busca:
        with st.spinner("Buscando na malha criogênica..."):
            time.sleep(0.4) # Simulação de lag de leitura real
            
        resultado = st.session_state.biobanco[st.session_state.biobanco["ID_Amostra"] == id_busca.strip()]
        
        if not resultado.empty:
            amostra = resultado.iloc[0]
            
            if "CONTAMINADA" in amostra["Status"]:
                st.markdown(f"""
                <div class="status-alert">
                    <strong>☣️ BLOQUEIO DE SEGURANÇA ATIVADO</strong><br>
                    Esta amostra está positivada para <strong>{amostra['Agente_Contaminante']}</strong>. 
                    Manipulação restrita a laboratórios NB3 (Nível de Biossegurança 3).
                </div>
                """, unsafe_allow_html=True)
                st.write("")
            else:
                st.pills("Status de Liberação", ["Amostra Segura ✔"], selection_mode="single", disabled=True)
            
            # Painel com Detalhes Clean
            col_left, col_right = st.columns(2)
            with col_left:
                st.info(f"**Tipo Biológico:** {amostra['Tipo']}")
                st.success(f"📍 **Endereço Físico:** {amostra['Localização']}")
            with col_right:
                st.metric(label="Último Checkpoint", value=amostra['Ultima_Modificacao'])
        else:
            st.error("Código de amostra não identificado na rede atual de biobancos.")

def render_sinalizacao():
    st.title("⚠️ Notificação de Risco Biológico")
    st.write("Isole digitalmente amostras comprometidas e dispare travas de auditoria.")
    
    with st.form("form_contaminacao", border=True):
        id_selecionado = st.selectbox("Selecione o ID do recipiente afetado:", st.session_state.biobanco["ID_Amostra"].tolist())
        novo_contaminante = st.text_input("Agente Patogênico Detectado:", placeholder="Ex: Mycoplasma hominis, HIV, Legionella")
        operador = st.text_input("Identificação do Operador (Matrícula/Nome):")
        
        enviar = st.form_submit_button("🚨 Gravar Flag de Contaminação e Notificar CIPA")
        
        if enviar:
            if novo_contaminante and operador:
                with st.status("Registrando nos nós de auditoria...", expanded=True) as status:
                    time.sleep(0.6)
                    
                    # Atualizando o DataFrame
                    idx = st.session_state.biobanco[st.session_state.biobanco["ID_Amostra"] == id_selecionado].index
                    st.session_state.biobanco.at[idx, "Status"] = "☣ CONTAMINADA"
                    st.session_state.biobanco.at[idx, "Agente_Contaminante"] = novo_contaminante
                    agora = datetime.now().strftime("%Y-%m-%d %H:%M")
                    st.session_state.biobanco.at[idx, "Ultima_Modificacao"] = agora
                    
                    # Atualizando Trilha de Auditoria
                    novo_log = pd.DataFrame([{"Data/Hora": agora, "ID": id_selecionado, "Ação": f"Contaminação por {novo_contaminante} reportada.", "Operador": operador}])
                    st.session_state.audit_trail = pd.concat([novo_log, st.session_state.audit_trail], ignore_index=True)
                    
                    status.update(label="Segurança Atualizada com Sucesso!", state="complete", expanded=False)
                st.toast(f"Amostra {id_selecionado} movida para isolamento digital.", icon="☣️")
            else:
                st.error("Todos os campos do formulário de risco são obrigatórios.")

# --- COMPONENTE DE NAVEGAÇÃO MODERNO (ST.NAVIGATION - LANÇAMENTO RECENTE) ---
paginas = {
    "NEXUS LIMS": [
        st.Page(render_dashboard, title="Dashboard Geral", icon="📊"),
        st.Page(render_rastreamento, title="Rastrear Código", icon="🔍"),
        st.Page(render_sinalizacao, title="Sinalizar Alerta", icon="⚠️"),
    ]
}

# Configuração da barra lateral nativa moderna
st.sidebar.markdown("<h3 style='color: #60a5fa;'>🧬 NEXUS BIOBANK</h3>", unsafe_allow_html=True)
st.sidebar.caption("Controle de Rastreabilidade v2.4")

# Executa o roteador de páginas
pg = st.navigation(paginas, position="sidebar")
pg.run()

# --- RODAPÉ DE AUDITORIA FIXO (Abaixo de todas as páginas) ---
st.markdown("---")
st.markdown("#### 📜 Trilha Inalterável de Auditoria (Audit Trail — Compliance ISO 20387)")
st.dataframe(st.session_state.audit_trail, use_container_width=True, hide_index=True)
