import pandas as pd
from .common import to_float, date_from_yyyymm

CLASSIFICATION_MAP = {
  "Nivel general y divisiones COICOP": "COICOP",
  "Categorias": "categorias",
  "Bienes y servicios": "bienes_servicios"
}

def extract(config: dict) -> tuple[list[dict], str]:
  df = pd.read_csv(config["url"], sep=config["separator"], encoding=config["encoding"])
  last_date = config.get("last-date")
  
  records = []
  for _, row in df.iterrows():
    if last_date is not None and row["Periodo"] <= last_date:
      continue
    
    name = row.get("Descripcion")
    if pd.isna(name):
      name = None
      
    classification = CLASSIFICATION_MAP.get(row["Clasificador"])
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