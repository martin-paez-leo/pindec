import warnings

import pandas as pd
from .common import to_float

_WINDOW_ROWS = 8

def _as_dates(values):
  with warnings.catch_warnings():
    warnings.simplefilter("ignore", UserWarning)
    return pd.to_datetime(values, errors="coerce")

def _data_window(raw, window):
  df = raw.dropna(how="all", axis=1)

  if df.empty or len(df.columns) == 0:
    return df

  valid = df[_as_dates(df.iloc[:, 0]).notna()]

  if valid.empty:
    return valid

  start = valid.index[max(0, len(valid) - window)]
  return df.loc[start:valid.index[-1]]

def extract(config: dict) -> tuple[dict, dict]:
  url = config["url"]
  sheets = config["sheets"]
  sheets_names = [s["name"] for s in sheets]

  all_sheets = pd.read_excel(url, sheet_name=sheets_names, header=None)

  new_skiprows = {}
  processed = {}

  for sc in sheets:
    name = sc["name"]
    columns = sc["columns"]

    raw = all_sheets[name]
    skiprows = raw.index[0] + len(raw)

    df = _data_window(raw, _WINDOW_ROWS)

    if len(df.columns) != len(columns):
      new_skiprows[name] = skiprows
      processed[name] = pd.DataFrame(columns=columns)
      continue

    df.columns = columns
    df.reset_index(drop=True, inplace=True)
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df = df.dropna(subset=["fecha"])

    new_skiprows[name] = skiprows
    processed[name] = df

  adulto = pd.merge(processed["CBA-CBT"], processed["Variaciones"], on="fecha", how="left")

  records = []
  for _, row in adulto.iterrows():
    records.append({
      "fecha": row["fecha"].strftime("%Y-%m"),
      "cba": to_float(row["cba"]),
      "coef_engel": to_float(row["coef_engel"]),
      "cbt": to_float(row["cbt"]),
      "cba_mensual": to_float(row["cba_mensual"]),
      "cba_interanual": to_float(row["cba_interanual"]),
      "cbt_mensual": to_float(row["cbt_mensual"]),
      "cbt_interanual": to_float(row["cbt_interanual"]),
    })

  hogares = []
  if "Hogares" in processed:
    for _, row in processed["Hogares"].iterrows():
      hogares.append({
        "fecha": row["fecha"].strftime("%Y-%m"),
        "cba_h1": to_float(row["cba_h1"]),
        "cba_h2": to_float(row["cba_h2"]),
        "cba_h3": to_float(row["cba_h3"]),
        "cbt_h1": to_float(row["cbt_h1"]),
        "cbt_h2": to_float(row["cbt_h2"]),
        "cbt_h3": to_float(row["cbt_h3"]),
      })

  return {"adulto_equivalente": records, "hogares": hogares}, new_skiprows