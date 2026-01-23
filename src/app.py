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
# 3. CARREGAMENTO DE DADOS
# ==================================================
MESES_PT = {
    1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 
    5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto', 
    9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
}

# Dicionário para abreviações (usado no novo gráfico)
MESES_ABREV = {
    1: 'jan', 2: 'fev', 3: 'mar', 4: 'abr',
    5: 'mai', 6: 'jun', 7: 'jul', 8: 'ago',
    9: 'set', 10: 'out', 11: 'nov', 12: 'dez'
}

def formata_mes(x):
    try:
        if pd.isna(x): return "Data Inválida"
        return f"{MESES_PT[x.month]}/{x.year}"
    except:
        return f"{x.month}/{x.year}"

# --- FUNÇÃO DE FORMATAÇÃO PARA O GRÁFICO ESTILO IMAGEM (jan.25) ---
def formata_mes_abrev_ano(x):
    try:
        if pd.isna(x): return ""
        # Pega os últimos 2 dígitos do ano
        ano_curto = str(x.year)[-2:]
        return f"{MESES_ABREV[x.month]}.{ano_curto}"
    except:
        return ""
# -------------------------------------------------------------------

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
        
        if "local" in df.columns: df["local"] = df["local"].astype(str).str.strip().str.upper()
        if "grupo" in df.columns: 
            df["grupo"] = df["grupo"].astype(str).str.strip().str.upper()
            df = df[~df["grupo"].isin(["UM", "NAN", "NONE"])]

        df['mes_filtro'] = df['data'].apply(formata_mes)
        df['data_sort'] = df['data']
        return df
    except Exception as e: st.error(f"Erro: {e}"); return None

df = carregar_dados_v2()

if df is None or df.empty:
    st.warning("⚠️ Dados não encontrados.")
    st.stop()

# ==================================================
# 4. BARRA LATERAL
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
    
    opcoes_local = sorted(df["local"].unique().tolist())
    filtro_local = st.multiselect("📍 Local", options=opcoes_local)

    opcoes_grupo = sorted(df["grupo"].unique().tolist())
    filtro_grupo = st.multiselect("📦 Grupo", options=opcoes_grupo)

    meses_ordenados = df.sort_values("data_sort")["mes_filtro"].unique().tolist()
    filtro_mes = st.multiselect("🗓️ Mês", options=meses_ordenados)

    st.markdown("---")
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Baixar CSV", csv, "dados.csv", "text/csv")

# Filtros
df_filtrado = df.copy()
if filtro_local: df_filtrado = df_filtrado[df_filtrado["local"].isin(filtro_local)]
if filtro_grupo: df_filtrado = df_filtrado[df_filtrado["grupo"].isin(filtro_grupo)]
if filtro_mes: df_filtrado = df_filtrado[df_filtrado["mes_filtro"].isin(filtro_mes)]

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
# 6. PÁGINAS DO SISTEMA
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
    resumo["mes_str"] = resumo["data"].apply(formata_mes)
    
    fig = px.bar(resumo, x="mes_str", y="bombonas", text="bombonas", title="Total de Bombonas Mês")
    fig.update_traces(textposition='outside', texttemplate='<b>%{text}</b>')
    fig.update_layout(yaxis_title=None, xaxis_title=None, plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)


