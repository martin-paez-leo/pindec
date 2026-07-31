import json
from checker import load_metadata, save_metadata, needs_update
from extractors import ipc, cba_cbt, emae, ica
from utils import to_native, load_json, write_json, extract_year, group_by_year, merge, API_DIR, ROOT
from api import generate_all_filters, generate_all_indexes

CONFIG_PATH = ROOT / "config" / "config.json"
METADATA_PATH = ROOT / "config" / "metadata.json"

EXTRACTORS = {
  "ipc": ipc,
  "cba-cbt": cba_cbt,
  "emae": emae,
  "ica": ica,
}

FUENTES = {
  "ipc": "INDEC - Índice de Precios al Consumidor",
  "cba-cbt": "INDEC - Canasta Básica Alimentaria y Canasta Básica Total",
  "emae": "INDEC - Estimador Mensual de Actividad Económica (EMAE)",
  "ica": "INDEC - Intercambio Comercial Argentino (Balanza Comercial)",
}

def load_config() -> dict:
  with open(CONFIG_PATH, "r") as f:
    return json.load(f)

def save_config(config: dict):
  with open(CONFIG_PATH, "w") as f:
    json.dump(to_native(config), f, indent=2, ensure_ascii=False)

def _load_year(indicator: str, year: int) -> dict | None:
  return load_json(API_DIR / indicator / str(year) / "index.json")

def _save_year(indicator: str, year: int, data: dict):
  write_json(API_DIR / indicator / str(year) / "index.json", data)

def _group_year_region_clasif(records):
  groups = {}
  for r in records:
    groups.setdefault(extract_year(r["periodo"]), {}).setdefault(r["region"], {}).setdefault(r["clasificacion"], []).append(r)
  return groups

def _build_by_code(flat_records):
  by_code = {}
  for r in flat_records:
    code = r["codigo"]
    if code not in by_code:
      by_code[code] = {"codigo": code, "nombre": r["nombre"], "historico": []}
    by_code[code]["historico"].append({
      "periodo": r["periodo"], "indice": r["indice"], "mensual": r["mensual"], "interanual": r["interanual"],
    })
  return list(by_code.values())

def _restructure_region_clasifs(regions_data):
  restructured = {}
  for region, clasifs in regions_data.items():
    inner = {}
    for clasificacion, flat_records in clasifs.items():
      inner[clasificacion] = _build_by_code(flat_records)
    restructured[region] = inner
  return restructured

def _merge_into_existing(datos, restructured):
  for region, clasifs in restructured.items():
    for clasificacion, new_codes in clasifs.items():
      old_list = datos.get(region, {}).get(clasificacion, [])
      old_map = {c["codigo"]: c for c in old_list}
      for new_item in new_codes:
        if new_item["codigo"] in old_map:
          old_hist = old_map[new_item["codigo"]].get("historico", [])
          new_item["historico"] = merge(old_hist, new_item["historico"], "periodo")
        old_map[new_item["codigo"]] = new_item
      datos.setdefault(region, {})[clasificacion] = list(old_map.values())

def _save_ipc(records: list[dict]):
  year_groups = _group_year_region_clasif(records)

  for year, regions_data in year_groups.items():
    restructured = _restructure_region_clasifs(regions_data)
    existing = _load_year("ipc", year)

    if existing and "datos" in existing:
      _merge_into_existing(existing["datos"], restructured)
      _save_year("ipc", year, existing)
    else:
      _save_year("ipc", year, {"fuente": FUENTES["ipc"], "datos": restructured})

def _save_cba_cbt(data: dict):
  adulto = [{
    "periodo": r["fecha"],
    "cba": {"indice": r["cba"], "mensual": r["cba_mensual"], "interanual": r["cba_interanual"]},
    "cbt": {"indice": r["cbt"], "mensual": r["cbt_mensual"], "interanual": r["cbt_interanual"]},
    "coef_engel": r["coef_engel"],
  } for r in data["adulto_equivalente"]]

  hogares = [{
    "periodo": r["fecha"],
    "hogar_1": {"cba": r["cba_h1"], "cbt": r["cbt_h1"]},
    "hogar_2": {"cba": r["cba_h2"], "cbt": r["cbt_h2"]},
    "hogar_3": {"cba": r["cba_h3"], "cbt": r["cbt_h3"]},
  } for r in data["hogares"]]

  adulto_groups = group_by_year(adulto, "periodo")
  hogares_groups = group_by_year(hogares, "periodo")
  all_years = set(adulto_groups.keys()) | set(hogares_groups.keys())

  for year in all_years:
    existing = _load_year("cba-cbt", year)
    if existing:
      merged_adulto = merge(existing.get("adulto_equivalente", []), adulto_groups.get(year, []), "periodo")
      merged_hogares = merge(existing.get("hogares", []), hogares_groups.get(year, []), "periodo")
    else:
      merged_adulto = adulto_groups.get(year, [])
      merged_hogares = hogares_groups.get(year, [])
    _save_year("cba-cbt", year, {
      "fuente": FUENTES["cba-cbt"],
      "adulto_equivalente": merged_adulto,
      "hogares": merged_hogares,
    })

