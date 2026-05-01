import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go 
from pathlib import Path
from datetime import timedelta

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
# 3. CARREGAMENTO E AUXILIARES (AJUSTADOS PARA INTEIROS)
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

def formata_numero_br(valor, prefixo=""):
    """Formata números para o padrão brasileiro sem casas decimais: 1.250"""
    if pd.isna(valor) or valor is None: 
        return f"{prefixo}0"
    valor_inteiro = int(round(valor))
    return f"{prefixo}{valor_inteiro:,}".replace(",", ".")

def formata_mes_grafico(x):
    try:
        if pd.isna(x): return "Data Inválida"
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

def aplicar_estilo_grafico(fig, is_financeiro=False):
    prefixo = "R$ " if is_financeiro else ""
    try:
        valores = []
        for trace in fig.data:
            if 'y' in trace and trace.y is not None:
                y_vals = [v for v in trace.y if v is not None and not pd.isna(v)]
                valores.extend(y_vals)
        if valores:
            max_y = max(valores)
            fig.update_yaxes(range=[0, max_y * 1.35])
    except:
        pass

    fig.update_layout(
        separators=",.", 
        font=dict(family="Arial Black", size=14, color="black"),
        title_font=dict(size=24, family="Arial Black", color="#1f618d"),
        xaxis=dict(tickfont=dict(size=14, family="Arial Black"), automargin=True),
        yaxis=dict(tickfont=dict(size=14, family="Arial Black"), automargin=True, tickformat=",.0f"),
        margin=dict(t=80, b=50, l=50, r=50),
        legend=dict(font=dict(size=12, family="Arial Black")),
        autosize=True
    )
    
    for trace in fig.data:
        if hasattr(trace, 'y') and trace.y is not None:
            textos_formatados = [formata_numero_br(v, prefixo) for v in trace.y]
            trace.update(text=textos_formatados, texttemplate='<b>%{text}</b>')
            
        if trace.type == 'bar':
            trace.update(textposition='outside', cliponaxis=False)
        else:
            trace.update(textposition='top center', cliponaxis=False)
            
    return fig

def exibir_comparativo_travado(df_raw, col_valor, titulo, prefixo=""):
    st.markdown(f"###  {titulo}")
    
    max_d = df_raw['data'].max()
    ini2, fim2 = max_d - timedelta(days=6), max_d
    ini1, fim1 = ini2 - timedelta(days=7), ini2 - timedelta(days=1)

    c1, c2, c3 = st.columns([2, 2, 3])
    with c1:
        d1 = st.date_input(f"Período 1 (Base) - {titulo[:3]}", [ini1.date(), fim1.date()], key=f"date1_{col_valor}")
    with c2:
        d2 = st.date_input(f"Período 2 (Atual) - {titulo[:3]}", [ini2.date(), fim2.date()], key=f"date2_{col_valor}")

    if len(d1) == 2 and len(d2) == 2:
        v1 = df_raw[(df_raw['data'].dt.date >= d1[0]) & (df_raw['data'].dt.date <= d1[1])][col_valor].sum()
        v2 = df_raw[(df_raw['data'].dt.date >= d2[0]) & (df_raw['data'].dt.date <= d2[1])][col_valor].sum()
        
        v1 = 0 if pd.isna(v1) else float(v1)
        v2 = 0 if pd.isna(v2) else float(v2)
        
        diff = v2 - v1
        perc = (diff / v1 * 100) if v1 != 0 else 0

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=["P1 (Anterior)", "P2 (Atual)"],
            y=[v1, v2],
            text=[formata_numero_br(v1, prefixo), formata_numero_br(v2, prefixo)],
            marker_color=['#FFD700', '#1f618d'], 
            width=0.4
        ))
        
        fig.update_layout(
            height=320,
            title=f"Diferença: {formata_numero_br(diff, prefixo)} ({int(perc):+d}%)",
            margin=dict(t=40, b=10)
        )
        st.plotly_chart(aplicar_estilo_grafico(fig, prefixo != ""), use_container_width=True)

