import pandas as pd
from .common import to_float, date_from_yyyymm

CLASSIFICATION_MAP = {
  "Nivel general y divisiones COICOP": "COICOP",
  "Categorias": "categorias",
  "Bienes y servicios": "bienes_servicios"
}

def _row_to_record(row):
  name = row.get("Descripcion")
  return {
    "region": row["Region"],
    "clasificacion": CLASSIFICATION_MAP.get(row["Clasificador"]),
    "codigo": str(row["Codigo"]),
    "nombre": None if pd.isna(name) else name,
    "periodo": date_from_yyyymm(row["Periodo"]),
    "indice": to_float(row["Indice_IPC"]),
    "mensual": to_float(row["v_m_IPC"]),
    "interanual": to_float(row["v_i_a_IPC"]),
  }

def extract(config: dict) -> tuple[list[dict], str]:
  df = pd.read_csv(config["url"], sep=config["separator"], encoding=config["encoding"])
  last_date = config.get("last-date")

  if last_date is not None:
    df = df[df["Periodo"] > last_date]

  records = [_row_to_record(row) for _, row in df.iterrows()]

  return records, last_date