# --- PESO (MÓDULO COM AS ADIÇÕES) ---
elif st.session_state.pagina_atual == 'Peso':
    st.title("⚖️ Análise de Peso")
    st.markdown("---")

    k1, k2, k3 = st.columns(3)
    k1.metric("Peso Real", f"{total_peso_real:,.2f} kg".replace(",", "X").replace(".", ",").replace("X", "."))
    k2.metric(f"Meta ({META_PESO}kg)", f"{peso_ideal_total:,.2f} kg".replace(",", "X").replace(".", ",").replace("X", "."))
    k3.metric("Diferença", f"{diferenca_peso:,.2f} kg".replace(",", "X").replace(".", ",").replace("X", "."), delta_color="inverse")

    # ==============================================================================
    # GRÁFICO DE PESO (ESTILO IMAGEM - LINHA + MÉDIA)
    # ==============================================================================
    st.markdown("---")
    
    # 1. Preparação dos dados para o peso
    df_peso_mes_novo = df_filtrado.groupby(pd.Grouper(key="data", freq="ME"))["peso"].sum().reset_index().sort_values("data")
    
    # Formatação de data estilo imagem (jan.25, fev.25)
    df_peso_mes_novo["mes_fmt"] = df_peso_mes_novo["data"].apply(formata_mes_abrev_ano)
    
    # Cálculo da média geral mensal do peso real
    media_peso_ref = df_peso_mes_novo["peso"].mean()
    df_peso_mes_novo["media_ref_val"] = media_peso_ref

    # 2. Construção do Gráfico
    fig_peso_novo = go.Figure()

    # Linha Azul (Total Peso Real Mensal)
    fig_peso_novo.add_trace(go.Scatter(
        x=df_peso_mes_novo["mes_fmt"],
        y=df_peso_mes_novo["peso"],
        mode='lines+markers+text',
        name='Total Peso Real',
        line=dict(color='#1f618d', width=3),
        marker=dict(size=8, color='#1f618d'),
        text=df_peso_mes_novo["peso"].astype(int),
        textposition="top center",
        textfont=dict(color='#1f618d', family="Arial Black")
    ))

    # Linha Laranja (Média Geral de Peso Real)
    fig_peso_novo.add_trace(go.Scatter(
        x=df_peso_mes_novo["mes_fmt"],
        y=df_peso_mes_novo["media_ref_val"],
        mode='lines+markers+text',
        name='Média do Período',
        line=dict(color='#E65100', width=3),
        marker=dict(size=8, color='#E65100'),
        text=df_peso_mes_novo["media_ref_val"].astype(int),
        textposition="bottom center",
        textfont=dict(color='#E65100', family="Arial Black")
    ))

    # 3. Ajustes de Layout
    fig_peso_novo.update_layout(
        title=dict(text="<b>TOTAL PESO MÊS (Comparativo Real vs Média)</b>", x=0.5, xanchor='center'),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(t=60, b=30, l=20, r=20)
    )
    fig_peso_novo.update_yaxes(showgrid=False, showticklabels=False, zeroline=False, title=None)
    fig_peso_novo.update_xaxes(showgrid=False, zeroline=False, title=None, type='category')

    st.plotly_chart(fig_peso_novo, use_container_width=True)
    # ==============================================================================

    st.markdown("---")
    st.subheader("Comparativo Mensal (Real vs Meta)")
    mensal = df_filtrado.groupby(pd.Grouper(key="data", freq="ME")).agg(
        peso_real=("peso", "sum"), qtd=("bombonas", "sum")
    ).reset_index().sort_values("data")
    
    mensal["peso_ideal"] = mensal["qtd"] * META_PESO
    mensal["mes_str"] = mensal["data"].apply(formata_mes)

    fig_peso = px.bar(mensal, x="mes_str", y="peso_real", text="peso_real", title="Real vs Meta", color_discrete_sequence=["#0083B8"])
    fig_peso.add_scatter(x=mensal["mes_str"], y=mensal["peso_ideal"], mode='lines+markers+text', 
                         name='Meta', line=dict(color='#E63946', width=3), text=mensal["peso_ideal"], textposition="top center")
    
    fig_peso.update_traces(texttemplate='<b>%{text:.0f}</b>', textposition='outside', selector=dict(type='bar'))
    fig_peso.update_traces(texttemplate='<b>%{text:.0f}</b>', selector=dict(type='scatter'))
    fig_peso.update_layout(yaxis_title=None, xaxis_title=None, plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_peso, use_container_width=True)

    st.markdown("---")
    st.subheader("🔎 Detalhamento dos Indicadores")

    df_peso_analise = df_filtrado.groupby(pd.Grouper(key="data", freq="ME")).agg(
        total_peso=("peso", "sum"),
        total_bombonas=("bombonas", "sum"),
        dias_unicos=("data", "nunique")
    ).reset_index().sort_values("data")

    df_peso_analise["mes_str"] = df_peso_analise["data"].apply(formata_mes)
    df_peso_analise["peso_ideal"] = df_peso_analise["total_bombonas"] * META_PESO
    df_peso_analise["media_peso_dia"] = df_peso_analise["total_peso"] / df_peso_analise["dias_unicos"]
    df_peso_analise["dif_real_vs_ideal_mes"] = df_peso_analise["total_peso"] - df_peso_analise["peso_ideal"]
    df_peso_analise["dif_real_vs_ideal_dia"] = df_peso_analise["dif_real_vs_ideal_mes"] / df_peso_analise["dias_unicos"]

    COR_BARRA = ["#FFC300"] 

    row1_c1, row1_c2 = st.columns(2)
    with row1_c1:
        fig1 = px.bar(df_peso_analise, x="mes_str", y="total_peso", text="total_peso", title="TOTAL PESO MÊS", color_discrete_sequence=COR_BARRA)
        fig1.update_traces(textposition='outside', texttemplate='<b>%{text:.0f}</b>')
        fig1.update_layout(yaxis_title=None, xaxis_title=None, plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig1, use_container_width=True)
    with row1_c2:
        fig2 = px.bar(df_peso_analise, x="mes_str", y="media_peso_dia", text="media_peso_dia", title="MÉDIA PESO DIA", color_discrete_sequence=COR_BARRA)
        fig2.update_traces(textposition='outside', texttemplate='<b>%{text:.0f}</b>')
        fig2.update_layout(yaxis_title=None, xaxis_title=None, plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig2, use_container_width=True)

    row2_c1, row2_c2 = st.columns(2)
    with row2_c1:
        fig3 = px.bar(df_peso_analise, x="mes_str", y="dif_real_vs_ideal_mes", text="dif_real_vs_ideal_mes", title="DIF. PESO REAL VS IDEAL (MÊS)", color_discrete_sequence=COR_BARRA)
        fig3.update_traces(textposition='outside', texttemplate='<b>%{text:.0f}</b>')
        fig3.update_layout(yaxis_title=None, xaxis_title=None, plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig3, use_container_width=True)
    with row2_c2:
        fig4 = px.bar(df_peso_analise, x="mes_str", y="dif_real_vs_ideal_dia", text="dif_real_vs_ideal_dia", title="DIF. PESO REAL VS IDEAL (DIA)", color_discrete_sequence=COR_BARRA)
        fig4.update_traces(textposition='outside', texttemplate='<b>%{text:.0f}</b>')
        fig4.update_layout(yaxis_title=None, xaxis_title=None, plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig4, use_container_width=True)

    # ==============================================================================
    # ADIÇÃO: NOVOS GRÁFICOS DE PESO (GRUPO E LOCAL)
    # ==============================================================================
    st.markdown("---")
    st.subheader("📊 Distribuição de Peso (Grupo e Local)")
    
    col_g, col_l = st.columns(2)
    
    with col_g:
        # Peso por Grupo
        peso_por_grupo = df_filtrado.groupby("grupo")["peso"].sum().reset_index().sort_values("peso", ascending=False)
        fig_pg = px.bar(peso_por_grupo, x="grupo", y="peso", text="peso", 
                        title="PESO POR GRUPO", color_discrete_sequence=["#FF9F1C"])
        fig_pg.update_traces(textposition='outside', texttemplate='<b>%{text:,.0f}</b>')
        fig_pg.update_layout(yaxis_title=None, xaxis_title=None, plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_pg, use_container_width=True)

    with col_l:
        # Peso por Local
        peso_por_local = df_filtrado.groupby("local")["peso"].sum().reset_index().sort_values("peso", ascending=False)
        # Opcional: Pegar top 10 se houver muitos locais
        peso_por_local = peso_por_local.head(10) 
        fig_pl = px.bar(peso_por_local, x="local", y="peso", text="peso", 
                        title="PESO POR LOCAL", # <--- ALTERADO AQUI
                        color_discrete_sequence=["#2A9D8F"])
        fig_pl.update_traces(textposition='outside', texttemplate='<b>%{text:,.0f}</b>')
        fig_pl.update_layout(yaxis_title=None, xaxis_title=None, plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_pl, use_container_width=True)
    # ==============================================================================


