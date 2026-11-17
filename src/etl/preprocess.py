import glob
import os
import sqlite3
import numpy as np
import pandas as pd

SELECTED_COLUMNS = [
    "DT_NOTIFIC",
    "DT_SIN_PRI",
    "SG_UF_NOT",
    "CS_SEXO",
    "NU_IDADE_N",
    "TP_IDADE",
    "UTI",
    "EVOLUCAO",
    "VACINA",
    "VACINA_COV",
    "CLASSI_FIN",
]


def load_raw_csvs(raw_dir: str = "data/raw") -> pd.DataFrame:
    """Lê os arquivos CSV de SRAG detectando automaticamente o separador (; ou ,)."""
    csv_files = glob.glob(os.path.join(raw_dir, "*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"Nenhum arquivo CSV encontrado em {raw_dir}")

    dfs = []
    for file in csv_files:
        print(f"Lendo arquivo: {file}...")
        with open(file, "r", encoding="latin1") as f:
            header = f.readline()
        sep = ";" if header.count(";") > header.count(",") else ","

        df = pd.read_csv(
            file,
            sep=sep,
            encoding="latin1",
            usecols=lambda col: col.strip().upper() in SELECTED_COLUMNS,
            low_memory=False,
        )
        df.columns = [c.strip().upper() for c in df.columns]
        dfs.append(df)

    return pd.concat(dfs, ignore_index=True)


def clean_and_transform(df: pd.DataFrame) -> pd.DataFrame:
    """Padroniza datas automaticamente e trata valores ignorados (código 9 -> NaN)."""
    df = df.copy()

    for date_col in ["DT_NOTIFIC", "DT_SIN_PRI"]:
        if date_col in df.columns:
            # Tenta primeiro YYYY-MM-DD; se falhar, tenta DD/MM/YYYY
            parsed = pd.to_datetime(df[date_col], format="%Y-%m-%d", errors="coerce")
            if parsed.isna().all():
                parsed = pd.to_datetime(df[date_col], format="%d/%m/%Y", errors="coerce")
            df[date_col] = parsed

    df = df.dropna(subset=["DT_NOTIFIC"])

    categorical_cols = ["UTI", "EVOLUCAO", "VACINA", "VACINA_COV", "CLASSI_FIN"]
    for col in categorical_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df[col] = df[col].replace(9, np.nan)

    df["VACINADO_GERAL"] = np.where(
        (df["VACINA"] == 1) | (df["VACINA_COV"] == 1),
        1,
        np.where((df["VACINA"] == 2) & (df["VACINA_COV"] == 2), 0, np.nan),
    )

    df = df.sort_values("DT_NOTIFIC").reset_index(drop=True)
    df["DT_NOTIFIC"] = df["DT_NOTIFIC"].dt.strftime("%Y-%m-%d")
    if "DT_SIN_PRI" in df.columns:
        df["DT_SIN_PRI"] = df["DT_SIN_PRI"].dt.strftime("%Y-%m-%d")

    return df


def save_to_sqlite(df: pd.DataFrame, db_path: str = "data/processed/srag.db") -> None:
    """Salva o DataFrame limpo em um banco SQLite."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    df.to_sql("srag_casos", conn, if_exists="replace", index=False)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_dt_notific ON srag_casos (DT_NOTIFIC);")
    conn.commit()
    conn.close()
    print(f"Banco SQLite salvo com sucesso em: {db_path} ({len(df)} registros válidos).")


if __name__ == "__main__":
    raw_df = load_raw_csvs("data/raw")
    clean_df = clean_and_transform(raw_df)
    save_to_sqlite(clean_df, "data/processed/srag.db")