def _group_sectores_by_year(sectores):
  by_year = {}
  for sector in sectores:
    for year, records in group_by_year(sector["historico"], "periodo").items():
      by_year.setdefault(year, []).append({
        "codigo": sector["codigo"],
        "nombre": sector["nombre"],
        "historico": records,
      })
  return by_year

def _merge_sectores(old_sectores, new_sectores):
  old_map = {s["codigo"]: s for s in old_sectores}
  for new_s in new_sectores:
    if new_s["codigo"] in old_map:
      old_hist = old_map[new_s["codigo"]].get("historico", [])
      new_s["historico"] = merge(old_hist, new_s["historico"], "periodo")
    old_map[new_s["codigo"]] = new_s
  return list(old_map.values())

def _save_emae(data: dict):
  nivel_groups = group_by_year(data["nivel_general"], "periodo")
  sectores_by_year = _group_sectores_by_year(data["sectores"])
  imp_groups = group_by_year(data["impuestos_netos_subsidios"]["historico"], "periodo")

  all_years = set(nivel_groups) | set(sectores_by_year) | set(imp_groups)

  for year in all_years:
    existing = _load_year("emae", year)
    if existing and "datos" in existing:
      old = existing["datos"]
      merged_nivel = merge(old.get("nivel_general", []), nivel_groups.get(year, []), "periodo")
      merged_imp = merge(old.get("impuestos_netos_subsidios", {}).get("historico", []), imp_groups.get(year, []), "periodo")
      merged_sectores = _merge_sectores(old.get("sectores", []), sectores_by_year.get(year, []))
    else:
      merged_nivel = nivel_groups.get(year, [])
      merged_sectores = sectores_by_year.get(year, [])
      merged_imp = imp_groups.get(year, [])

    _save_year("emae", year, {
      "fuente": FUENTES["emae"],
      "datos": {
        "nivel_general": merged_nivel,
        "sectores": merged_sectores,
        "impuestos_netos_subsidios": {"historico": merged_imp},
      },
    })

def _save_ica(records: list[dict]):
  groups = group_by_year(records, "periodo")
  for year, new_records in groups.items():
    existing = _load_year("ica", year)
    if existing and "datos" in existing:
      merged = merge(existing["datos"], new_records, "periodo")
    else:
      merged = new_records
    _save_year("ica", year, {
      "fuente": FUENTES["ica"],
      "unidad_medida": "Millones de dólares",
      "datos": merged,
    })

_SAVERS = {
  "ipc": _save_ipc,
  "cba-cbt": _save_cba_cbt,
  "emae": _save_emae,
  "ica": _save_ica,
}

def _update_emae_skiprows(sheets, new_skiprows):
  for key in ("monthly", "activity"):
    if key in new_skiprows and key in sheets:
      for sheet_cfg, new_sheet in zip(sheets[key], new_skiprows[key]):
        sheet_cfg["skiprows"] = new_sheet["skiprows"]

def _update_cba_cbt_skiprows(sheets, new_skiprows):
  if isinstance(new_skiprows, dict):
    first_val = next(iter(new_skiprows.values()))
    if not isinstance(first_val, dict):
      for sheet_cfg in sheets:
        if sheet_cfg["name"] in new_skiprows:
          sheet_cfg["skiprows"] = new_skiprows[sheet_cfg["name"]]

def _update_default_skiprows(sheets, new_skiprows):
  if isinstance(new_skiprows, dict) and "sheets" in new_skiprows:
    for sheet_cfg, new_sheet in zip(sheets, new_skiprows["sheets"]):
      sheet_cfg["skiprows"] = new_sheet["skiprows"]

_SKIPROW_UPDATERS = {
  "emae": _update_emae_skiprows,
  "cba-cbt": _update_cba_cbt_skiprows,
}

def update_skiprows(config, name, new_skiprows):
  updater = _SKIPROW_UPDATERS.get(name)
  if updater:
    updater(config[name]["sheets"], new_skiprows)
  elif "sheets" in config[name]:
    _update_default_skiprows(config[name]["sheets"], new_skiprows)

def run():
  config = load_config()
  metadata = load_metadata(METADATA_PATH)

  for name, extractor in EXTRACTORS.items():
    indicator_config = config.get(name)
    if not indicator_config:
      continue

    url = indicator_config.get("urls") or indicator_config.get("url")
    changed, last_modified = needs_update(metadata.get(name, {}), url)

    if not changed:
      print(f"{name}: no updates")
      continue

    print(f"{name}: extracting...")
    data, new_skiprows = extractor.extract(indicator_config)
    _SAVERS[name](data)

    metadata[name] = {"last-modified": last_modified}
    update_skiprows(config, name, new_skiprows)
    print(f"{name}: done")

  save_metadata(METADATA_PATH, metadata)
  save_config(config)

  print("generating API filters and indexes...")
  for indicator in EXTRACTORS:
    indicator_dir = API_DIR / indicator
    if not indicator_dir.exists():
      continue
    for year_dir in sorted(d for d in indicator_dir.iterdir() if d.is_dir() and d.name.isdigit()):
      year_data = load_json(year_dir / "index.json")
      if year_data:
        generate_all_filters(indicator, year_data, int(year_dir.name))

  generate_all_indexes()
  print("API structure generated")

if __name__ == "__main__":
  run()
