# Dashboard Bambole Kids

Dashboard simples em **Streamlit** para análise fictícia de vendas da loja Bambole Kids.

O projeto conecta em um banco **PostgreSQL**, carrega os dados de vendas com `pandas` e apresenta indicadores, gráficos e tabelas para acompanhar faturamento, lucro, produtos vendidos, estoque e sugestão de reposição.

---

## Visão geral

### Principais análises

| Área | O que mostra |
| --- | --- |
| Indicadores | Faturamento total, lucro estimado, itens vendidos e ticket médio |
| Vendas por período | Evolução do faturamento por mês |
| Produtos | Produtos mais vendidos e lucro por produto |
| Categorias | Faturamento por categoria |
| Pagamento | Faturamento por forma de pagamento |
| Estoque | Produtos com menor saída e estoque restante estimado |
| Reposição | Sugestão de compra com orçamento de R$ 3.500,00 |

### Tecnologias usadas

| Tecnologia | Uso |
| --- | --- |
| Python | Linguagem principal |
| Streamlit | Interface do dashboard |
| Pandas | Manipulação e análise dos dados |
| SQLAlchemy | Conexão com o banco |
| PostgreSQL | Base de dados |
| psycopg2 | Driver PostgreSQL |

---

## Banco de dados

### Configuração usada pela aplicação

| Campo | Valor |
| --- | --- |
| SGBD | PostgreSQL |
| Hospedagem local | PostgreSQL local |
| Hospedagem online | Supabase |
| Variável de conexão | `DATABASE_URL` |

> As credenciais do banco não devem ficar no GitHub. A aplicação lê a conexão pela variável `DATABASE_URL`, configurada nos secrets do Streamlit ou nas variáveis de ambiente locais.

### Link do Supabase

Projeto Supabase: `COLE_AQUI_O_LINK_PUBLICO_DO_PROJETO_OU_DA_ORGANIZACAO`

> Não coloque a connection string do banco aqui, porque ela contém usuário, senha e host privado de conexão.

---

## Modelo relacional

```mermaid
erDiagram
    CLIENTES ||--o{ VENDAS : realiza
    VENDAS ||--o{ ITENS_VENDA : possui
    PRODUTOS ||--o{ ITENS_VENDA : compoe

    CLIENTES {
        int id_cliente PK
        varchar nome
        varchar bairro
        varchar tipo_cliente
    }

    VENDAS {
        int id_venda PK
        date data_venda
        int id_cliente FK
        varchar forma_pagamento
    }

    PRODUTOS {
        int id_produto PK
        varchar nome_produto
        varchar categoria
        numeric preco_custo
        numeric preco_venda
        int estoque_inicial
    }

    ITENS_VENDA {
        int id_item PK
        int id_venda FK
        int id_produto FK
        int quantidade
        numeric valor_unitario
    }
```

---

## Estrutura das tabelas

### `clientes`

Armazena os dados cadastrais dos clientes.

| Coluna | Tipo | Obrigatório | Chave | Descrição |
| --- | --- | --- | --- | --- |
| `id_cliente` | `integer` | Sim | PK | Identificador único do cliente |
| `nome` | `varchar(100)` | Sim |  | Nome do cliente |
| `bairro` | `varchar(100)` | Sim |  | Bairro do cliente |
| `tipo_cliente` | `varchar(20)` | Sim |  | Classificação do cliente |

---

### `produtos`

Armazena os produtos vendidos pela loja.

| Coluna | Tipo | Obrigatório | Chave | Descrição |
| --- | --- | --- | --- | --- |
| `id_produto` | `integer` | Sim | PK | Identificador único do produto |
| `nome_produto` | `varchar(100)` | Sim |  | Nome do produto |
| `categoria` | `varchar(50)` | Sim |  | Categoria do produto |
| `preco_custo` | `numeric(10,2)` | Sim |  | Custo unitário do produto |
| `preco_venda` | `numeric(10,2)` | Sim |  | Preço padrão de venda |
| `estoque_inicial` | `integer` | Sim |  | Quantidade inicial disponível em estoque |

