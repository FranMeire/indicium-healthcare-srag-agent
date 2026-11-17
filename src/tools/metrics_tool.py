import json
import sqlite3
from datetime import datetime, timedelta
from langchain_core.tools import tool

DB_PATH = "data/processed/srag.db"


@tool
def get_srag_metrics() -> str:
    """
    Consulta o banco SQLite de SRAG e calcula as 4 métricas obrigatórias:
    taxa de aumento de casos, taxa de mortalidade, taxa de ocupação de UTI e taxa de vacinação.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT MAX(DT_NOTIFIC) FROM srag_casos;")
    max_date_str = cursor.fetchone()[0]
    max_date = datetime.strptime(max_date_str, "%Y-%m-%d")

    dt_30d_ago = (max_date - timedelta(days=30)).strftime("%Y-%m-%d")
    dt_60d_ago = (max_date - timedelta(days=60)).strftime("%Y-%m-%d")
    dt_12m_ago = (max_date - timedelta(days=365)).strftime("%Y-%m-%d")

    # 1. Taxa de aumento de casos (30 dias atuais vs 30 dias anteriores)
    cursor.execute(
        "SELECT COUNT(*) FROM srag_casos WHERE DT_NOTIFIC > ? AND DT_NOTIFIC <= ?;",
        (dt_30d_ago, max_date_str),
    )
    casos_30d = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM srag_casos WHERE DT_NOTIFIC > ? AND DT_NOTIFIC <= ?;",
        (dt_60d_ago, dt_30d_ago),
    )
    casos_prev_30d = cursor.fetchone()[0]

    taxa_aumento = (
        ((casos_30d - casos_prev_30d) / casos_prev_30d) * 100
        if casos_prev_30d > 0
        else 0.0
    )

    # 2. Taxa de mortalidade (últimos 12 meses)
    cursor.execute(
        """
        SELECT 
            SUM(CASE WHEN EVOLUCAO = 2 THEN 1 ELSE 0 END),
            COUNT(EVOLUCAO)
        FROM srag_casos
        WHERE DT_NOTIFIC >= ? AND EVOLUCAO IN (1, 2, 3);
        """,
        (dt_12m_ago,),
    )
    obitos_srag, total_desfecho = cursor.fetchone()
    taxa_mortalidade = (obitos_srag / total_desfecho) * 100 if total_desfecho else 0.0

    # 3. Taxa de ocupação de UTI (últimos 12 meses)
    cursor.execute(
        """
        SELECT 
            SUM(CASE WHEN UTI = 1 THEN 1 ELSE 0 END),
            COUNT(UTI)
        FROM srag_casos
        WHERE DT_NOTIFIC >= ? AND UTI IN (1, 2);
        """,
        (dt_12m_ago,),
    )
    total_uti, total_valido_uti = cursor.fetchone()
    taxa_uti = (total_uti / total_valido_uti) * 100 if total_valido_uti else 0.0

    # 4. Taxa de vacinação (últimos 12 meses)
    cursor.execute(
        """
        SELECT 
            SUM(CASE WHEN VACINADO_GERAL = 1 THEN 1 ELSE 0 END),
            COUNT(VACINADO_GERAL)
        FROM srag_casos
        WHERE DT_NOTIFIC >= ? AND VACINADO_GERAL IN (0, 1);
        """,
        (dt_12m_ago,),
    )
    total_vac, total_valido_vac = cursor.fetchone()
    taxa_vacinacao = (total_vac / total_valido_vac) * 100 if total_valido_vac else 0.0

    conn.close()

    result = {
        "data_referencia_base": max_date_str,
        "casos_ultimos_30_dias": casos_30d,
        "casos_30_dias_anteriores": casos_prev_30d,
        "taxa_aumento_casos_percentual": round(taxa_aumento, 2),
        "taxa_mortalidade_percentual": round(taxa_mortalidade, 2),
        "taxa_ocupacao_uti_percentual": round(taxa_uti, 2),
        "taxa_vacinacao_percentual": round(taxa_vacinacao, 2),
        "amostra_desfechos_validos_12m": total_desfecho,
        "amostra_uti_validos_12m": total_valido_uti,
        "amostra_vacinacao_validos_12m": total_valido_vac,
    }
    return json.dumps(result, ensure_ascii=False, indent=2)
