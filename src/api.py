from utils import write_json, API_DIR

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

  regions = []
  structure = {}
  for d in sorted(ipc_dir.iterdir()):
    if d.is_dir() and not _is_year(d.name):
      regions.append(d.name)
      clasifs = {}
      for c in sorted(d.iterdir()):
        if c.is_dir() and not _is_year(c.name):
          clasifs[c.name] = [p.name for p in sorted(c.iterdir()) if p.is_dir() and not _is_year(p.name)]
      structure[d.name] = clasifs

  write_json(ipc_dir / "index.json", {
    "indicador": "ipc",
    "nombre": "Índice de Precios al Consumidor",
    "regiones": regions,
    "anos_disponibles": _get_years("ipc"),
    "estructura": structure,
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
  write_json(API_DIR / "cba-cbt" / "index.json", {
    "indicador": "cba-cbt",
    "nombre": "Canasta Básica Alimentaria y Canasta Básica Total",
    "subcategorias": ["adulto-equivalente", "hogares"],
    "anos_disponibles": _get_years("cba-cbt"),
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
  sectores_dir = emae_dir / "sectores"
  sectores_codes = []
  if sectores_dir.exists():
    for d in sorted(sectores_dir.iterdir()):
      if d.is_dir() and not _is_year(d.name):
        sectores_codes.append(d.name)

  write_json(emae_dir / "index.json", {
    "indicador": "emae",
    "nombre": "Estimador Mensual de Actividad Económica (EMAE)",
    "subcategorias": ["nivel-general", "sectores", "impuestos"],
    "sectores": sectores_codes,
    "anos_disponibles": _get_years("emae"),
  })

  if sectores_dir.exists():
    write_json(sectores_dir / "index.json", {
      "indicador": "emae",
      "subcategoria": "sectores",
      "codigos": sectores_codes,
      "anos_disponibles": _get_years("emae"),
    })

def generate_ica_index():
  write_json(API_DIR / "ica" / "index.json", {
    "indicador": "ica",
    "nombre": "Intercambio Comercial Argentino (Balanza Comercial)",
    "unidad_medida": "Millones de dólares",
    "anos_disponibles": _get_years("ica"),
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
