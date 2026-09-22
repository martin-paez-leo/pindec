from utils import load_json, write_json, API_DIR
from extractors.common import FUENTES

def _is_year(name: str) -> bool:
  return name.isdigit() and len(name) == 4

def _get_years(indicator: str) -> list[int]:
  indicator_dir = API_DIR / indicator
  if not indicator_dir.exists():
    return []
  years = []
  for d in indicator_dir.iterdir():
    if d.is_dir() and d.name.isdigit():
      years.append(int(d.name))
  return sorted(years)

def _write_ipc_code_filters(clas_dir, year, fuente, codes):
  for code_obj in codes:
    write_json(clas_dir / code_obj["codigo"] / str(year) / "index.json", {
      "fuente": fuente, "datos": code_obj,
    })

def _write_ipc_clasif_filters(region_dir, year, fuente, clasifs):
  clasificacion_codes = {}
  for clasificacion, codes in clasifs.items():
    clasificacion_codes[clasificacion] = [c["codigo"] for c in codes]
    clas_dir = region_dir / clasificacion
    write_json(clas_dir / str(year) / "index.json", {"fuente": fuente, "datos": codes})
    _write_ipc_code_filters(clas_dir, year, fuente, codes)
  return clasificacion_codes

def generate_ipc_filters(year_data: dict, year: int):
  datos = year_data.get("datos", {})
  fuente = year_data.get("fuente", "")

  for region, clasifs in datos.items():
    region_dir = API_DIR / "ipc" / region
    write_json(region_dir / str(year) / "index.json", {"fuente": fuente, "datos": clasifs})
    clasificacion_codes = _write_ipc_clasif_filters(region_dir, year, fuente, clasifs)
    write_json(region_dir / "index.json", {
      "indicador": "ipc",
      "region": region,
      "clasificaciones": clasificacion_codes,
      "anos_disponibles": _get_years("ipc"),
    })

def generate_ipc_index():
  ipc_dir = API_DIR / "ipc"
  if not ipc_dir.exists():
    return

  data = {}

  for year_dir in sorted(ipc_dir.iterdir()):
    if not year_dir.is_dir() or not _is_year(year_dir.name):
      continue

    year_data = load_json(year_dir / "index.json")
    if not year_data:
      continue
    
    data[year_dir.name] = year_data.get("datos", {})

  write_json(ipc_dir / "index.json", {
    "fuente": FUENTES["ipc"],
    "datos": data,
  })

def generate_cba_cbt_filters(year_data: dict, year: int):
  fuente = year_data.get("fuente", "")

  adulto = year_data.get("adulto_equivalente", [])
  if adulto:
    write_json(API_DIR / "cba-cbt" / "adulto-equivalente" / str(year) / "index.json", {
      "fuente": fuente,
      "datos": adulto,
    })

  hogares = year_data.get("hogares", [])
  if hogares:
    write_json(API_DIR / "cba-cbt" / "hogares" / str(year) / "index.json", {
      "fuente": fuente,
      "datos": hogares,
    })

def generate_cba_cbt_index():
  cba_cbt_dir = API_DIR / "cba-cbt"
  if not cba_cbt_dir.exists():
    return
  
  data = {}

  for year_dir in sorted(cba_cbt_dir.iterdir()):
    if not year_dir.is_dir() or not _is_year(year_dir.name):
      continue

    year_data = load_json(year_dir / "index.json")
    if not year_data:
      continue
    
    data[year_dir.name] = {
      "adulto_equivalente": year_data.get("adulto_equivalente", []),
      "hogares": year_data.get("hogares", []),
    }

  write_json(cba_cbt_dir / "index.json", {
    "fuente": FUENTES["cba-cbt"],
    "datos": data,
  })

def generate_emae_filters(year_data: dict, year: int):
  datos = year_data.get("datos", {})
  fuente = year_data.get("fuente", "")

  nivel = datos.get("nivel_general", [])
  if nivel:
    write_json(API_DIR / "emae" / "nivel-general" / str(year) / "index.json", {
      "fuente": fuente,
      "datos": nivel,
    })

  sectores = datos.get("sectores", [])
  if sectores:
    sectores_dir = API_DIR / "emae" / "sectores"
    write_json(sectores_dir / str(year) / "index.json", {
      "fuente": fuente,
      "datos": sectores,
    })
    for sector in sectores:
      write_json(sectores_dir / sector["codigo"] / str(year) / "index.json", {
        "fuente": fuente,
        "datos": sector,
      })

  impuestos = datos.get("impuestos_netos_subsidios", {})
  if impuestos:
    write_json(API_DIR / "emae" / "impuestos" / str(year) / "index.json", {
      "fuente": fuente,
      "datos": impuestos,
    })

def generate_emae_index():
  emae_dir = API_DIR / "emae"
  if not emae_dir.exists():
    return
  
  data = {}

  for year_dir in sorted(emae_dir.iterdir()):
    if not year_dir.is_dir() or not _is_year(year_dir.name):
      continue

    year_data = load_json(year_dir / "index.json")
    if not year_data:
      continue
    
    data[year_dir.name] = year_data.get("datos", {})

  write_json(emae_dir / "index.json", {
    "fuente": FUENTES["emae"],
    "datos": data,
  })

def generate_ica_index():
  ica_dir = API_DIR / "ica"
  if not ica_dir.exists():
    return
  
  data = {}

  for year_dir in sorted(ica_dir.iterdir()):
    if not year_dir.is_dir() or not _is_year(year_dir.name):
      continue

    year_data = load_json(year_dir / "index.json")
    if not year_data:
      continue
    
    data[year_dir.name] = year_data.get("datos", {})
    
  write_json(ica_dir / "index.json", {
    "fuente": FUENTES["ica"],
    "unidad_medida": "Millones de dólares",
    "datos": data,
  })

_FILTER_GENERATORS = {
  "ipc": generate_ipc_filters,
  "cba-cbt": generate_cba_cbt_filters,
  "emae": generate_emae_filters,
}

def generate_all_filters(indicator: str, year_data: dict, year: int):
  generator = _FILTER_GENERATORS.get(indicator)
  if generator:
    generator(year_data, year)

def generate_all_indexes():
  generate_ipc_index()
  generate_cba_cbt_index()
  generate_emae_index()
  generate_ica_index()

  write_json(API_DIR / "index.json", {
    "nombre": "PINDEC API",
    "descripcion": "API no oficial del INDEC para indicadores económicos y sociales de Argentina",
    "version": "v1",
    "indicadores": ["ipc", "cba-cbt", "emae", "ica"],
  })
