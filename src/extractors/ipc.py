import pandas as pd
from .common import to_float, date_from_yyyymm

CLASSIFICATION_MAP = {
  "Nivel general y divisiones COICOP": "COICOP",
  "Categorias": "categorias",
  "Bienes y servicios": "bienes_servicios"
}

def extract(file_path: str, config: dict) -> tuple[list[dict], str]:
  df = pd.read_csv(file_path, sep=config["separator"], encoding=config["encoding"])
  last_date = config.get("last-date")
  
  records = []
  for _, row in df.iterrows():
    if last_date is None or last_date > row["Periodo"]:
      continue
    
    name = row.get("Descripcion", None)
    classification = CLASSIFICATION_MAP.get(row["Clasificación"])
    date = date_from_yyyymm(row["Periodo"])
    
    records.append({
      "region": row["Region"],
      "clasificacion": classification,
      "codigo": str(row["Codigo"]),
      "nombre": name,
      "periodo": date,
      "indice": to_float(row["Indice_IPC"]),
      "mensual": to_float(row["v_m_IPC"]),
      "interanual": to_float(row["v_i_a_IPC"]),  
    })
  
  return records, last_date