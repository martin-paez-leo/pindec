import pandas as pd

_PLACEHOLDERS_NA = {"..", "...", "///", "na", "n/a", "-", ""}

def to_float(value, decimals=6):
  
  if pd.isna(value) or value.lower() in _PLACEHOLDERS_NA:
    return None
  
  if isinstance(value, str):
    value = value.replace(",", ".")
    
  try:
    return round(float(value), decimals)
      
  except (ValueError, TypeError):
    return None
  
def date_from_yyyymm(value) -> str:
  date = str(value)
  return f"{date[:4]}-{date[4:]}"

