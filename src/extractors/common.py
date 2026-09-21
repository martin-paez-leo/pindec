import pandas as pd

_PLACEHOLDERS_NA = {"..", "...", "///", "na", "n/a", "-", ""}

MONTHS = {
  "Enero": "01", "Febrero": "02", "Marzo": "03", "Abril": "04",
  "Mayo": "05", "Junio": "06", "Julio": "07", "Agosto": "08",
  "Septiembre": "09", "Octubre": "10", "Noviembre": "11", "Diciembre": "12"
}

def to_float(value, decimals=6):
  if pd.isna(value):
    return None

  if isinstance(value, str):
    if value.lower() in _PLACEHOLDERS_NA:
      return None
    value = value.replace(",", ".")
    
  try:
    return round(float(value), decimals)
      
  except (ValueError, TypeError):
    return None
  
def date_from_yyyymm(value) -> str:
  date = str(value)
  return f"{date[:4]}-{date[4:]}"