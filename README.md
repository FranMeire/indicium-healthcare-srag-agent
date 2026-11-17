# Indicium HealthCare Inc. — Agente de Inteligência Epidemiológica (SRAG)

Prova de Conceito (PoC) desenvolvida para a **Certificação Artificial Intelligence Engineer by Indicium AI**. A solução implementa um agente autônomo baseado em **LangGraph** capaz de consultar microdados reais de internações por Síndrome Respiratória Aguda Grave (SRAG) do **Open DATASUS**, calcular indicadores epidemiológicos críticos, gerar visualizações temporais e cruzar os números com notícias recentes em tempo real.

---

## Arquitetura da Solução

O diagrama conceitual completo está disponível em [`docs/arquitetura.pdf`](docs/arquitetura.pdf).

* **Orquestrador (`src/agent/graph.py`):** Agente ReAct construído com **LangGraph** que coordena o planejamento e a execução das ferramentas.
* **LLM (`Ollama / Llama 3.2`):** Modelo de linguagem responsável por interpretar os dados estruturados, sintetizar notícias e redigir o relatório técnico.
* **Ferramentas (`src/tools/`):**
  1. `get_srag_metrics`: Executa consultas SQL no banco **SQLite** para calcular as 4 métricas obrigatórias.
  2. `generate_srag_charts`: Gera os gráficos diário (últimos 30 dias) e mensal (últimos 12 meses) com **Matplotlib/Seaborn**.
  3. `search_srag_news`: Consulta notícias e boletins epidemiológicos recentes via **Tavily Search API**.

---

## Tratamento de Dados e Conformidade (LGPD)

Os microdados brutos (`INFLUD25`, 165.397 registros válidos) foram processados pelo pipeline [`src/etl/preprocess.py`](src/etl/preprocess.py) seguindo o Dicionário de Dados oficial do SIVEP-Gripe ([`docs/Dicionario_de_Dados_SRAG_Hospitalizado_19.09.2022.pdf`](docs/Dicionario_de_Dados_SRAG_Hospitalizado_19.09.2022.pdf)):

* **Anonimização (Dados Sensíveis):** Exclusão na ingestão de colunas identificáveis (CPF, nome do paciente, nome da mãe, CEP, telefone e data de nascimento exata).
* **Tratamento de Códigos Ignorados:** Valores preenchidos com código `9` ("Ignorado" no dicionário DATASUS) foram convertidos para `NaN` e excluídos dos denominadores para evitar distorções nas taxas de mortalidade, UTI e vacinação.
* **Definição das Métricas:**
  * **Taxa de aumento de casos:** Variação percentual entre os últimos 30 dias da base e os 30 dias imediatamente anteriores.
  * **Taxa de mortalidade:** Óbitos por SRAG (`EVOLUCAO = 2`) divididos pelo total de casos com desfecho conhecido (`EVOLUCAO IN (1, 2, 3)`).
  * **Taxa de ocupação de UTI:** Internados em UTI (`UTI = 1`) divididos pelo total de registros válidos (`UTI IN (1, 2)`).
  * **Taxa de vacinação:** Pacientes imunizados contra Influenza (`VACINA = 1`) ou COVID-19 (`VACINA_COV = 1`) entre os registros com status vacinal válido.

---

## Governança, Transparência e Guardrails

* **Guardrails de Entrada e Saída (`src/agent/guardrails.py`):** Validação contra *prompt injection* ou tentativas de consulta de dados pessoais (LGPD) na entrada, além da inserção obrigatória de aviso de governança clínica na saída.
* **Auditoria (`outputs/audit_log.jsonl`):** Registro estruturado em JSONL com *timestamp* de todas as validações, ferramentas acionadas pelo agente e artefatos gerados.

---

## Estrutura do Projeto

```text
indicium-healthcare-srag-agent/
├── data/
│   ├── raw/                  # CSV original do Open DATASUS (ignorado no Git)
│   └── processed/            # Banco SQLite tratado (ignorado no Git)
├── docs/
│   ├── arquitetura.pdf       # Diagrama conceitual da arquitetura
│   └── Dicionario_de_Dados_SRAG_Hospitalizado_19.09.2022.pdf
├── outputs/
│   ├── charts/               # Gráficos gerados (30 dias e 12 meses)
│   ├── audit_log.jsonl       # Log de auditoria e governança do agente
│   └── relatorio_srag.md     # Exemplo de relatório gerado automaticamente
├── src/
│   ├── agent/
│   │   ├── graph.py          # Orquestrador LangGraph
│   │   └── guardrails.py     # Guardrails e auditoria
│   ├── etl/
│   │   └── preprocess.py     # Pipeline ETL e anonimização LGPD
│   ├── tools/
│   │   ├── charts_tool.py    # Geração dos 2 gráficos
│   │   ├── metrics_tool.py   # Cálculo das 4 métricas via SQL
│   │   └── news_tool.py      # Busca de notícias em tempo real
│   └── main.py               # Ponto de entrada
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Como Executar

1. **Clonar o repositório e instalar dependências:**
   ```bash
   git clone https://github.com
   cd indicium-healthcare-srag-agent
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. **Configurar variáveis e modelo local:**
   * Copie `.env.example` para `.env` e adicione sua `TAVILY_API_KEY`.
   * Certifique-se de ter o **Ollama** rodando localmente com o modelo `llama3.2` (`ollama pull llama3.2`).
3. **Executar o ETL e o Agente:**
   ```bash
   python src/etl/preprocess.py
   python -m src.main
   ```
