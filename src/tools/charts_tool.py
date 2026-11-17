import os
import sqlite3
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from langchain_core.tools import tool

DB_PATH = "data/processed/srag.db"
CHARTS_DIR = "outputs/charts"


@tool
def generate_srag_charts() -> str:
    """
    Gera os dois gráficos obrigatórios de SRAG (últimos 30 dias diário e últimos 12 meses mensal).
    """
    os.makedirs(CHARTS_DIR, exist_ok=True)
    sns.set_theme(style="whitegrid")

    conn = sqlite3.connect(DB_PATH)
    max_date_str = pd.read_sql("SELECT MAX(DT_NOTIFIC) as max_dt FROM srag_casos;", conn)["max_dt"].iloc[0]
    max_date = datetime.strptime(max_date_str, "%Y-%m-%d")

    # Gráfico 1: Diário dos últimos 30 dias
    dt_30d = (max_date - timedelta(days=30)).strftime("%Y-%m-%d")
    df_30d = pd.read_sql(
        f"""
        SELECT DT_NOTIFIC AS data, COUNT(*) AS casos
        FROM srag_casos
        WHERE DT_NOTIFIC > '{dt_30d}' AND DT_NOTIFIC <= '{max_date_str}'
        GROUP BY DT_NOTIFIC
        ORDER BY DT_NOTIFIC;
        """,
        conn,
    )

    plt.figure(figsize=(10, 4.5))
    sns.lineplot(data=df_30d, x="data", y="casos", marker="o", color="#1f77b4", linewidth=2)
    plt.title(f"Casos Diários de SRAG - Últimos 30 Dias (até {max_date_str})", fontsize=13, fontweight="bold")
    plt.xlabel("Data de Notificação")
    plt.ylabel("Número de Casos")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    path_30d = os.path.join(CHARTS_DIR, "casos_diarios_30d.png")
    plt.savefig(path_30d, dpi=150)
    plt.close()

    # Gráfico 2: Mensal dos últimos 12 meses
    dt_12m = (max_date - timedelta(days=365)).strftime("%Y-%m-%d")
    df_12m = pd.read_sql(
        f"""
        SELECT SUBSTR(DT_NOTIFIC, 1, 7) AS mes, COUNT(*) AS casos
        FROM srag_casos
        WHERE DT_NOTIFIC >= '{dt_12m}' AND DT_NOTIFIC <= '{max_date_str}'
        GROUP BY mes
        ORDER BY mes;
        """,
        conn,
    )

    plt.figure(figsize=(10, 4.5))
    sns.barplot(data=df_12m, x="mes", y="casos", color="#2b5c8f")
    plt.title("Casos Mensais de SRAG - Últimos 12 Meses", fontsize=13, fontweight="bold")
    plt.xlabel("Ano-Mês")
    plt.ylabel("Número de Casos")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    path_12m = os.path.join(CHARTS_DIR, "casos_mensais_12m.png")
    plt.savefig(path_12m, dpi=150)
    plt.close()

    conn.close()
    return f"Gráficos gerados com sucesso: '{path_30d}' e '{path_12m}'."
