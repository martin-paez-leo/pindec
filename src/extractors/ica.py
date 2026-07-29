import pandas as pd
from .common import to_float

_MONTHS = {
  "Enero": "01", "Febrero": "02", "Marzo": "03", "Abril": "04",
  "Mayo": "05", "Junio": "06", "Julio": "07", "Agosto": "08",
  "Septiembre": "09", "Octubre": "10", "Noviembre": "11", "Diciembre": "12"
}

def _build_periodo(row):
  month = _MONTHS.get(str(row["mes"]), "01")
  year = str(row["anio"]).replace("*", "")
  return f"{int(year)}-{month}"

def extract(config: dict) -> tuple[dict, dict]:
  url = config["url"]
  sheet_cfg = config["sheets"][0]
  skiprows = sheet_cfg["skiprows"]
  columns = sheet_cfg["columns"]

  df = pd.read_excel(url, sheet_name="FOB-CIF", header=None)
  df = df.dropna(how="all", axis=1)

  if len(df.columns) != len(columns):
    return [], {"sheets": [{"name": "FOB-CIF", "skiprows": skiprows, "columns": columns}]}

  df.columns = columns
  df["anio"] = df["anio"].ffill()
  df = df.dropna(subset=["mes", "anio"])

  last_index = df.index[-1] + 1

  df = df.loc[skiprows:]

  records = []
  for _, row in df.iterrows():
    records.append({
      "periodo": _build_periodo(row),
      "exportaciones": {
        "mensual": to_float(row["exp_mensual"]),
        "acumulado": to_float(row["exp_acumulado"]),
        "var_interanual_mensual": to_float(row["var_exp_mensual"]),
        "var_interanual_acumulada": to_float(row["var_exp_acumulada"])
      },
      "importaciones": {
        "mensual": to_float(row["imp_mensual"]),
        "acumulado": to_float(row["imp_acumulado"]),
        "var_interanual_mensual": to_float(row["var_imp_mensual"]),
        "var_interanual_acumulada": to_float(row["var_imp_acumulada"])
      },
      "saldo": to_float(row["saldo"])
    })

  new_skiprows = {"sheets": [{"name": "FOB-CIF", "skiprows": last_index, "columns": columns}]}

  return records, new_skiprows