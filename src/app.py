import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go 
from pathlib import Path

# ==================================================
# 1. CONFIGURAÇÃO E CSS (MANTIDO INTEGRALMENTE)
# ==================================================
st.set_page_config(
    page_title="Controle de Bombonas",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
        .block-container {padding-top: 1rem;}
        div[data-testid="metric-container"] {
            background-color: #FFFFFF;
            border: 1px solid #E0E0E0;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        [data-testid="stMetricValue"] {
            font-size: 55px !important;
            font-weight: 900 !important;
            color: #1f618d !important;
        }
        [data-testid="stMetricLabel"] {
            font-size: 26px !important;
            font-weight: 800 !important;
            color: #333333 !important;
        }
        h1, h2, h3 {
            font-family: 'Arial Black' !important;
            font-size: 32px !important;
            font-weight: 900 !important;
        }
        .stButton > button {
            width: 100%;
            border-radius: 8px;
            height: 3em;
            font-weight: 700;
            font-size: 18px;
            border: 1px solid #d1d1d1;
        }
    </style>
""", unsafe_allow_html=True)

# ==================================================
# 2. GERENCIAMENTO DE ESTADO
# ==================================================
if 'pagina_atual' not in st.session_state:
    st.session_state.pagina_atual = 'Home'

def ir_para(pagina):
    st.session_state.pagina_atual = pagina

# ==================================================
# 3. CARREGAMENTO E AUXILIARES
# ==================================================
MESES_PT = {
    1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 
    5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto', 
    9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
}

MESES_ABREV = {
    1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr',
    5: 'Mai', 6: 'Jun', 7: 'Jul', 8: 'Ago',
    9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
}

def formata_mes_grafico(x):
    try:
        if pd.isna(x): return "Data Inválida"
        # Pega a abreviação (Jan, Fev...) e o ano curto (25, 26...)
        mes_abrev = MESES_ABREV[x.month]
        ano_curto = str(x.year)[-2:]
        return f"{mes_abrev}.{ano_curto}"
    except:
        return f"{x.month}/{x.year}"

def formata_mes_abrev_ano(x):
    try:
        if pd.isna(x): return ""
        ano_curto = str(x.year)[-2:]
        return f"{MESES_ABREV[x.month]}.{ano_curto}"
    except:
        return ""

def aplicar_estilo_grafico(fig):
    # 1. Ajuste manual de escala para dar teto ao gráfico
    try:
        valores = []
        for trace in fig.data:
            if 'y' in trace and trace.y is not None:
                valores.extend([v for v in trace.y if v is not None])
        
        if valores:
            max_y = max(valores)
            # Dá 25% de folga no topo para o número não sumir
            fig.update_yaxes(range=[0, max_y * 1.25])
    except:
        pass

    # 2. Configurações de Layout
    fig.update_layout(
        separators=",.", 
        font=dict(family="Arial Black", size=14, color="black"),
        title_font=dict(size=24, family="Arial Black", color="#1f618d"),
        xaxis=dict(tickfont=dict(size=14, family="Arial Black"), automargin=True),
        yaxis=dict(tickfont=dict(size=14, family="Arial Black"), automargin=True),
        margin=dict(t=100, b=50, l=50, r=50),
        legend=dict(font=dict(size=12, family="Arial Black")),
        autosize=True
    )
    
    # 3. Regra de Ouro: Diferencia Barra de Linha
    for trace in fig.data:
        # Se for gráfico de BARRA, coloca OUTSIDE
        if trace.type == 'bar':
            trace.update(textposition='outside', cliponaxis=False)
        # Se for gráfico de LINHA (scatter), coloca TOP CENTER
        else:
            trace.update(textposition='top center', cliponaxis=False)
            
        trace.update(
            texttemplate='<b>%{text:,.0f}</b>', 
            textfont=dict(size=18, family="Arial Black")
        )
    return fig

BASE_DIR = Path(__file__).resolve().parent.parent
ARQUIVO_DADOS = BASE_DIR / "dados" / "bombonas_v2.csv"

@st.cache_data
def carregar_dados_v2():
    caminho = ARQUIVO_DADOS
    if not caminho.exists():
        caminho = Path("dados/bombonas_v2.csv")
    if not caminho.exists(): return None

    try:
        df = pd.read_csv(caminho)
        df.columns = df.columns.str.strip().str.lower()
        df["data"] = pd.to_datetime(df["data"])
        df["ano"] = df["data"].dt.year
        df["mes_nome"] = df["data"].dt.month.map(MESES_PT)
        
        # NOVA COLUNA PARA O FILTRO SOLICITADO
        df["mes_ano_ref"] = df["data"].apply(formata_mes_abrev_ano)

        if "local" in df.columns: df["local"] = df["local"].astype(str).str.strip().str.upper()
        if "grupo" in df.columns: 
            df["grupo"] = df["grupo"].astype(str).str.strip().str.upper()
            df = df[~df["grupo"].isin(["UM", "NAN", "NONE"])]

        df['mes_grafico'] = df['data'].apply(formata_mes_grafico)
        return df
    except Exception as e: st.error(f"Erro: {e}"); return None

df = carregar_dados_v2()

if df is None or df.empty:
    st.warning("⚠️ Dados não encontrados.")
    st.stop()

# ==================================================
# 4. BARRA LATERAL (COM NOVO FILTRO)
# ==================================================
with st.sidebar:
    if st.session_state.pagina_atual != 'Home':
        if st.button("🏠 Voltar ao Início", width='stretch'):
            ir_para("Home")
            st.rerun()
        st.markdown("---")

    with st.expander("⚙️ Configurações / Simulador", expanded=False):
        st.caption("Ajuste os valores para simular cenários:")
        META_PESO = st.number_input("Meta Peso (kg)", value=25.0, step=0.5)
        PRECO_BASE = st.number_input("Preço Base (R$)", value=95.95, step=1.0)
        PRECO_ESTIMADO = st.number_input("Preço Estimado (R$)", value=101.00, step=1.0)
    
    st.markdown("---")
    st.header("🔍 Filtros")
    
    # 1. Filtro Novo: Mês e Ano (Ex: Jan.25)
    # Ordenado por data para não ficar bagunçado
    opcoes_mes_ano = df.sort_values("data")["mes_ano_ref"].unique().tolist()
    filtro_mes_ano = st.multiselect("📅 Mês/Ano (Ex: Jan.25)", options=opcoes_mes_ano)

    # 2. Filtros Originais (mantidos por precaução)
    opcoes_ano = sorted(df["ano"].unique().tolist(), reverse=True)
    filtro_ano = st.multiselect("📅 Ano (Simples)", options=opcoes_ano)
    
    df_temp = df.copy()
    if filtro_mes_ano:
        df_temp = df_temp[df_temp["mes_ano_ref"].isin(filtro_mes_ano)]
    if filtro_ano:
        df_temp = df_temp[df_temp["ano"].isin(filtro_ano)]

    ordem_meses = [MESES_PT[i] for i in range(1, 13)]
    meses_disponiveis = [m for m in ordem_meses if m in df_temp["mes_nome"].unique()]
    filtro_mes = st.multiselect("🗓️ Mês (Simples)", options=meses_disponiveis)

    opcoes_local = sorted(df_temp["local"].unique().tolist())
    filtro_local = st.multiselect("📍 Local", options=opcoes_local)

    opcoes_grupo = sorted(df_temp["grupo"].unique().tolist())
    filtro_grupo = st.multiselect("📦 Grupo", options=opcoes_grupo)

# Aplicação final dos filtros
df_filtrado = df_temp.copy()
if filtro_local: df_filtrado = df_filtrado[df_filtrado["local"].isin(filtro_local)]
if filtro_grupo: df_filtrado = df_filtrado[df_filtrado["grupo"].isin(filtro_grupo)]
if filtro_mes: df_filtrado = df_filtrado[df_filtrado["mes_nome"].isin(filtro_mes)]

if df_filtrado.empty:
    st.info("Nenhum dado encontrado.")
    st.stop()

# Cálculos Gerais
total_bombonas = df_filtrado["bombonas"].sum()
total_peso_real = df_filtrado["peso"].sum()
peso_ideal_total = total_bombonas * META_PESO 
diferenca_peso = total_peso_real - peso_ideal_total
gasto_estimado = total_bombonas * PRECO_ESTIMADO

# ==================================================
# 5. PÁGINAS DO SISTEMA (MANTIDAS INTEGRALMENTE)
# ==================================================

# --- HOME ---
if st.session_state.pagina_atual == 'Home':
    st.title("♻️ Painel Analise de Bombonas")
    st.markdown(f"**Cenário Atual:** Meta {int(META_PESO)}kg | Custo Est. R$ {int(PRECO_ESTIMADO)}")
    st.markdown("---")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("TOTAL PESO", f"{int(total_peso_real):,.0f}".replace(",", "."), delta=None)
        if st.button("Acessar Peso", key="btn_peso"): ir_para("Peso"); st.rerun()
    with c2:
        st.metric("UNIDADES", f"{int(total_bombonas)}")
        if st.button("Acessar Bombonas", key="btn_bomb"): ir_para("Bombonas"); st.rerun()
    with c3:
        st.metric("GASTO ESTIMADO", f"R$ {int(gasto_estimado):,.0f}".replace(",", "."))
        if st.button("Acessar Financeiro", key="btn_fin"): ir_para("Financeiro"); st.rerun()

    st.markdown("---")
    st.subheader("📊 Visão Geral")
    resumo = df_filtrado.groupby(pd.Grouper(key="data", freq="ME"))["bombonas"].sum().reset_index()
    resumo = resumo[resumo["bombonas"] > 0]
    resumo["mes_str"] = resumo["data"].apply(formata_mes_grafico)
    
    fig = px.bar(resumo, x="mes_str", y="bombonas", text="bombonas", title="TOTAL DE BOMBONAS POR MÊS")
    st.plotly_chart(aplicar_estilo_grafico(fig), use_container_width=True)


# --- PESO ---
elif st.session_state.pagina_atual == 'Peso':
    st.title("⚖️ Análise de Peso")
    st.markdown("---")

    k1, k2, k3 = st.columns(3)
    k1.metric("PESO REAL", f"{int(total_peso_real):,.0f}".replace(",", "."))
    k2.metric(f"META ({int(META_PESO)}KG)", f"{int(peso_ideal_total):,.0f}".replace(",", "."))
    k3.metric("DIFERENÇA", f"{int(diferenca_peso):,.0f}".replace(",", "."), delta_color="inverse")

    st.markdown("---")
    df_p_m_n = df_filtrado.groupby(pd.Grouper(key="data", freq="ME"))["peso"].sum().reset_index().sort_values("data")
    df_p_m_n = df_p_m_n[df_p_m_n["peso"] > 0]
    df_p_m_n["mes_fmt"] = df_p_m_n["data"].apply(formata_mes_abrev_ano)
    media_p_ref = int(df_p_m_n["peso"].mean())

    fig_p_n = go.Figure()
    fig_p_n.add_trace(go.Scatter(x=df_p_m_n["mes_fmt"], y=df_p_m_n["peso"], mode='lines+markers+text', name='Real', line=dict(color='#1f618d', width=4), text=df_p_m_n["peso"]))
    fig_p_n.add_trace(go.Scatter(x=df_p_m_n["mes_fmt"], y=[media_p_ref]*len(df_p_m_n), mode='lines', name=f'Média: {media_p_ref:,.0f}'.replace(",", "."), line=dict(color='orange', width=3, dash='dash')))
    fig_p_n.update_layout(title="TOTAL PESO MÊS (Comparativo Real vs Média)")
    st.plotly_chart(aplicar_estilo_grafico(fig_p_n), use_container_width=True)

    st.markdown("---")
    st.subheader("Comparativo Mensal (Real vs Meta)")
    mensal = df_filtrado.groupby(pd.Grouper(key="data", freq="ME")).agg(peso_real=("peso", "sum"), qtd=("bombonas", "sum")).reset_index().sort_values("data")
    mensal = mensal[mensal["peso_real"] > 0]
    mensal["peso_ideal"] = mensal["qtd"] * META_PESO
    mensal["mes_str"] = mensal["data"].apply(formata_mes_grafico)
    
    fig_p = go.Figure()
    fig_p.add_trace(go.Scatter(
        x=mensal["mes_str"], y=mensal["peso_real"], 
        mode='lines+markers+text', name='Real', text=mensal["peso_real"],
        textposition="top center",
        line=dict(color='#1f618d', width=4)
    ))
    fig_p.add_trace(go.Scatter(
        x=mensal["mes_str"], y=mensal["peso_ideal"], 
        mode='lines+markers+text', name='Meta', text=mensal["peso_ideal"],
        textposition="bottom center",
        line=dict(color='red', width=4)
    ))
    fig_p.update_layout(title="PESO REAL VS PESO META (MENSAL)")
    st.plotly_chart(aplicar_estilo_grafico(fig_p), use_container_width=True)

    st.markdown("---")
    st.subheader("🔎 Detalhamento dos Indicadores")
    df_p_a = df_filtrado.groupby(pd.Grouper(key="data", freq="ME")).agg(tp=("peso", "sum"), tb=("bombonas", "sum"), d=("data", "nunique")).reset_index().sort_values("data")
    df_p_a = df_p_a[df_p_a["tp"] > 0]
    df_p_a["mes_str"] = df_p_a["data"].apply(formata_mes_grafico)
    df_p_a["media_p"] = df_p_a["tp"] / df_p_a["d"]
    df_p_a["dif_m"] = df_p_a["tp"] - (df_p_a["tb"] * META_PESO)
    df_p_a["dif_d"] = df_p_a["dif_m"] / df_p_a["d"]

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(aplicar_estilo_grafico(px.bar(df_p_a, x="mes_str", y="tp", text="tp", title="TOTAL PESO MÊS", color_discrete_sequence=["#FFC300"])), use_container_width=True)
    with c2:
        st.plotly_chart(aplicar_estilo_grafico(px.bar(df_p_a, x="mes_str", y="media_p", text="media_p", title="MÉDIA PESO DIA", color_discrete_sequence=["#FFC300"])), use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        st.plotly_chart(aplicar_estilo_grafico(px.bar(df_p_a, x="mes_str", y="dif_m", text="dif_m", title="DIF. REAL VS IDEAL (MÊS)", color_discrete_sequence=["#FFC300"])), use_container_width=True)
    with c4:
        st.plotly_chart(aplicar_estilo_grafico(px.bar(df_p_a, x="mes_str", y="dif_d", text="dif_d", title="DIF. REAL VS IDEAL (DIA)", color_discrete_sequence=["#FFC300"])), use_container_width=True)

    st.markdown("---")
    st.subheader("📊 Distribuição de Peso")
    col_g, col_l = st.columns(2)
    with col_g:
        p_g = df_filtrado.groupby("grupo")["peso"].sum().reset_index().sort_values("peso", ascending=False)
        st.plotly_chart(aplicar_estilo_grafico(px.bar(p_g, x="grupo", y="peso", text="peso", title="PESO POR GRUPO", color_discrete_sequence=["#FF9F1C"])), use_container_width=True)
    with col_l:
        p_l = df_filtrado.groupby("local")["peso"].sum().reset_index().sort_values("peso", ascending=False).head(10)
        st.plotly_chart(aplicar_estilo_grafico(px.bar(p_l, x="local", y="peso", text="peso", title="PESO POR LOCAL", color_discrete_sequence=["#2A9D8F"])), use_container_width=True)


# --- BOMBONAS ---
elif st.session_state.pagina_atual == 'Bombonas':
    st.title("🛢️ Análise de Bombonas")
    st.markdown("---")
    k1, k2 = st.columns(2)
    k1.metric("TOTAL BOMBONAS", int(total_bombonas))
    k2.metric("MÉDIA/DIA", f"{int(total_bombonas / df_filtrado['data'].nunique())}")

    st.markdown("---")
    df_n_c = df_filtrado.groupby(pd.Grouper(key="data", freq="ME"))["bombonas"].sum().reset_index().sort_values("data")
    df_n_c = df_n_c[df_n_c["bombonas"] > 0]
    df_n_c["mes_fmt"] = df_n_c["data"].apply(formata_mes_abrev_ano)
    media_b_ref = int(df_n_c["bombonas"].mean())

    fig_n = go.Figure()
    fig_n.add_trace(go.Scatter(x=df_n_c["mes_fmt"], y=df_n_c["bombonas"], mode='lines+markers+text', name='Total', text=df_n_c["bombonas"]))
    fig_n.add_trace(go.Scatter(x=df_n_c["mes_fmt"], y=[media_b_ref]*len(df_n_c), mode='lines', name=f'Média: {media_b_ref}', line=dict(dash='dash', color='orange', width=3)))
    fig_n.update_layout(title="EVOLUÇÃO QTD BOMBONAS")
    st.plotly_chart(aplicar_estilo_grafico(fig_n), use_container_width=True)

    st.markdown("---")
    df_e_b = df_filtrado.groupby(pd.Grouper(key="data", freq="ME"))["bombonas"].sum().reset_index().sort_values("data")
    df_e_b = df_e_b[df_e_b["bombonas"] > 0]
    df_e_b["mes_str"] = df_e_b["data"].apply(formata_mes_grafico)
    st.plotly_chart(aplicar_estilo_grafico(px.bar(df_e_b, x="mes_str", y="bombonas", text="bombonas", title="TOTAL BOMBONAS MÊS", color_discrete_sequence=["#1f618d"])), use_container_width=True)

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(aplicar_estilo_grafico(px.bar(df_filtrado.groupby("grupo")["bombonas"].sum().reset_index(), x="grupo", y="bombonas", text="bombonas", title="POR GRUPO", color_discrete_sequence=["#FF9F1C"])), use_container_width=True)
    with c2:
        st.plotly_chart(aplicar_estilo_grafico(px.bar(df_filtrado.groupby("local")["bombonas"].sum().reset_index().nlargest(10, "bombonas"), x="local", y="bombonas", text="bombonas", title="POR LOCAL", color_discrete_sequence=["#2A9D8F"])), use_container_width=True)
    
    st.markdown("---")
    st.subheader("📈 Média de Bombonas por Dia (Evolução por Local)")
    df_m_e = df_filtrado.groupby([pd.Grouper(key="data", freq="ME"), "local"]).agg(tb=("bombonas", "sum"), d=("data", "nunique")).reset_index()
    df_m_e = df_m_e[df_m_e["tb"] > 0]
    df_m_e["media_dia"] = df_m_e["tb"] / df_m_e["d"]
    df_m_e["mes_str"] = df_m_e["data"].apply(formata_mes_grafico)
    fig_l_evol = px.line(df_m_e.sort_values("data"), x="mes_str", y="media_dia", color="local", text="media_dia", markers=True, title="MÉDIA DIÁRIA POR LOCAL")
    st.plotly_chart(aplicar_estilo_grafico(fig_l_evol), use_container_width=True)


# --- FINANCEIRO ---
elif st.session_state.pagina_atual == 'Financeiro':
    st.title("💰 Financeiro")
    st.markdown("---")
    f1, f2 = st.columns(2)
    f1.metric("GASTO CENÁRIO BASE", f"R$ {int(total_bombonas * PRECO_BASE):,.0f}".replace(",", "."))
    f2.metric("GASTO ESTIMADO", f"R$ {int(gasto_estimado):,.0f}".replace(",", "."))

    st.subheader("📈 Evolução de Gastos (R$)")
    fin_m = df_filtrado.groupby(pd.Grouper(key="data", freq="ME"))["bombonas"].sum().reset_index()
    fin_m = fin_m[fin_m["bombonas"] > 0]
    fin_m["custo"] = fin_m["bombonas"] * PRECO_ESTIMADO
    fin_m["mes_str"] = fin_m["data"].apply(formata_mes_grafico)
    fig_f = px.bar(fin_m, x="mes_str", y="custo", text="custo", title="CUSTO MENSAL ESTIMADO", color_discrete_sequence=["#2ca02c"])
    st.plotly_chart(aplicar_estilo_grafico(fig_f), use_container_width=True)

    st.markdown("---")
    st.subheader("📊 Distribuição de CUSTO")
    col_fin_g, col_fin_l = st.columns(2)
    
    with col_fin_g:
        fin_g = df_filtrado.groupby("grupo")["bombonas"].sum().reset_index()
        fin_g["custo_g"] = fin_g["bombonas"] * PRECO_ESTIMADO
        fig_fin_g = px.bar(fin_g.sort_values("custo_g", ascending=False), x="grupo", y="custo_g", text="custo_g", title="CUSTO POR GRUPO (R$)", color_discrete_sequence=["#E67E22"])
        st.plotly_chart(aplicar_estilo_grafico(fig_fin_g), use_container_width=True)
        
    with col_fin_l:
        fin_l = df_filtrado.groupby("local")["bombonas"].sum().reset_index()
        fin_l["custo_l"] = fin_l["bombonas"] * PRECO_ESTIMADO
        fig_fin_l = px.bar(fin_l.nlargest(10, "custo_l"), x="local", y="custo_l", text="custo_l", title="CUSTO POR LOCAL", color_discrete_sequence=["#27AE60"])
        st.plotly_chart(aplicar_estilo_grafico(fig_fin_l), use_container_width=True)