# --- BOMBONAS ---
elif st.session_state.pagina_atual == 'Bombonas':
    st.title("🛢️ Análise de Bombonas")
    st.markdown("---")

    k1, k2 = st.columns(2)
    k1.metric("Total", int(total_bombonas))
    media = total_bombonas / df_filtrado["data"].nunique()
    k2.metric("Média/Dia", f"{media:.1f}")

    # ==============================================================================
    # GRÁFICO ESTILO IMAGEM (TOTAL BOMBONAS MES - LINHAS COMBINADAS)
    # ==============================================================================
    st.markdown("---")
    
    # 1. Preparação dos dados
    df_new_chart = df_filtrado.groupby(pd.Grouper(key="data", freq="ME"))["bombonas"].sum().reset_index().sort_values("data")
    
    # Formatação de data estilo imagem (jan.25, fev.25)
    df_new_chart["mes_fmt"] = df_new_chart["data"].apply(formata_mes_abrev_ano)
    
    # Cálculo da média geral do período filtrado (para a linha laranja)
    media_ref = df_new_chart["bombonas"].mean()
    df_new_chart["media_ref_val"] = media_ref

    # 2. Construção do Gráfico
    fig_new = go.Figure()

    # Linha Azul (Total do Mês)
    fig_new.add_trace(go.Scatter(
        x=df_new_chart["mes_fmt"],
        y=df_new_chart["bombonas"],
        mode='lines+markers+text',
        name='Total Mês',
        line=dict(color='#1f618d', width=3),
        marker=dict(size=8, color='#1f618d'),
        text=df_new_chart["bombonas"],
        textposition="top center",
        textfont=dict(color='#1f618d', family="Arial Black")
    ))

    # Linha Laranja (Média Referência)
    fig_new.add_trace(go.Scatter(
        x=df_new_chart["mes_fmt"],
        y=df_new_chart["media_ref_val"],
        mode='lines+markers+text',
        name='Média do Período',
        line=dict(color='#E65100', width=3),
        marker=dict(size=8, color='#E65100'),
        text=df_new_chart["media_ref_val"].astype(int),
        textposition="bottom center",
        textfont=dict(color='#E65100', family="Arial Black")
    ))

    # 3. Ajustes de Layout
    fig_new.update_layout(
        title=dict(text="<b>TOTAL BOMBONAS MES (Comparativo)</b>", x=0.5, xanchor='center'),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(t=50, b=20, l=20, r=20)
    )
    fig_new.update_yaxes(showgrid=False, showticklabels=False, zeroline=False, title=None)
    fig_new.update_xaxes(showgrid=False, zeroline=False, title=None, type='category')

    st.plotly_chart(fig_new, use_container_width=True)
    # ==============================================================================
    

    st.markdown("---")
    st.markdown("### 📊 Evolução Mensal (Barras)") 
    df_bombonas_mes = df_filtrado.groupby(pd.Grouper(key="data", freq="ME"))["bombonas"].sum().reset_index().sort_values("data")
    df_bombonas_mes["mes_str"] = df_bombonas_mes["data"].apply(formata_mes)

    fig_total_mes = px.bar(df_bombonas_mes, x="mes_str", y="bombonas", text="bombonas", 
                           title="TOTAL BOMBONAS MÊS", color_discrete_sequence=["#1f618d"]) 
    fig_total_mes.update_traces(textposition='outside', texttemplate='<b>%{text}</b>')
    fig_total_mes.update_layout(yaxis_title=None, xaxis_title=None, plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_total_mes, use_container_width=True)
    st.markdown("---")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Por Grupo")
        g_grupo = df_filtrado.groupby("grupo")["bombonas"].sum().reset_index()
        fig_grupo = px.bar(g_grupo, x="grupo", y="bombonas", text="bombonas", color_discrete_sequence=["#FF9F1C"])
        fig_grupo.update_traces(textposition='outside', texttemplate='<b>%{text}</b>')
        fig_grupo.update_layout(yaxis_title=None, xaxis_title=None, plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_grupo, use_container_width=True)
    
    with c2:
        st.subheader("Por Local")
        g_local = df_filtrado.groupby("local")["bombonas"].sum().reset_index().sort_values("bombonas", ascending=False).head(10)
        fig_bar = px.bar(g_local, x="local", y="bombonas", text="bombonas", color_discrete_sequence=["#2A9D8F"])
        fig_bar.update_traces(textposition='outside', texttemplate='<b>%{text}</b>')
        fig_bar.update_layout(yaxis_title=None, xaxis_title=None, plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_bar, use_container_width=True)
    
    st.markdown("---")
    st.subheader("📈 Média de Bombonas por Dia (Evolução por Local)")

    df_media_evolucao = df_filtrado.groupby([pd.Grouper(key="data", freq="ME"), "local"]).agg(
        total_bombonas=("bombonas", "sum"),
        dias_unicos=("data", "nunique")
    ).reset_index()

    df_media_evolucao["media_dia"] = df_media_evolucao["total_bombonas"] / df_media_evolucao["dias_unicos"]
    df_media_evolucao["mes_str"] = df_media_evolucao["data"].apply(formata_mes)
    df_media_evolucao = df_media_evolucao.sort_values("data")

    fig_line_media = px.line(
        df_media_evolucao, x="mes_str", y="media_dia", color="local", 
        text="media_dia", markers=True, title="Média Diária por Local"
    )
    fig_line_media.update_traces(textposition="top center", texttemplate="<b>%{text:.2f}</b>")
    fig_line_media.update_layout(yaxis_title=None, xaxis_title=None, plot_bgcolor="rgba(0,0,0,0)", legend_title_text="Local")
    st.plotly_chart(fig_line_media, use_container_width=True)


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
    fin_mes = df_filtrado.groupby(pd.Grouper(key="data", freq="ME"))["bombonas"].sum().reset_index()
    fin_mes["custo"] = fin_mes["bombonas"] * PRECO_ESTIMADO
    fin_mes["mes_str"] = fin_mes["data"].apply(formata_mes)
    
    fig_fin = px.bar(fin_mes, x="mes_str", y="custo", text="custo", title="Custo Mensal Estimado", color_discrete_sequence=["#2ca02c"])
    fig_fin.update_traces(texttemplate='<b>R$ %{text:,.2f}</b>', textposition='outside')
    fig_fin.update_layout(yaxis_title=None, xaxis_title=None, plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_fin, use_container_width=True)
