import streamlit as st
import pandas as pd
import urllib.parse
import plotly.graph_objects as go

# --- URLs das abas ---
sheet_id = "1eVmdyj8Gue7vr10cybJr1Uz0C_Xr6XIw"

url_contato = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=Controle%20de%20contato"
url_reuniao = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRMIUAGf8uZFTGiLwsrlZ4cJ0tnkfOZ0x5ChwankP5SosC3waREpY4h45xibiFrvw/pub?gid=73898366&single=true&output=csv"
url_indicacoes = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRMIUAGf8uZFTGiLwsrlZ4cJ0tnkfOZ0x5ChwankP5SosC3waREpY4h45xibiFrvw/pub?gid=73898366&single=true&output=csv"


# --- Sidebar ---
aba = st.sidebar.selectbox(
    "📂 Selecione a aba do dashboard:",
    ["Contato com Clientes", "Contagem de Reunião", "Contagem de Indicação", "Resumo Funil"]
)

# --- Função para carregar dados limpos ---
@st.cache_data
def carregar_dados(url):
    df = pd.read_csv(url, encoding="utf-8")
    df.columns = df.columns.str.strip()
    return df


# --- ABA 1 ---
if aba == "Contato com Clientes":
    df = pd.read_csv(url_contato)
    df.columns.values[0] = "Código"
    df.columns.values[1] = "Nome"
    df.columns.values[3] = "Farmer"
    df["Primeiro Contato"] = df["Primeiro Contato"].fillna("Vazio")

    st.title("📞 Dashboard de Contato com Clientes")
    st.subheader("Clique em cada fase para visualizar os clientes")

    status_unicos = df["Primeiro Contato"].unique()
    for status in sorted(status_unicos):
        clientes_status = df[df["Primeiro Contato"] == status][["Código", "Nome", "Farmer"]]
        contagem = len(clientes_status)

        with st.expander(f"{status} – {contagem} cliente(s)", expanded=False):
            st.dataframe(clientes_status, use_container_width=True)

    st.markdown("---")
    st.metric(label="📊 Total Geral de Clientes", value=len(df))

# --- ABA 2 ---
elif aba == "Contagem de Reunião":
    df_reuniao = pd.read_csv(url_reuniao, encoding="utf-8")
    df_reuniao.columns.values[0] = "Código"
    df_reuniao.columns.values[1] = "Nome"
    df_reuniao.columns.values[3] = "Farmer"
    df_reuniao.columns.values[9] = "Aconteceu"

    # Preencher vazios com "Vazio" para consistência
    df_reuniao["Aconteceu"] = df_reuniao["Aconteceu"].str.strip().str.capitalize()
    df_reuniao["Farmer"] = df_reuniao["Farmer"].fillna("Não informado")

    # Tabela dinâmica: contagem por Farmer e Aconteceu (Sim/Não)
    tabela = pd.pivot_table(df_reuniao,
                            index="Farmer",
                            columns="Aconteceu",
                            values="Código",
                            aggfunc="count",
                            fill_value=0).reset_index()

    # Calcular total por linha
    tabela["Total Geral"] = tabela.get("Sim", 0) + tabela.get("Não", 0)

    # Ordenar pela quantidade de reuniões "Sim"
    tabela = tabela.sort_values(by="Sim", ascending=False)

    st.title("📅 Dashboard de Reuniões")
    st.subheader("📋 Contagem de Reuniões por Farmer")

    st.dataframe(tabela, use_container_width=True)

    st.subheader("🔍 Detalhes por Farmer")
    for _, row in tabela.iterrows():
        nome_farmer = row["Farmer"]
        clientes = df_reuniao[df_reuniao["Farmer"] == nome_farmer][["Código", "Nome", "Aconteceu"]]
        with st.expander(f"{nome_farmer} – {len(clientes)} cliente(s)", expanded=False):
            st.dataframe(clientes, use_container_width=True)

    # Total geral final
    total_geral = len(df_reuniao)
    st.markdown("---")
    st.metric("📊 Total Geral de Reuniões Registradas", total_geral)