# --- CARREGAMENTO ---
BASE_DIR = Path(__file__).resolve().parent.parent
ARQUIVO_DADOS = BASE_DIR / "dados" / "bombonas_v2.csv"

@st.cache_data
def carregar_dados_v2():
    caminho = ARQUIVO_DADOS
    if not caminho.exists(): caminho = Path("dados/bombonas_v2.csv")
    if not caminho.exists(): return None

    try:
        df_base = pd.read_csv(caminho)
        df_base.columns = df_base.columns.str.strip().str.lower()
        df_base["data"] = pd.to_datetime(df_base["data"])
        df_base["ano"] = df_base["data"].dt.year
        df_base["mes_nome"] = df_base["data"].dt.month.map(MESES_PT)
        df_base["mes_ano_ref"] = df_base["data"].apply(formata_mes_abrev_ano)

        if "local" in df_base.columns: df_base["local"] = df_base["local"].astype(str).str.strip().str.upper()
        if "grupo" in df_base.columns: 
            df_base["grupo"] = df_base["grupo"].astype(str).str.strip().str.upper()
            df_base = df_base[~df_base["grupo"].isin(["UM", "NAN", "NONE"])]

        df_base['mes_grafico'] = df_base['data'].apply(formata_mes_grafico)
        return df_base
    except Exception as e: st.error(f"Erro: {e}"); return None

df = carregar_dados_v2()

if df is None or df.empty:
    st.warning("⚠️ Dados não encontrados.")
    st.stop()

# ==================================================
# 4. BARRA LATERAL (FILTROS)
# ==================================================
with st.sidebar:
    if st.session_state.pagina_atual != 'Home':
        if st.button("🏠 Voltar ao Início", width='stretch'):
            ir_para("Home")
            st.rerun()
        st.markdown("---")

    with st.expander("⚙️ Configurações / Simulador", expanded=False):
        st.caption("Ajuste os valores para simular cenários:")
        META_PESO = st.number_input("Meta Peso (kg)", value=25.0, step=1.0)
        PRECO_BASE = st.number_input("Preço Red 5% (R$)", value=95.0, step=1.0)
        PRECO_ESTIMADO = st.number_input("Preço Base (R$)", value=101.0, step=1.0)
    
    st.markdown("---")
    st.header("🔍 Filtros")
    
    opcoes_mes_ano = df.sort_values("data")["mes_ano_ref"].unique().tolist()
    filtro_mes_ano = st.multiselect("📅 Mês/Ano (Ex: Jan.25)", options=opcoes_mes_ano)

    opcoes_ano = sorted(df["ano"].unique().tolist(), reverse=True)
    filtro_ano = st.multiselect("📅 Ano (Simples)", options=opcoes_ano)
    
    df_temp = df.copy()
    if filtro_mes_ano: df_temp = df_temp[df_temp["mes_ano_ref"].isin(filtro_mes_ano)]
    if filtro_ano: df_temp = df_temp[df_temp["ano"].isin(filtro_ano)]

    ordem_meses = [MESES_PT[i] for i in range(1, 13)]
    meses_disponiveis = [m for m in ordem_meses if m in df_temp["mes_nome"].unique()]
    filtro_mes = st.multiselect("🗓️ Mês (Simples)", options=meses_disponiveis)

    opcoes_local = sorted(df_temp["local"].unique().tolist())
    filtro_local = st.multiselect("📍 Local", options=opcoes_local)

    opcoes_grupo = sorted(df_temp["grupo"].unique().tolist())
    filtro_grupo = st.multiselect("📦 Grupo", options=opcoes_grupo)

df_filtrado = df_temp.copy()
if filtro_local: df_filtrado = df_filtrado[df_filtrado["local"].isin(filtro_local)]
if filtro_grupo: df_filtrado = df_filtrado[df_filtrado["grupo"].isin(filtro_grupo)]
if filtro_mes: df_filtrado = df_filtrado[df_filtrado["mes_nome"].isin(filtro_mes)]

