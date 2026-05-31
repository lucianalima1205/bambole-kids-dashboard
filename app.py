import pandas as pd
import streamlit as st
import os
from sqlalchemy import create_engine


st.set_page_config(
    page_title="Dashboard Bambole Kids",
    layout="wide"
)


# ==============================
# CONEXÃO COM O BANCO
# ==============================

def obter_database_url():
    database_url = os.getenv("DATABASE_URL")

    try:
        database_url = st.secrets.get("DATABASE_URL", database_url)
    except FileNotFoundError:
        pass

    if database_url:
        return database_url

    st.error(
        "Conexao com o banco nao configurada. "
        "Defina DATABASE_URL nos secrets do Streamlit ou nas variaveis de ambiente."
    )
    st.stop()


engine = create_engine(obter_database_url())


# ==============================
# CARREGAMENTO DOS DADOS
# ==============================

@st.cache_data
def carregar_dados():
    query = """
    SELECT 
        v.id_venda,
        v.data_venda,
        c.nome AS cliente,
        c.bairro,
        c.tipo_cliente,
        v.forma_pagamento,
        p.nome_produto,
        p.categoria,
        p.preco_custo,
        p.preco_venda,
        p.estoque_inicial,
        i.quantidade,
        i.valor_unitario,
        (i.quantidade * i.valor_unitario) AS total_venda,
        (i.quantidade * (i.valor_unitario - p.preco_custo)) AS lucro
    FROM itens_venda i
    JOIN vendas v ON i.id_venda = v.id_venda
    JOIN clientes c ON v.id_cliente = c.id_cliente
    JOIN produtos p ON i.id_produto = p.id_produto
    ORDER BY v.data_venda;
    """

    df = pd.read_sql(query, engine)
    df["data_venda"] = pd.to_datetime(df["data_venda"])
    return df


df = carregar_dados()


# ==============================
# COLUNAS AUXILIARES DE DATA
# ==============================

MESES_PT_BR = {
    1: "Janeiro",
    2: "Fevereiro",
    3: "Março",
    4: "Abril",
    5: "Maio",
    6: "Junho",
    7: "Julho",
    8: "Agosto",
    9: "Setembro",
    10: "Outubro",
    11: "Novembro",
    12: "Dezembro"
}

df["ano"] = df["data_venda"].dt.year
df["mes_numero"] = df["data_venda"].dt.month
df["mes_nome"] = df["mes_numero"].map(MESES_PT_BR)
df["mes_ano"] = df["mes_nome"] + "/" + df["ano"].astype(str)
df["ordem_mes_ano"] = df["ano"] * 100 + df["mes_numero"]


# ==============================
# TÍTULO
# ==============================

st.title("Dashboard de Vendas - Bambole Kids")
st.write("Análise fictícia de vendas, estoque e comportamento de clientes.")


# ==============================
# FILTROS
# ==============================

st.sidebar.header("Filtros")

anos = st.sidebar.multiselect(
    "Ano",
    options=sorted(df["ano"].unique()),
    default=sorted(df["ano"].unique())
)

meses_disponiveis = (
    df[["mes_numero", "mes_nome"]]
    .drop_duplicates()
    .sort_values("mes_numero")
)

meses = st.sidebar.multiselect(
    "Mês",
    options=meses_disponiveis["mes_nome"].tolist(),
    default=meses_disponiveis["mes_nome"].tolist()
)

categorias = st.sidebar.multiselect(
    "Categoria",
    options=sorted(df["categoria"].unique()),
    default=sorted(df["categoria"].unique())
)

formas_pagamento = st.sidebar.multiselect(
    "Forma de pagamento",
    options=sorted(df["forma_pagamento"].unique()),
    default=sorted(df["forma_pagamento"].unique())
)

tipo_cliente = st.sidebar.multiselect(
    "Tipo de cliente",
    options=sorted(df["tipo_cliente"].unique()),
    default=sorted(df["tipo_cliente"].unique())
)


df_filtrado = df[
    (df["ano"].isin(anos)) &
    (df["mes_nome"].isin(meses)) &
    (df["categoria"].isin(categorias)) &
    (df["forma_pagamento"].isin(formas_pagamento)) &
    (df["tipo_cliente"].isin(tipo_cliente))
]


# ==============================
# CASO NÃO TENHA DADOS
# ==============================

if df_filtrado.empty:
    st.warning("Nenhum dado encontrado para os filtros selecionados.")
    st.stop()


# ==============================
# INDICADORES PRINCIPAIS
# ==============================

faturamento_total = df_filtrado["total_venda"].sum()
lucro_total = df_filtrado["lucro"].sum()
itens_vendidos = df_filtrado["quantidade"].sum()
total_vendas = df_filtrado["id_venda"].nunique()

ticket_medio = faturamento_total / total_vendas if total_vendas > 0 else 0


col1, col2, col3, col4 = st.columns(4)