---

### `vendas`

Armazena o cabeçalho de cada venda.

| Coluna | Tipo | Obrigatório | Chave | Descrição |
| --- | --- | --- | --- | --- |
| `id_venda` | `integer` | Sim | PK | Identificador único da venda |
| `data_venda` | `date` | Sim |  | Data em que a venda ocorreu |
| `id_cliente` | `integer` | Sim | FK | Cliente associado à venda |
| `forma_pagamento` | `varchar(30)` | Sim |  | Forma de pagamento usada |

**Relacionamento**

| Coluna | Referencia |
| --- | --- |
| `id_cliente` | `clientes.id_cliente` |

---

### `itens_venda`

Armazena os produtos vendidos dentro de cada venda.

| Coluna | Tipo | Obrigatório | Chave | Descrição |
| --- | --- | --- | --- | --- |
| `id_item` | `integer` | Sim | PK | Identificador único do item da venda |
| `id_venda` | `integer` | Sim | FK | Venda à qual o item pertence |
| `id_produto` | `integer` | Sim | FK | Produto vendido |
| `quantidade` | `integer` | Sim |  | Quantidade vendida do produto |
| `valor_unitario` | `numeric(10,2)` | Sim |  | Valor unitário aplicado na venda |

**Relacionamentos**

| Coluna | Referencia |
| --- | --- |
| `id_venda` | `vendas.id_venda` |
| `id_produto` | `produtos.id_produto` |

---

## Consulta principal do dashboard

O dashboard cruza as quatro tabelas para montar uma base analítica de vendas:

```sql
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
```

### Campos calculados

| Campo | Cálculo | Uso |
| --- | --- | --- |
| `total_venda` | `quantidade * valor_unitario` | Faturamento |
| `lucro` | `quantidade * (valor_unitario - preco_custo)` | Lucro estimado |
| `estoque_restante` | `estoque_inicial - quantidade_vendida` | Análise de estoque |
| `ticket_medio` | `faturamento_total / total_vendas` | Indicador geral |

---

## Publicação da aplicação

Para o usuário ver a aplicação funcionando, o GitHub sozinho não hospeda o Streamlit. O fluxo recomendado é:

1. Subir este projeto para um repositório no GitHub.
2. Criar um app no Streamlit Community Cloud apontando para o arquivo `app.py`.
3. Configurar o secret `DATABASE_URL` no painel do Streamlit.
4. Usar a connection string do Supabase como valor desse secret.

Exemplo de secret:

```toml
DATABASE_URL = "postgresql+psycopg2://USUARIO:SENHA@HOST:PORTA/BANCO"
```

Depois do deploy, o Streamlit gera um link público no formato `https://nome-do-app.streamlit.app`.

---

## Como executar

Configure a variável `DATABASE_URL` localmente:

```powershell
$env:DATABASE_URL="postgresql+psycopg2://USUARIO:SENHA@HOST:PORTA/BANCO"
```

Depois, ative o ambiente virtual e rode a aplicação:

```powershell
.\venv\Scripts\Activate.ps1
streamlit run app.py
```

Depois, acesse o endereço exibido pelo Streamlit no navegador.

---

## Estrutura do projeto

```text
bambole_kids_dashboard/
|-- .streamlit/
|   `-- secrets.toml.example
|-- .gitignore
|-- app.py
|-- README.md
|-- requirements.txt
`-- venv/
```

---

## Observações

- A base é relacional e segue o padrão clássico de vendas: clientes, vendas, produtos e itens da venda.
- A tabela `vendas` representa a transação.
- A tabela `itens_venda` permite que uma mesma venda tenha vários produtos.
- O dashboard trabalha com dados já existentes no PostgreSQL; ele não cria tabelas nem insere dados.
