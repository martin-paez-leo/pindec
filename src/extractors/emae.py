import pandas as pd
from .common import to_float, MONTHS

_FALLBACK_MONTHS = 3

_SECTORS = {
  "A": "Agricultura, ganadería, caza y silvicultura",
  "B": "Pesca",
  "C": "Explotación de minas y canteras",
  "D": "Industria manufacturera",
  "E": "Electricidad, gas y agua",
  "F": "Construcción",
  "G": "Comercio mayorista, minorista y reparaciones",
  "H": "Hoteles y restaurantes",
  "I": "Transporte y comunicaciones",
  "J": "Intermediación financiera",
  "K": "Actividades inmobiliarias, empresariales y de alquiler",
  "L": "Administración pública y defensa; planes de seguridad social de afiliación obligatoria",
  "M": "Enseñanza",
  "N": "Servicios sociales y de salud",
  "O": "Otras actividades de servicios comunitarios, sociales y personales"
}

_SECTOR_CODES = list(_SECTORS.keys())

def _build_period(row):
  month_str = str(row["mes"])
  year = int(row["anio"])
  month = MONTHS.get(month_str, "01")
  return f"{year}-{month}"

def _process_sheet(df, skiprows, columns):
  df = df.dropna(how="all", axis=1)

  if len(df.columns) != len(columns):
    return pd.DataFrame(columns=columns), skiprows

  df.columns = columns
  df["anio"] = df["anio"].ffill()
  df = df.dropna(subset=["mes", "anio"])

  cursor = df.index[-1] + 1

  if skiprows >= cursor:
    skiprows = max(df.index[0], cursor - _FALLBACK_MONTHS)

  df = df.loc[skiprows:]

  return df, cursor

def _extract_monthly(url, skiprows, columns):
  raw = pd.read_excel(url, sheet_name="Tabla", header=None)
  df, cursor = _process_sheet(raw, skiprows, columns)

  records = []
  for _, row in df.iterrows():
    records.append({
      "periodo": _build_period(row),
      "original": {
        "indice": to_float(row["indice_original"]),
        "interanual": to_float(row["interanual"])
      },
      "desestacionalizada": {
        "indice": to_float(row["indice_desest"]),
        "mensual": to_float(row["var_mensual_desest"])
      },
      "tendencia_ciclo": {
        "indice": to_float(row["indice_tendencia"]),
        "mensual": to_float(row["var_mensual_tendencia"])
      }
    })

  return records, cursor

def _extract_sectors(raw, skiprows_indices, skiprows_var, columns_indices, columns_var):
  df_indices, cursor_indices = _process_sheet(raw["Tabla Letras"], skiprows_indices, columns_indices)
  df_var, cursor_var = _process_sheet(raw["Tabla Var Letras"], skiprows_var, columns_var)

  if df_indices.empty or df_var.empty:
    return [], {"historico": []}, cursor_indices, cursor_var

  df_indices["periodo"] = df_indices.apply(_build_period, axis=1)
  df_var["periodo"] = df_var.apply(_build_period, axis=1)

  sectores = {code: {"historico": []} for code in _SECTOR_CODES}
  impuestos = {"historico": []}

  var_by_periodo = {}
  for _, row in df_var.iterrows():
    period = row["periodo"]
    var_by_periodo[period] = {code: row[code] for code in _SECTOR_CODES}
    var_by_periodo[period]["impuestos"] = row["impuestos"]

  for _, row in df_indices.iterrows():
    period = row["periodo"]
    variations = var_by_periodo.get(period, {})

    for code in _SECTOR_CODES:
      sectores[code]["historico"].append({
        "periodo": period,
        "indice": to_float(row[code]),
        "interanual": to_float(variations.get(code))
      })

    impuestos["historico"].append({
      "periodo": period,
      "indice": to_float(row["impuestos"]),
      "interanual": to_float(variations.get("impuestos"))
    })

  sectores_list = [
    {"codigo": code, "nombre": _SECTORS[code], "historico": sectores[code]["historico"]}
    for code in _SECTOR_CODES
  ]

  return sectores_list, impuestos, cursor_indices, cursor_var

def extract(config: dict) -> tuple[dict, dict]:
  urls = config["urls"]
  sheets = config["sheets"]

  monthly_cfg = sheets["monthly"][0]
  nivel_general, new_skiprows_monthly = _extract_monthly(
    urls["monthly"], monthly_cfg["skiprows"], monthly_cfg["columns"]
  )

  raw_activity = pd.read_excel(urls["activity"], sheet_name=None, header=None)

  activity_indices_cfg = sheets["activity"][0]
  activity_var_cfg = sheets["activity"][1]
  sectores, impuestos, new_skiprows_indices, new_skiprows_var = _extract_sectors(
    raw_activity,
    activity_indices_cfg["skiprows"],
    activity_var_cfg["skiprows"],
    activity_indices_cfg["columns"],
    activity_var_cfg["columns"]
  )

  new_skiprows = {
    "monthly": [{"name": "Tabla", "skiprows": new_skiprows_monthly, "columns": monthly_cfg["columns"]}],
    "activity": [
      {"name": "Tabla Letras", "skiprows": new_skiprows_indices, "columns": activity_indices_cfg["columns"]},
      {"name": "Tabla Var Letras", "skiprows": new_skiprows_var, "columns": activity_var_cfg["columns"]}
    ]
  }

  return {
    "nivel_general": nivel_general,
    "sectores": sectores,
    "impuestos_netos_subsidios": impuestos
  }, new_skiprows