if df_filtrado.empty:
    st.info("Nenhum dado encontrado.")
    st.stop()

# Cálculos Gerais
total_bombonas = int(df_filtrado["bombonas"].sum())
total_peso_real = df_filtrado["peso"].sum()
peso_ideal_total = total_bombonas * META_PESO 
diferenca_peso = total_peso_real - peso_ideal_total
gasto_estimado = total_bombonas * PRECO_ESTIMADO

# ==================================================
# 5. PÁGINAS DO SISTEMA
# ==================================================

# --- HOME ---
if st.session_state.pagina_atual == 'Home':
    st.title("♻️ Painel Analise de Bombonas")
    st.markdown(f"**Cenário Atual:** Meta {int(META_PESO)}kg | Custo Est. R$ {int(PRECO_ESTIMADO)}")
    st.markdown("---")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("TOTAL PESO", formata_numero_br(total_peso_real), delta=None)
        if st.button("Acessar Peso", key="btn_peso"): ir_para("Peso"); st.rerun()
    with c2:
        st.metric("UNIDADES", f"{int(total_bombonas)}")
        if st.button("Acessar Bombonas", key="btn_bomb"): ir_para("Bombonas"); st.rerun()
    with c3:
        st.metric("CUSTO BASE", formata_numero_br(gasto_estimado, "R$ "))
        if st.button("Acessar Financeiro", key="btn_fin"): ir_para("Financeiro"); st.rerun()

    st.markdown("---")
    st.subheader(" Visão Geral")
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
    k1.metric("PESO REAL", formata_numero_br(total_peso_real))
    k2.metric(f"META ({int(META_PESO)}KG)", formata_numero_br(peso_ideal_total))
    k3.metric("DIFERENÇA", formata_numero_br(diferenca_peso), delta_color="inverse")

    st.markdown("---")
    exibir_comparativo_travado(df, "peso", "Comparativo de Peso")
    
    st.markdown("---")
    df_p_m_n = df_filtrado.groupby(pd.Grouper(key="data", freq="ME"))["peso"].sum().reset_index().sort_values("data")
    df_p_m_n = df_p_m_n[df_p_m_n["peso"] > 0]
    df_p_m_n["mes_fmt"] = df_p_m_n["data"].apply(formata_mes_abrev_ano)
    media_p_ref = int(df_p_m_n["peso"].mean())

    fig_p_n = go.Figure()
    fig_p_n.add_trace(go.Scatter(x=df_p_m_n["mes_fmt"], y=df_p_m_n["peso"], mode='lines+markers+text', name='Real', line=dict(color='#1f618d', width=4)))
    fig_p_n.add_trace(go.Scatter(x=df_p_m_n["mes_fmt"], y=[media_p_ref]*len(df_p_m_n), mode='lines', name=f'Média: {media_p_ref}', line=dict(color='orange', width=3, dash='dash')))
    fig_p_n.update_layout(title="TOTAL PESO MÊS (Comparativo Real vs Média)")
    st.plotly_chart(aplicar_estilo_grafico(fig_p_n), use_container_width=True)

    st.markdown("---")
    st.subheader("Comparativo Mensal (Real vs Meta)")
    mensal = df_filtrado.groupby(pd.Grouper(key="data", freq="ME")).agg(peso_real=("peso", "sum"), qtd=("bombonas", "sum")).reset_index().sort_values("data")
    mensal = mensal[mensal["peso_real"] > 0]
    mensal["peso_ideal"] = mensal["qtd"] * META_PESO
    mensal["mes_str"] = mensal["data"].apply(formata_mes_grafico)

    # Criação do texto detalhado para a legenda da Meta
    meta_labels = "<br>".join([f"{row['mes_str']}: {formata_numero_br(row['peso_ideal'])}" for _, row in mensal.iterrows()])

    fig_p = go.Figure()
    fig_p.add_trace(go.Scatter(x=mensal["mes_str"], y=mensal["peso_real"], mode='lines+markers+text', name='Real', line=dict(color='#1f618d', width=4)))
    fig_p.add_trace(go.Scatter(x=mensal["mes_str"], y=mensal["peso_ideal"], mode='lines', name=f'Meta:<br>{meta_labels}', line=dict(color='red', width=3, dash='dash')))
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
    with c1: st.plotly_chart(aplicar_estilo_grafico(px.bar(df_p_a, x="mes_str", y="tp", title="TOTAL PESO MÊS", color_discrete_sequence=["#FFC300"])), use_container_width=True)
    with c2: st.plotly_chart(aplicar_estilo_grafico(px.bar(df_p_a, x="mes_str", y="media_p", title="MÉDIA PESO DIA", color_discrete_sequence=["#FFC300"])), use_container_width=True)

    c3, c4 = st.columns(2)
    with c3: st.plotly_chart(aplicar_estilo_grafico(px.bar(df_p_a, x="mes_str", y="dif_m", title="DIF. REAL VS IDEAL (MÊS)", color_discrete_sequence=["#FFC300"])), use_container_width=True)
    with c4: st.plotly_chart(aplicar_estilo_grafico(px.bar(df_p_a, x="mes_str", y="dif_d", title="DIF. REAL VS IDEAL (DIA)", color_discrete_sequence=["#FFC300"])), use_container_width=True)

    st.markdown("---")
    st.subheader(" Distribuição de Peso")
    col_g, col_l = st.columns(2)
    with col_g:
        p_g = df_filtrado.groupby("grupo")["peso"].sum().reset_index().sort_values("peso", ascending=False)
        st.plotly_chart(aplicar_estilo_grafico(px.bar(p_g, x="grupo", y="peso", title="PESO POR GRUPO", color_discrete_sequence=["#FF9F1C"])), use_container_width=True)
    with col_l:
        p_l = df_filtrado.groupby("local")["peso"].sum().reset_index().sort_values("peso", ascending=False).head(10)
        st.plotly_chart(aplicar_estilo_grafico(px.bar(p_l, x="local", y="peso", title="PESO POR LOCAL", color_discrete_sequence=["#2A9D8F"])), use_container_width=True)

