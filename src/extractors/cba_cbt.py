import pandas as pd
from .common import to_float

def extract(config: dict) -> tuple[dict, dict]:
  url = config["url"]
  sheets = config["sheets"]
  sheets_names = [s["name"] for s in sheets]

  all_sheets = pd.read_excel(url, sheet_name=sheets_names, header=None)

  new_skiprows = {}
  processed = {}

  for sc in sheets:
    name = sc["name"]
    skiprows = sc["skiprows"]
    columns = sc["columns"]

    df = all_sheets[name].iloc[skiprows:]
    df = df.dropna(how="all", axis=1)

    if len(df.columns) != len(columns):
      new_skiprows[name] = skiprows
      processed[name] = pd.DataFrame(columns=columns)
      continue

    df.columns = columns
    df.reset_index(drop=True, inplace=True)
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df = df.dropna(subset=["fecha"])

    new_skiprows[name] = skiprows + len(df)
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