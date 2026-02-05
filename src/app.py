import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go 
from pathlib import Path

# ==================================================
# 1. CONFIGURAÇÃO E CSS
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
        .stButton > button {
            width: 100%;
            border-radius: 8px;
            height: 3em;
            font-weight: 600;
            border: 1px solid #d1d1d1;
        }
        .stButton > button:hover {
            border-color: #0083B8;
            color: #0083B8;
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
# 3. CARREGAMENTO DE DADOS E FORMATAÇÃO
# ==================================================
MESES_PT = {
    1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 
    5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto', 
    9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
}

MESES_ABREV = {
    1: 'jan', 2: 'fev', 3: 'mar', 4: 'abr',
    5: 'mai', 6: 'jun', 7: 'jul', 8: 'ago',
    9: 'set', 10: 'out', 11: 'nov', 12: 'dez'
}

def formata_mes_grafico(x):
    try:
        if pd.isna(x): return "Data Inválida"
        return f"{MESES_PT[x.month]}/{x.year}"
    except:
        return f"{x.month}/{x.year}"

def formata_mes_abrev_ano(x):
    try:
        if pd.isna(x): return ""
        ano_curto = str(x.year)[-2:]
        return f"{MESES_ABREV[x.month]}.{ano_curto}"
    except:
        return ""

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
        
        # --- AJUSTE: Filtro agora usa apenas o nome do mês ---
        df["mes_nome"] = df["data"].dt.month.map(MESES_PT)
        
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
# 4. BARRA LATERAL (Filtros)
# ==================================================
with st.sidebar:
    if st.session_state.pagina_atual != 'Home':
        if st.button("🏠 Voltar ao Início", use_container_width=True):
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
    
    opcoes_ano = sorted(df["ano"].unique().tolist(), reverse=True)
    filtro_ano = st.multiselect("📅 Ano", options=opcoes_ano)
    
    df_temp = df.copy()
    if filtro_ano:
        df_temp = df_temp[df_temp["ano"].isin(filtro_ano)]

    # --- AJUSTE: Filtro apenas com Nome do Mês ---
    # Ordena os meses cronologicamente de 1 a 12
    ordem_meses = [MESES_PT[i] for i in range(1, 13)]
    meses_disponiveis = [m for m in ordem_meses if m in df_temp["mes_nome"].unique()]
    filtro_mes = st.multiselect("🗓️ Mês", options=meses_disponiveis)

    opcoes_local = sorted(df_temp["local"].unique().tolist())
    filtro_local = st.multiselect("📍 Local", options=opcoes_local)

    opcoes_grupo = sorted(df_temp["grupo"].unique().tolist())
    filtro_grupo = st.multiselect("📦 Grupo", options=opcoes_grupo)

# Aplicação dos Filtros
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
# 5. PÁGINAS DO SISTEMA
# ==================================================

# --- HOME ---
if st.session_state.pagina_atual == 'Home':
    st.title("♻️ Painel de Controle")
    st.markdown(f"**Cenário Atual:** Meta {META_PESO}kg | Custo Est. R$ {PRECO_ESTIMADO}")
    st.markdown("---")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.info("⚖️ **PESO**")
        st.metric("Total", f"{total_peso_real:,.0f} kg".replace(",", "X").replace(".", ",").replace("X", "."))
        if st.button("Acessar Peso"): ir_para("Peso"); st.rerun()
    with c2:
        st.info("🛢️ **BOMBONAS**")
        st.metric("Unidades", f"{int(total_bombonas)}")
        if st.button("Acessar Bombonas"): ir_para("Bombonas"); st.rerun()
    with c3:
        st.info("💰 **FINANCEIRO**")
        val_fmt = f"R$ {gasto_estimado:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        st.metric("Gasto Estimado", val_fmt)
        if st.button("Acessar Financeiro"): ir_para("Financeiro"); st.rerun()

    st.markdown("---")
    st.subheader("📊 Visão Geral")
    resumo = df_filtrado.groupby(pd.Grouper(key="data", freq="ME"))["bombonas"].sum().reset_index()
    resumo = resumo[resumo["bombonas"] > 0]
    resumo["mes_str"] = resumo["data"].apply(formata_mes_grafico)
    
    fig = px.bar(resumo, x="mes_str", y="bombonas", text="bombonas", title="Total de Bombonas Mês")
    fig.update_traces(textposition='outside', texttemplate='<b>%{text}</b>')
    fig.update_layout(yaxis_title=None, xaxis_title=None, plot_bgcolor="rgba(0,0,0,0)", xaxis={'type': 'category'})
    st.plotly_chart(fig, use_container_width=True)


# --- PESO ---
elif st.session_state.pagina_atual == 'Peso':
    st.title("⚖️ Análise de Peso")
    st.markdown("---")

    k1, k2, k3 = st.columns(3)
    k1.metric("Peso Real", f"{total_peso_real:,.2f} kg".replace(",", "X").replace(".", ",").replace("X", "."))
    k2.metric(f"Meta ({META_PESO}kg)", f"{peso_ideal_total:,.2f} kg".replace(",", "X").replace(".", ",").replace("X", "."))
    k3.metric("Diferença", f"{diferenca_peso:,.2f} kg".replace(",", "X").replace(".", ",").replace("X", "."), delta_color="inverse")

    st.markdown("---")
    df_p_m_n = df_filtrado.groupby(pd.Grouper(key="data", freq="ME"))["peso"].sum().reset_index().sort_values("data")
    df_p_m_n = df_p_m_n[df_p_m_n["peso"] > 0]
    df_p_m_n["mes_fmt"] = df_p_m_n["data"].apply(formata_mes_abrev_ano)
    media_p_ref = df_p_m_n["peso"].mean()

    fig_p_n = go.Figure()
    fig_p_n.add_trace(go.Scatter(x=df_p_m_n["mes_fmt"], y=df_p_m_n["peso"], mode='lines+markers+text', name='Total Peso Real', line=dict(color='#1f618d', width=3), marker=dict(size=8, color='#1f618d'), text=df_p_m_n["peso"].astype(int), textposition="top center", textfont=dict(color='#1f618d', family="Arial Black")))
    fig_p_n.add_trace(go.Scatter(x=df_p_m_n["mes_fmt"], y=[media_p_ref]*len(df_p_m_n), mode='lines+markers+text', name='Média do Período', line=dict(color='#E65100', width=3), marker=dict(size=8, color='#E65100'), text=[int(media_p_ref)]*len(df_p_m_n), textposition="bottom center", textfont=dict(color='#E65100', family="Arial Black")))
    fig_p_n.update_layout(title=dict(text="<b>TOTAL PESO MÊS (Comparativo Real vs Média)</b>", x=0.5, xanchor='center'), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), margin=dict(t=60, b=30, l=20, r=20))
    fig_p_n.update_yaxes(showgrid=False, showticklabels=False, zeroline=False, title=None)
    fig_p_n.update_xaxes(showgrid=False, zeroline=False, title=None, type='category')
    st.plotly_chart(fig_p_n, use_container_width=True)

    st.markdown("---")
    st.subheader("Comparativo Mensal (Real vs Meta)")
    mensal = df_filtrado.groupby(pd.Grouper(key="data", freq="ME")).agg(peso_real=("peso", "sum"), qtd=("bombonas", "sum")).reset_index().sort_values("data")
    mensal = mensal[mensal["peso_real"] > 0]
    mensal["peso_ideal"] = mensal["qtd"] * META_PESO
    mensal["mes_str"] = mensal["data"].apply(formata_mes_grafico)
    fig_p = px.bar(mensal, x="mes_str", y="peso_real", text="peso_real", title="Real vs Meta", color_discrete_sequence=["#0083B8"])
    fig_p.add_scatter(x=mensal["mes_str"], y=mensal["peso_ideal"], mode='lines+markers+text', name='Meta', line=dict(color='#E63946', width=3), text=mensal["peso_ideal"], textposition="top center")
    fig_p.update_traces(texttemplate='<b>%{text:.0f}</b>', textposition='outside', selector=dict(type='bar'))
    fig_p.update_layout(yaxis_title=None, xaxis_title=None, plot_bgcolor="rgba(0,0,0,0)", xaxis={'type': 'category'})
    st.plotly_chart(fig_p, use_container_width=True)

    st.markdown("---")
    st.subheader("🔎 Detalhamento dos Indicadores")
    df_p_a = df_filtrado.groupby(pd.Grouper(key="data", freq="ME")).agg(tp=("peso", "sum"), tb=("bombonas", "sum"), d=("data", "nunique")).reset_index().sort_values("data")
    df_p_a = df_p_a[df_p_a["tp"] > 0]
    df_p_a["mes_str"] = df_p_a["data"].apply(formata_mes_grafico)
    df_p_a["media_p"] = df_p_a["tp"] / df_p_a["d"]
    df_p_a["dif_m"] = df_p_a["tp"] - (df_p_a["tb"] * META_PESO)
    df_p_a["dif_d"] = df_p_a["dif_m"] / df_p_a["d"]

    COR_B = ["#FFC300"] 
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(px.bar(df_p_a, x="mes_str", y="tp", text="tp", title="TOTAL PESO MÊS", color_discrete_sequence=COR_B).update_traces(textposition='outside', texttemplate='<b>%{text:.0f}</b>').update_layout(plot_bgcolor="rgba(0,0,0,0)", xaxis={'type': 'category'}), use_container_width=True)
    with c2:
        st.plotly_chart(px.bar(df_p_a, x="mes_str", y="media_p", text="media_p", title="MÉDIA PESO DIA", color_discrete_sequence=COR_B).update_traces(textposition='outside', texttemplate='<b>%{text:.0f}</b>').update_layout(plot_bgcolor="rgba(0,0,0,0)", xaxis={'type': 'category'}), use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        st.plotly_chart(px.bar(df_p_a, x="mes_str", y="dif_m", text="dif_m", title="DIF. PESO REAL VS IDEAL (MÊS)", color_discrete_sequence=COR_B).update_traces(textposition='outside', texttemplate='<b>%{text:.0f}</b>').update_layout(plot_bgcolor="rgba(0,0,0,0)", xaxis={'type': 'category'}), use_container_width=True)
    with c4:
        st.plotly_chart(px.bar(df_p_a, x="mes_str", y="dif_d", text="dif_d", title="DIF. PESO REAL VS IDEAL (DIA)", color_discrete_sequence=COR_B).update_traces(textposition='outside', texttemplate='<b>%{text:.0f}</b>').update_layout(plot_bgcolor="rgba(0,0,0,0)", xaxis={'type': 'category'}), use_container_width=True)

    st.markdown("---")
    st.subheader("📊 Distribuição de Peso (Grupo e Local)")
    col_g, col_l = st.columns(2)
    with col_g:
        p_g = df_filtrado.groupby("grupo")["peso"].sum().reset_index().sort_values("peso", ascending=False)
        st.plotly_chart(px.bar(p_g, x="grupo", y="peso", text="peso", title="PESO POR GRUPO", color_discrete_sequence=["#FF9F1C"]).update_traces(textposition='outside', texttemplate='<b>%{text:,.0f}</b>').update_layout(plot_bgcolor="rgba(0,0,0,0)"), use_container_width=True)
    with col_l:
        p_l = df_filtrado.groupby("local")["peso"].sum().reset_index().sort_values("peso", ascending=False).head(10)
        st.plotly_chart(px.bar(p_l, x="local", y="peso", text="peso", title="PESO POR LOCAL", color_discrete_sequence=["#2A9D8F"]).update_traces(textposition='outside', texttemplate='<b>%{text:,.0f}</b>').update_layout(plot_bgcolor="rgba(0,0,0,0)"), use_container_width=True)


# --- BOMBONAS ---
elif st.session_state.pagina_atual == 'Bombonas':
    st.title("🛢️ Análise de Bombonas")
    st.markdown("---")
    k1, k2 = st.columns(2)
    k1.metric("Total", int(total_bombonas))
    k2.metric("Média/Dia", f"{(total_bombonas / df_filtrado['data'].nunique()):.1f}")

    st.markdown("---")
    df_n_c = df_filtrado.groupby(pd.Grouper(key="data", freq="ME"))["bombonas"].sum().reset_index().sort_values("data")
    df_n_c = df_n_c[df_n_c["bombonas"] > 0]
    df_n_c["mes_fmt"] = df_n_c["data"].apply(formata_mes_abrev_ano)
    media_r = df_n_c["bombonas"].mean()

    fig_n = go.Figure()
    fig_n.add_trace(go.Scatter(x=df_n_c["mes_fmt"], y=df_n_c["bombonas"], mode='lines+markers+text', name='Total Mês', line=dict(color='#1f618d', width=3), marker=dict(size=8, color='#1f618d'), text=df_n_c["bombonas"], textposition="top center", textfont=dict(color='#1f618d', family="Arial Black")))
    fig_n.add_trace(go.Scatter(x=df_n_c["mes_fmt"], y=[media_r]*len(df_n_c), mode='lines+markers+text', name='Média do Período', line=dict(color='#E65100', width=3), marker=dict(size=8, color='#E65100'), text=[int(media_r)]*len(df_n_c), textposition="bottom center", textfont=dict(color='#E65100', family="Arial Black")))
    fig_n.update_layout(title=dict(text="<b>TOTAL BOMBONAS MÊS (Comparativo)</b>", x=0.5, xanchor='center'), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), margin=dict(t=50, b=20, l=20, r=20))
    fig_n.update_yaxes(showgrid=False, showticklabels=False, zeroline=False, title=None)
    fig_n.update_xaxes(showgrid=False, zeroline=False, title=None, type='category')
    st.plotly_chart(fig_n, use_container_width=True)

    st.markdown("---")
    st.markdown("### 📊 Evolução Mensal (Barras)") 
    df_e_b = df_filtrado.groupby(pd.Grouper(key="data", freq="ME"))["bombonas"].sum().reset_index().sort_values("data")
    df_e_b = df_e_b[df_e_b["bombonas"] > 0]
    df_e_b["mes_str"] = df_e_b["data"].apply(formata_mes_grafico)
    st.plotly_chart(px.bar(df_e_b, x="mes_str", y="bombonas", text="bombonas", title="TOTAL BOMBONAS MÊS", color_discrete_sequence=["#1f618d"]).update_traces(textposition='outside', texttemplate='<b>%{text}</b>').update_layout(plot_bgcolor="rgba(0,0,0,0)", xaxis={'type': 'category'}), use_container_width=True)

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(px.bar(df_filtrado.groupby("grupo")["bombonas"].sum().reset_index(), x="grupo", y="bombonas", text="bombonas", title="Por Grupo", color_discrete_sequence=["#FF9F1C"]).update_traces(textposition='outside'), use_container_width=True)
    with c2:
        st.plotly_chart(px.bar(df_filtrado.groupby("local")["bombonas"].sum().reset_index().sort_values("bombonas", ascending=False).head(10), x="local", y="bombonas", text="bombonas", title="Por Local", color_discrete_sequence=["#2A9D8F"]).update_traces(textposition='outside'), use_container_width=True)
    
    st.markdown("---")
    st.subheader("📈 Média de Bombonas por Dia (Evolução por Local)")
    df_m_e = df_filtrado.groupby([pd.Grouper(key="data", freq="ME"), "local"]).agg(tb=("bombonas", "sum"), d=("data", "nunique")).reset_index()
    df_m_e = df_m_e[df_m_e["tb"] > 0]
    df_m_e["media_dia"] = df_m_e["tb"] / df_m_e["d"]
    df_m_e["mes_str"] = df_m_e["data"].apply(formata_mes_grafico)
    st.plotly_chart(px.line(df_m_e.sort_values("data"), x="mes_str", y="media_dia", color="local", text="media_dia", markers=True, title="Média Diária por Local").update_traces(textposition="top center", texttemplate="<b>%{text:.2f}</b>").update_layout(plot_bgcolor="rgba(0,0,0,0)", xaxis={'type': 'category'}), use_container_width=True)