# --- BOMBONAS ---
elif st.session_state.pagina_atual == 'Bombonas':
    st.title("🛢️ Análise de Bombonas")
    st.markdown("---")

    k1, k2 = st.columns(2)
    k1.metric("TOTAL BOMBONAS", int(total_bombonas))
    k2.metric("MÉDIA/DIA", int(total_bombonas / df_filtrado['data'].nunique()) if df_filtrado['data'].nunique() > 0 else 0)

    st.markdown("---")
    exibir_comparativo_travado(df, "bombonas", "Comparativo de Bombonas")

    st.markdown("---")
    df_n_c = df_filtrado.groupby(pd.Grouper(key="data", freq="ME"))["bombonas"].sum().reset_index().sort_values("data")
    df_n_c = df_n_c[df_n_c["bombonas"] > 0]
    df_n_c["mes_fmt"] = df_n_c["data"].apply(formata_mes_abrev_ano)
    media_b_ref = int(df_n_c["bombonas"].mean())

    fig_n = go.Figure()
    fig_n.add_trace(go.Scatter(x=df_n_c["mes_fmt"], y=df_n_c["bombonas"], mode='lines+markers+text', name='Total'))
    fig_n.add_trace(go.Scatter(x=df_n_c["mes_fmt"], y=[media_b_ref]*len(df_n_c), mode='lines', name=f'Média: {media_b_ref}', line=dict(dash='dash', color='orange', width=3)))
    fig_n.update_layout(title="EVOLUÇÃO QTD BOMBONAS")
    st.plotly_chart(aplicar_estilo_grafico(fig_n), use_container_width=True)

    st.markdown("---")
    df_e_b = df_filtrado.groupby(pd.Grouper(key="data", freq="ME"))["bombonas"].sum().reset_index().sort_values("data")
    df_e_b["mes_str"] = df_e_b["data"].apply(formata_mes_grafico)
    st.plotly_chart(aplicar_estilo_grafico(px.bar(df_e_b, x="mes_str", y="bombonas", title="TOTAL BOMBONAS MÊS", color_discrete_sequence=["#1f618d"])), use_container_width=True)

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1: st.plotly_chart(aplicar_estilo_grafico(px.bar(df_filtrado.groupby("grupo")["bombonas"].sum().reset_index(), x="grupo", y="bombonas", title="POR GRUPO", color_discrete_sequence=["#FF9F1C"])), use_container_width=True)
    with c2: st.plotly_chart(aplicar_estilo_grafico(px.bar(df_filtrado.groupby("local")["bombonas"].sum().reset_index().nlargest(10, "bombonas"), x="local", y="bombonas", title="POR LOCAL", color_discrete_sequence=["#2A9D8F"])), use_container_width=True)
    
    st.markdown("---")
    st.subheader("📈 Média de Bombonas por Dia (Evolução por Local)")
    df_m_e = df_filtrado.groupby([pd.Grouper(key="data", freq="ME"), "local"]).agg(tb=("bombonas", "sum"), d=("data", "nunique")).reset_index()
    df_m_e["media_dia"] = df_m_e["tb"] / df_m_e["d"]
    df_m_e["mes_str"] = df_m_e["data"].apply(formata_mes_grafico)
    fig_l_evol = px.line(df_m_e.sort_values("data"), x="mes_str", y="media_dia", color="local", text="media_dia", title="MÉDIA DIÁRIA POR LOCAL")
    st.plotly_chart(aplicar_estilo_grafico(fig_l_evol), use_container_width=True)