# --- ABA 3 ---
elif aba == "Contagem de Indicação":
    # Se já carregou df_reuniao antes, pode reutilizar
    if 'df_reuniao' not in locals():
        df_reuniao = pd.read_csv(url_reuniao, encoding="utf-8")

    df_reuniao.columns.values[0] = "Código"
    df_reuniao.columns.values[1] = "Nome"
    df_reuniao.columns.values[3] = "Farmer"
    df_reuniao.columns.values[12] = "Indicação"  # Coluna M = índice 12

    df_reuniao["Indicação"] = df_reuniao["Indicação"].fillna("Vazio").str.strip().str.capitalize()
    df_reuniao["Farmer"] = df_reuniao["Farmer"].fillna("Não informado")

    tabela_indicacao = pd.pivot_table(
        df_reuniao,
        index="Farmer",
        columns="Indicação",
        values="Código",
        aggfunc="count",
        fill_value=0
    ).reset_index()

    # Garante que todas as colunas existam
    for col in ["Sim", "Não", "Vão indicar"]:
        if col not in tabela_indicacao.columns:
            tabela_indicacao[col] = 0

    tabela_indicacao["Total Geral"] = (
        tabela_indicacao["Sim"] + tabela_indicacao["Não"] + tabela_indicacao["Vão indicar"]
    )

    tabela_indicacao = tabela_indicacao.sort_values(by="Total Geral", ascending=False)

    # Ordena a tabela
    tabela_indicacao = tabela_indicacao.sort_values(by="Total Geral", ascending=False)

    # Adiciona a linha de Total Geral na tabela
    total_row = pd.DataFrame({
        "Farmer": ["Total geral"],
        "Sim": [tabela_indicacao["Sim"].sum()],
        "Não": [tabela_indicacao["Não"].sum()],
        "Vão indicar": [tabela_indicacao["Vão indicar"].sum()],
        "Total Geral": [tabela_indicacao["Total Geral"].sum()]
    })

    tabela_indicacao = pd.concat([tabela_indicacao, total_row], ignore_index=True)

    # Exibe a tabela com total na última linha
    st.title("🤝 Dashboard de Indicações")
    st.subheader("📋 Contagem de Indicações por Farmer")
    st.dataframe(tabela_indicacao, use_container_width=True)

    st.subheader("🔍 Detalhes por Farmer")
    for _, row in tabela_indicacao.iterrows():
        nome_farmer = row["Farmer"]
        clientes = df_reuniao[df_reuniao["Farmer"] == nome_farmer][["Código", "Nome", "Indicação"]]
        with st.expander(f"{nome_farmer} – {len(clientes)} cliente(s)", expanded=False):
            st.dataframe(clientes, use_container_width=True)


    # --- Lista de indicações feitas pelos clientes ---
    st.markdown("---")

    url_lista = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRMIUAGf8uZFTGiLwsrlZ4cJ0tnkfOZ0x5ChwankP5SosC3waREpY4h45xibiFrvw/pub?gid=779895520&single=true&output=csv"

    # Lê os dados da aba publicada
    df_lista = pd.read_csv(url_lista, encoding="utf-8")

    # Limpa espaços dos nomes de colunas
    df_lista.columns = df_lista.columns.str.strip()

    # 🔍 Remove linhas onde o nome do cliente está vazio ou nulo
    df_lista = df_lista[df_lista["CLIENTE"].notna()]
    df_lista = df_lista[df_lista["CLIENTE"].astype(str).str.strip() != ""]

    # Converte a coluna de quantidade para número
    df_lista["Quantidade de indicação"] = (
        df_lista["Quantidade de indicação"]
        .astype(str)
        .str.replace(",", ".")
        .str.strip()
    )

    df_lista["Quantidade de indicação"] = pd.to_numeric(df_lista["Quantidade de indicação"], errors="coerce").fillna(0)

    # Ordena pela quantidade de indicações
    df_lista = df_lista.sort_values(by="Quantidade de indicação", ascending=False)

    # Calcula o total geral
    total_geral = df_lista["Quantidade de indicação"].sum()

    # Cria linha de total
    linha_total = pd.DataFrame({
        "CLIENTE": ["Total Geral"],
        "Quantidade de indicação": [total_geral],
        "FARMER": [""]
    })

    # Junta tudo
    df_final = pd.concat([df_lista, linha_total], ignore_index=True)

    # Exibe no dashboard
    st.subheader("📌 Clientes que Indicaram")
    st.dataframe(df_final[["CLIENTE", "Quantidade de indicação", "FARMER"]], use_container_width=True)