# --- FINANCEIRO ---
elif st.session_state.pagina_atual == 'Financeiro':
    st.title("💰 Financeiro")
    st.markdown("---")
    f1, f2 = st.columns(2)
    v1 = f"R$ {total_bombonas * PRECO_BASE:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    v2 = f"R$ {gasto_estimado:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    f1.metric(f"Cenário Base (R$ {PRECO_BASE})", v1)
    f2.metric(f"Estimado (R$ {PRECO_ESTIMADO})", v2)

    st.subheader("Evolução de Gastos (R$)")
    fin_m = df_filtrado.groupby(pd.Grouper(key="data", freq="ME"))["bombonas"].sum().reset_index()
    fin_m = fin_m[fin_m["bombonas"] > 0]
    fin_m["custo"] = fin_m["bombonas"] * PRECO_ESTIMADO
    fin_m["mes_str"] = fin_m["data"].apply(formata_mes_grafico)
    st.plotly_chart(px.bar(fin_m, x="mes_str", y="custo", text="custo", title="Custo Mensal Estimado", color_discrete_sequence=["#2ca02c"]).update_traces(texttemplate='<b>R$ %{text:,.2f}</b>', textposition='outside').update_layout(plot_bgcolor="rgba(0,0,0,0)", xaxis={'type': 'category'}), use_container_width=True)