col1.metric("Faturamento Total", f"R$ {faturamento_total:,.2f}")
col2.metric("Lucro Estimado", f"R$ {lucro_total:,.2f}")
col3.metric("Itens Vendidos", int(itens_vendidos))
col4.metric("Ticket Médio", f"R$ {ticket_medio:,.2f}")

st.divider()


# ==============================
# FATURAMENTO POR MÊS
# ==============================

st.subheader("Faturamento por Mês")

faturamento_mes = (
    df_filtrado.groupby(["ordem_mes_ano", "mes_ano"])["total_venda"]
    .sum()
    .reset_index()
    .sort_values("ordem_mes_ano")
)

faturamento_mes_grafico = faturamento_mes.set_index("mes_ano")["total_venda"]

st.line_chart(faturamento_mes_grafico)

st.divider()


# ==============================
# GRÁFICOS PRINCIPAIS
# ==============================

col_graf1, col_graf2 = st.columns(2)

with col_graf1:
    st.subheader("Faturamento por Categoria")

    faturamento_categoria = (
        df_filtrado.groupby("categoria")["total_venda"]
        .sum()
        .sort_values(ascending=False)
    )

    st.bar_chart(faturamento_categoria)


with col_graf2:
    st.subheader("Produtos Mais Vendidos")

    produtos_mais_vendidos = (
        df_filtrado.groupby("nome_produto")["quantidade"]
        .sum()
        .sort_values(ascending=False)
    )

    st.bar_chart(produtos_mais_vendidos)


col_graf3, col_graf4 = st.columns(2)

with col_graf3:
    st.subheader("Lucro por Produto")

    lucro_produto = (
        df_filtrado.groupby("nome_produto")["lucro"]
        .sum()
        .sort_values(ascending=False)
    )

    st.bar_chart(lucro_produto)


with col_graf4:
    st.subheader("Faturamento por Forma de Pagamento")

    pagamento = (
        df_filtrado.groupby("forma_pagamento")["total_venda"]
        .sum()
        .sort_values(ascending=False)
    )

    st.bar_chart(pagamento)


st.divider()


# ==============================
# ANÁLISE DE ESTOQUE
# ==============================

st.subheader("Análise de Estoque")

estoque = (
    df_filtrado.groupby(["nome_produto", "categoria", "estoque_inicial"])
    .agg(quantidade_vendida=("quantidade", "sum"))
    .reset_index()
)

estoque["estoque_restante"] = estoque["estoque_inicial"] - estoque["quantidade_vendida"]

produtos_encalhados = estoque.sort_values(
    by=["quantidade_vendida", "estoque_restante"],
    ascending=[True, False]
)

st.write("Produtos com menor saída no período selecionado:")
st.dataframe(produtos_encalhados, use_container_width=True)


# ==============================
# SUGESTÃO DE REPOSIÇÃO
# ==============================

st.subheader("Sugestão de Reposição com Orçamento de R$ 3.500,00")

orcamento = 3500.00

analise_reposicao = (
    df_filtrado.groupby(["nome_produto", "categoria", "preco_custo"])
    .agg(
        quantidade_vendida=("quantidade", "sum"),
        faturamento=("total_venda", "sum"),
        lucro=("lucro", "sum")
    )
    .reset_index()
)

analise_reposicao["prioridade"] = (
    analise_reposicao["quantidade_vendida"] * 0.5 +
    analise_reposicao["lucro"] * 0.03
)

analise_reposicao = analise_reposicao.sort_values(
    by="prioridade",
    ascending=False
)

produtos_reposicao = []
valor_total = 0

for _, produto in analise_reposicao.iterrows():
    preco_custo = float(produto["preco_custo"])

    if valor_total + preco_custo <= orcamento:
        quantidade_sugerida = int((orcamento * 0.15) // preco_custo)

        if quantidade_sugerida < 1:
            quantidade_sugerida = 1

        valor_sugerido = quantidade_sugerida * preco_custo

        if valor_total + valor_sugerido <= orcamento:
            produtos_reposicao.append({
                "Produto": produto["nome_produto"],
                "Categoria": produto["categoria"],
                "Quantidade sugerida": quantidade_sugerida,
                "Custo unitário": preco_custo,
                "Valor sugerido": valor_sugerido
            })

            valor_total += valor_sugerido

reposicao_df = pd.DataFrame(produtos_reposicao)

st.dataframe(reposicao_df, use_container_width=True)

st.metric("Total sugerido para reposição", f"R$ {valor_total:,.2f}")
st.metric("Saldo restante do orçamento", f"R$ {orcamento - valor_total:,.2f}")


st.divider()


# ==============================
# BASE DE DADOS
# ==============================

st.subheader("Base de Dados das Vendas")

colunas_exibicao = [
    "id_venda",
    "data_venda",
    "ano",
    "mes_nome",
    "cliente",
    "bairro",
    "tipo_cliente",
    "forma_pagamento",
    "nome_produto",
    "categoria",
    "quantidade",
    "valor_unitario",
    "total_venda",
    "lucro"
]

st.dataframe(df_filtrado[colunas_exibicao], use_container_width=True)