# --- ABA 4: Resumo Funil ---
elif aba == "Resumo Funil":
    st.title("📊 Resumo Funil - Visão Geral")

    # --- Contato ---
    df_contato = carregar_dados(url_contato)
    df_contato["Primeiro Contato"] = df_contato["Primeiro Contato"].fillna("Vazio")
    contato_counts = df_contato["Primeiro Contato"].value_counts()
    contato_total = len(df_contato)
    contato_concluido = contato_counts.get("Concluido", 0)
    contato_caixa = contato_counts.get("Caixa postal", 0)
    contato_vazio = contato_counts.get("Vazio", 0)

    # --- Reuniões ---
    df_reuniao = carregar_dados(url_reuniao)
    df_reuniao["Aconteceu"] = df_reuniao["Aconteceu"].str.strip().str.capitalize()
    reuni_total = len(df_reuniao)
    reuni_sim = df_reuniao["Aconteceu"].value_counts().get("Sim", 0)
    reuniao_counts = df_reuniao["Aconteceu"].value_counts()
    reuni_nao = reuniao_counts.get("Não", 0)
    nao_topou = reuniao_counts.get("Não topou reunião", 0)


    # --- Indicações (Reuniões) ---
    
    df_indicacao = carregar_dados(url_indicacoes)
    df_indicacao["Indicação"] = df_indicacao["Indicação"].str.strip().str.capitalize()
    indic_total = df_indicacao[df_indicacao["Indicação"].isin(["Sim", "Vão indicar"])]["Cliente"].nunique()
    indic_sim = df_indicacao["Indicação"].value_counts().get("Sim", 0)
    indic_nao = df_indicacao["Indicação"].value_counts().get("Não", 0)
    indic_vao = df_indicacao["Indicação"].value_counts().get("Vão indicar", 0)
    clientes_ativos = df_indicacao[df_indicacao["Indicação"] == "Sim"]["Cliente"].nunique()

    # --- Leads Gerados ---
    url_lista = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRMIUAGf8uZFTGiLwsrlZ4cJ0tnkfOZ0x5ChwankP5SosC3waREpY4h45xibiFrvw/pub?gid=779895520&single=true&output=csv"
    df_lista = carregar_dados(url_lista)
    df_lista.columns = df_lista.columns.str.strip()

    if "Quantidade de indicação" in df_lista.columns and "CLIENTE" in df_lista.columns:
        df_lista = df_lista[df_lista["CLIENTE"].notna()]
        df_lista["Quantidade de indicação"] = (
            df_lista["Quantidade de indicação"]
            .astype(str)
            .str.replace(",", ".")
            .str.strip()
        )
        df_lista["Quantidade de indicação"] = pd.to_numeric(df_lista["Quantidade de indicação"], errors="coerce").fillna(0)
        leads_gerados = int(df_lista["Quantidade de indicação"].sum())
    else:
        leads_gerados = 0

    # --- Funnel Data ---
    labels = [
        "Contato - Total",
        "Contato - Concluído",
        "Contato - Caixa postal",
        "Contato - Vazio",
        "Reuniões - Total",
        "Reuniões - Aconteceram (Sim)",
        "Reuniões - Não aconteceram",
        "Clientes que não toparam reunião",
        "Indicações - Total",
        "Clientes que indicaram",
        "Indicações - Não",
        "Indicações - Vão indicar",
        "Leads gerados"
    ]

    values = [
        contato_total,
        contato_concluido,
        contato_caixa,
        contato_vazio,
        reuni_total,
        reuni_sim,
        reuni_nao,
        nao_topou,
        indic_total,
        clientes_ativos,
        indic_nao,
        indic_vao,
        leads_gerados
    ]

    fig = go.Figure(go.Funnel(
    y=labels,
    x=values,
    textinfo="value+percent initial",
    textposition="inside",
    textfont=dict(
        size=[28] * (len(labels) - 1) + [36],  # aumenta tamanho da última
        color=["black"] * (len(labels) - 1) + ["white"]  # última branca se fundo escuro
    ),
    marker=dict(
        color=["#636EFA", "#00CC96", "#EF553B", "#AB63FA",
               "#FFA15A", "#19D3F3", "#FF6692",
               "#B6E880", "#FF97FF", "#FECB52", "#FF7F50", "#66CDAA", "#2E91E5"]
    )
))


    fig.update_layout(
        margin=dict(l=100, r=100, t=100, b=100),
        width=900,
        height=700,
        font=dict(size=20)
    )

    st.plotly_chart(fig, use_container_width=True)






