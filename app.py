else:
    st.sidebar.markdown("<h3 style='color: #60a5fa; margin-top: 10px;'>🔬 NEXUS LIMS</h3>", unsafe_allow_html=True)
    st.sidebar.caption(f"Operador: {st.session_state['nome_usuario']}")
    st.sidebar.markdown("---")
    
    modulo = st.sidebar.radio(
        "📋 Módulos do Sistema", 
        ["📦 Painel de Amostras", "➕ Cadastrar Nova Amostra"],
        index=0 if st.session_state["aba_atual"] == "📦 Painel de Amostras" else 1,
        key="navegacao_radio"
    )
    st.session_state["aba_atual"] = modulo

    # --- TOP BAR / LOGOUT ---
    st.markdown(f"""
        <div class='top-bar'>
            <span style='color: #f8fafc; font-weight: 700; font-size: 1.2rem;'>{st.session_state["aba_atual"]}</span>
            <span style='color: #94a3b8; font-size: 0.9rem;'>Nexus Edition V1.0</span>
        </div>
    """, unsafe_allow_html=True)
    
    if st.sidebar.button("🚪 Encerrar Sessão", use_container_width=True):
        st.session_state["logado"] = False
        st.session_state["nome_usuario"] = ""
        st.rerun()

    # =========================================================================
    #  MÓDULO: PAINEL DE AMOSTRAS
    # =========================================================================
    if st.session_state["aba_atual"] == "📦 Painel de Amostras":
        # Métricas em Linha
        df_metricas = pd.read_sql_query("SELECT nivel_risco FROM monitoramento", conn)
        total_amostras = len(df_metricas)
        criticas = len(df_metricas[df_metricas['nivel_risco'] == "Risco Crítico"])
        alertas = len(df_metricas[df_metricas['nivel_risco'] == "Nivel de Alerta"])
        
        m1, m2, m3 = st.columns(3)
        m1.markdown(f"<div class='metric-card'><div class='metric-title'>Total de Amostras</div><div class='metric-value'>{total_amostras}</div></div>", unsafe_allow_html=True)
        m2.markdown(f"<div class='metric-card'><div class='metric-title'>Status de Alerta</div><div class='metric-value' style='color: #f59e0b;'>{alertas}</div></div>", unsafe_allow_html=True)
        m3.markdown(f"<div class='metric-card'><div class='metric-title'>Risco Crítico (Contaminadas)</div><div class='metric-value' style='color: #ef4444;'>{criticas}</div></div>", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Tabela de Dados
        st.subheader("Histórico de Rastreabilidade")
        df_dados = pd.read_sql_query("SELECT id, codigo, origem, area, ponto_coleta, data_coleta, nivel_risco, status_acao FROM monitoramento ORDER BY id DESC", conn)
        
        if not df_dados.empty:
            st.dataframe(df_dados, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma amostra catalogada no biobanco até o momento.")

    # =========================================================================
    #  MÓDULO: CADASTRAR NOVA AMOSTRA
    # =========================================================================
    elif st.session_state["aba_atual"] == "➕ Cadastrar Nova Amostra":
        with st.form("cadastro_amostra_form"):
            c1, c2, c3 = st.columns(3)
            with c1:
                codigo = st.text_input("Código de Rastreabilidade (Barcode/ID):", placeholder="EX: BIO-2026-001").strip()
                origem = st.selectbox("Origem da Amostra:", OPCOES_ORIGEM)
                area = st.selectbox("Área do Laboratório:", OPCOES_AREA)
            with c2:
                ponto_coleta = st.selectbox("Ponto de Coleta Específico:", OPCOES_PONTO_COLETA)
                metodo = st.selectbox("Método de Análise:", OPCOES_METHOD)
                frequencia = st.selectbox("Frequência de Monitoramento:", OPCOES_FREQUENCIA)
            with c3:
                data_coleta = st.date_input("Data de Coleta:", datetime.now()).strftime("%Y-%m-%d")
                nivel_risco = st.selectbox("Classificação de Risco Biológico:", OPCOES_RISCO)
                status_acao = st.selectbox("Status Operacional:", ["Em Análise", "Liberado", "Quarentena / Bloqueado"])
            
            st.markdown("---")
            st.caption("🔬 Dados de Identificação Microbiológica (Opcional)")
            c4, c5 = st.columns(2)
            with c4:
                forma = st.selectbox("Forma da Colônia:", ["N/A"] + OPCOES_FORMA)
                margem = st.selectbox("Margem da Colônia:", ["N/A"] + OPCOES_MARGEM)
                tipo_contaminante = st.text_input("Tipo de Contaminante Suspeito:", placeholder="Ex: Bactéria Gram-Negativa")
            with c5:
                contagem_ufc = st.number_input("Contagem Absoluta (UFC):", min_value=0, step=1, value=0)
                resultado_final = st.text_area("Laudo Técnico Parcial / Resultado Final:", placeholder="Descreva os achados microscópicos...")

            st.markdown("<br>", unsafe_allow_html=True)
            salvar = st.form_submit_button("💾 Registrar e Criptografar na Nuvem", use_container_width=True)
            
            if salvar:
                if not codigo:
                    st.error("O código de rastreabilidade é obrigatório para garantir a cadeia de custódia.")
                else:
                    try:
                        cursor.execute("""
                            INSERT INTO monitoramento (
                                codigo, origem, area, ponto_coleta, metodo, data_coleta, analista, 
                                contagem_ufc, nivel_risco, tipo_contaminante, status_acao, forma, 
                                margem, resultado_final, frequencia
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            codigo, origem, area, ponto_coleta, metodo, data_coleta, st.session_state["nome_usuario"],
                            contagem_ufc, nivel_risco, tipo_contaminante, status_acao, forma, margem, resultado_final, frequencia
                        ))
                        conn.commit()
                        st.success(f"Amostra {codigo} registrada com sucesso e integrada à cadeia de custódia!")
                        time.sleep(1)
                        st.session_state["aba_atual"] = "📦 Painel de Amostras"
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error(f"Erro de Integridade: O código '{codigo}' já está cadastrado em nossa base.")
                        