# --- FINANCEIRO ---
elif st.session_state.pagina_atual == 'Financeiro':
    st.title("💰 Financeiro")
    st.markdown("---")

    f1, f2 = st.columns(2)
    f1.metric("CUSTO RED 5%", formata_numero_br(total_bombonas * PRECO_BASE, "R$ "))
    f2.metric("CUSTO BASE", formata_numero_br(gasto_estimado, "R$ "))

    st.markdown("---")
    exibir_comparativo_travado(df, "bombonas", "Comparativo Financeiro", prefixo="R$ ")

    st.markdown("---")
    st.subheader("Custo Mensal Mes a Mes")
    fin_m = df_filtrado.groupby(pd.Grouper(key="data", freq="ME"))["bombonas"].sum().reset_index()
    fin_m = fin_m[fin_m["bombonas"] > 0]
    fin_m["custo"] = fin_m["bombonas"] * PRECO_ESTIMADO
    fin_m["mes_str"] = fin_m["data"].apply(formata_mes_grafico)
    fig_f = px.bar(fin_m, x="mes_str", y="custo", title="CUSTO MENSAL BASE", color_discrete_sequence=["#2ca02c"])
    st.plotly_chart(aplicar_estilo_grafico(fig_f, is_financeiro=True), use_container_width=True)

    st.markdown("---")
    st.subheader(" Custo por Local")
    c1, c2 = st.columns(2)
    with c1:
        fin_g = df_filtrado.groupby("grupo")["bombonas"].sum().reset_index()
        fin_g["custo_g"] = fin_g["bombonas"] * PRECO_ESTIMADO
        st.plotly_chart(aplicar_estilo_grafico(px.bar(fin_g.sort_values("custo_g", ascending=False), x="grupo", y="custo_g", title="CUSTO POR GRUPO", color_discrete_sequence=["#E67E22"]), is_financeiro=True), use_container_width=True)
    with c2:
        fin_l = df_filtrado.groupby("local")["bombonas"].sum().reset_index()
        fin_l["custo_l"] = fin_l["bombonas"] * PRECO_ESTIMADO
        st.plotly_chart(aplicar_estilo_grafico(px.bar(fin_l.nlargest(10, "custo_l"), x="local", y="custo_l", title="CUSTO POR LOCAL", color_discrete_sequence=["#27AE60"]), is_financeiro=True), use_container_width=True)