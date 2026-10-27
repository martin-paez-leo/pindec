import sys
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from utils import write_json
from api import (
  generate_ipc_filters,
  generate_ipc_index,
  generate_ipc_parent_indexes,
  generate_cba_cbt_filters,
  generate_cba_cbt_index,
  generate_cba_cbt_parent_indexes,
  generate_emae_filters,
  generate_emae_index,
  generate_emae_parent_indexes,
  generate_ica_index,
  generate_all_filters,
  generate_all_indexes,
  generate_meta,
  generate_error_page,
)


class TestGenerateIpcFilters:
  def test_creates_region_files(self, tmp_path, monkeypatch):
    monkeypatch.setattr("api.API_DIR", tmp_path)
    year_data = {
      "fuente": "INDEC",
      "datos": {
        "Nacional": {
          "COICOP": [
            {"codigo": "0", "nombre": "NIVEL GENERAL", "historico": [{"periodo": "2026-01", "indice": 100.0, "mensual": 2.0, "interanual": 30.0}]}
          ]
        }
      },
    }
    generate_ipc_filters(year_data, 2026)
    assert (tmp_path / "ipc" / "Nacional" / "2026" / "index.json").exists()
    data = json.loads((tmp_path / "ipc" / "Nacional" / "2026" / "index.json").read_text())
    assert "COICOP" in data["datos"]

  def test_creates_clasificacion_files(self, tmp_path, monkeypatch):
    monkeypatch.setattr("api.API_DIR", tmp_path)
    year_data = {
      "fuente": "INDEC",
      "datos": {
        "Nacional": {
          "COICOP": [
            {"codigo": "0", "nombre": "NIVEL GENERAL", "historico": [{"periodo": "2026-01", "indice": 100.0, "mensual": 2.0, "interanual": 30.0}]}
          ]
        }
      },
    }
    generate_ipc_filters(year_data, 2026)
    assert (tmp_path / "ipc" / "Nacional" / "COICOP" / "2026" / "index.json").exists()

  def test_creates_code_files(self, tmp_path, monkeypatch):
    monkeypatch.setattr("api.API_DIR", tmp_path)
    year_data = {
      "fuente": "INDEC",
      "datos": {
        "Nacional": {
          "COICOP": [
            {"codigo": "0", "nombre": "NIVEL GENERAL", "historico": [{"periodo": "2026-01", "indice": 100.0, "mensual": 2.0, "interanual": 30.0}]}
          ]
        }
      },
    }
    generate_ipc_filters(year_data, 2026)
    code_file = tmp_path / "ipc" / "Nacional" / "COICOP" / "0" / "2026" / "index.json"
    assert code_file.exists()
    data = json.loads(code_file.read_text())
    assert data["datos"]["codigo"] == "0"

  def test_creates_region_index(self, tmp_path, monkeypatch):
    monkeypatch.setattr("api.API_DIR", tmp_path)
    year_data = {
      "fuente": "INDEC",
      "datos": {
        "Nacional": {
          "COICOP": [
            {"codigo": "0", "nombre": "NIVEL GENERAL", "historico": []}
          ]
        }
      },
    }
    generate_ipc_filters(year_data, 2026)
    index = json.loads((tmp_path / "ipc" / "Nacional" / "index.json").read_text())
    assert "COICOP" in index["clasificaciones"]


class TestGenerateCbaCbtFilters:
  def test_creates_subcategory_files(self, tmp_path, monkeypatch):
    monkeypatch.setattr("api.API_DIR", tmp_path)
    year_data = {
      "fuente": "INDEC",
      "adulto_equivalente": [{"periodo": "2026-01", "cba": {"indice": 100.0}}],
      "hogares": [{"periodo": "2026-01", "hogar_1": {"cba": 500.0}}],
    }
    generate_cba_cbt_filters(year_data, 2026)
    assert (tmp_path / "cba-cbt" / "adulto-equivalente" / "2026" / "index.json").exists()
    assert (tmp_path / "cba-cbt" / "hogares" / "2026" / "index.json").exists()


class TestGenerateEmaeFilters:
  def test_creates_subcategory_files(self, tmp_path, monkeypatch):
    monkeypatch.setattr("api.API_DIR", tmp_path)
    year_data = {
      "fuente": "INDEC",
      "datos": {
        "nivel_general": [{"periodo": "2004-01", "original": {"indice": 92.0}}],
        "sectores": [{"codigo": "A", "nombre": "Agri", "historico": [{"periodo": "2004-01", "indice": 65.0}]}],
        "impuestos_netos_subsidios": {"historico": [{"periodo": "2004-01", "indice": 104.0}]},
      },
    }
    generate_emae_filters(year_data, 2004)
    assert (tmp_path / "emae" / "nivel-general" / "2004" / "index.json").exists()
    assert (tmp_path / "emae" / "sectores" / "2004" / "index.json").exists()
    assert (tmp_path / "emae" / "sectores" / "A" / "2004" / "index.json").exists()
    assert (tmp_path / "emae" / "impuestos" / "2004" / "index.json").exists()


class TestGenerateParentIndexes:
  def _seed(self, tmp_path, dirs):
    for rel in dirs:
      (tmp_path / rel).mkdir(parents=True, exist_ok=True)

  def test_ipc_clasificacion_parent(self, tmp_path, monkeypatch):
    monkeypatch.setattr("api.API_DIR", tmp_path)
    self._seed(tmp_path, [
      "ipc/2016", "ipc/2026",
      "ipc/Nacional/COICOP/0/2026",
      "ipc/Pampeana/COICOP/04/2026",
    ])
    generate_ipc_parent_indexes()
    data = json.loads((tmp_path / "ipc" / "Nacional" / "COICOP" / "index.json").read_text())
    assert data["region"] == "Nacional"
    assert data["clasificacion"] == "COICOP"
    assert data["codigos"] == ["0"]
    assert data["anos_disponibles"] == [2016, 2026]

  def test_cba_cbt_parents(self, tmp_path, monkeypatch):
    monkeypatch.setattr("api.API_DIR", tmp_path)
    self._seed(tmp_path, ["cba-cbt/2026", "cba-cbt/adulto-equivalente/2026", "cba-cbt/hogares/2026"])
    generate_cba_cbt_parent_indexes()
    for subcategoria in ("adulto-equivalente", "hogares"):
      data = json.loads((tmp_path / "cba-cbt" / subcategoria / "index.json").read_text())
      assert data["indicador"] == "cba-cbt"
      assert data["subcategoria"] == subcategoria
      assert data["anos_disponibles"] == [2026]

  def test_emae_parents(self, tmp_path, monkeypatch):
    monkeypatch.setattr("api.API_DIR", tmp_path)
    self._seed(tmp_path, [
      "emae/2026", "emae/nivel-general/2026", "emae/impuestos/2026",
      "emae/sectores/2026", "emae/sectores/A/2026", "emae/sectores/B/2026",
    ])
    generate_emae_parent_indexes()

    nivel = json.loads((tmp_path / "emae" / "nivel-general" / "index.json").read_text())
    assert nivel["subcategoria"] == "nivel-general"

    sectores = json.loads((tmp_path / "emae" / "sectores" / "index.json").read_text())
    assert sectores["codigos"] == ["A", "B"]

    sector = json.loads((tmp_path / "emae" / "sectores" / "A" / "index.json").read_text())
    assert sector["codigo"] == "A"
    assert sector["anos_disponibles"] == [2026]

  def test_missing_subcategory_is_skipped(self, tmp_path, monkeypatch):
    monkeypatch.setattr("api.API_DIR", tmp_path)
    self._seed(tmp_path, ["emae/2026"])
    generate_emae_parent_indexes()
    assert not (tmp_path / "emae" / "nivel-general").exists()

  def test_empty_api_dir_is_safe(self, tmp_path, monkeypatch):
    monkeypatch.setattr("api.API_DIR", tmp_path)
    generate_ipc_parent_indexes()
    generate_cba_cbt_parent_indexes()
    generate_emae_parent_indexes()

  def test_ipc_year_dirs_are_not_treated_as_clasificaciones(self, tmp_path, monkeypatch):
    """Las carpetas de anios viven junto a las clasificaciones y no deben sobrescribirse."""
    monkeypatch.setattr("api.API_DIR", tmp_path)
    self._seed(tmp_path, [
      "ipc/2016", "ipc/Nacional/2016", "ipc/Nacional/COICOP/0/2016",
    ])
    generate_ipc_parent_indexes()
    assert not (tmp_path / "ipc" / "Nacional" / "2016" / "index.json").exists()
    assert (tmp_path / "ipc" / "Nacional" / "COICOP" / "index.json").exists()


class TestGenerateIpcIndex:
  def test_generate_index(self, tmp_path, monkeypatch):
    monkeypatch.setattr("api.API_DIR", tmp_path)
    
    year_data = {
      "fuente": "INDEC",
      "datos": {
        "Nacional": {
          "COICOP": [
            {"codigo": "0", "nombre": "NIVEL GENERAL", "historico": [{"periodo": "2026-01", "indice": 100.0, "mensual": 2.0, "interanual": 30.0}]}
          ]
        }
      },
    }
    write_json(tmp_path / "ipc" / "2026" / "index.json", year_data)
    
    generate_ipc_index()
    
    result = json.loads((tmp_path / "ipc" / "index.json").read_text())
    assert "fuente" in result
    assert "2026" in result["datos"]
    assert "Nacional" in result["datos"]["2026"]


class TestGenerateCbaCbtIndex:
  def test_generate_index(self, tmp_path, monkeypatch):
    monkeypatch.setattr("api.API_DIR", tmp_path)
    
    year_data = {
      "fuente": "INDEC",
      "adulto_equivalente": [{"periodo": "2026-01", "cba": {"indice": 100.0}}],
      "hogares": [{"periodo": "2026-01", "hogar_1": {"cba": 500.0}}],
    }
    write_json(tmp_path / "cba-cbt" / "2026" / "index.json", year_data)
    
    generate_cba_cbt_index()
    
    result = json.loads((tmp_path / "cba-cbt" / "index.json").read_text())
    assert "fuente" in result
    assert "2026" in result["datos"]
    assert "adulto_equivalente" in result["datos"]["2026"]
    assert "hogares" in result["datos"]["2026"]


class TestGenerateEmaeIndex:
  def test_generate_index(self, tmp_path, monkeypatch):
    monkeypatch.setattr("api.API_DIR", tmp_path)
    
    year_data = {
      "fuente": "INDEC",
      "datos": {
        "nivel_general": [{"periodo": "2004-01", "original": {"indice": 92.0}}],
        "sectores": [{"codigo": "A", "nombre": "Agri", "historico": [{"periodo": "2004-01", "indice": 65.0}]}],
        "impuestos_netos_subsidios": {"historico": [{"periodo": "2004-01", "indice": 104.0}]},
      },
    }
    write_json(tmp_path / "emae" / "2026" / "index.json", year_data)
    
    generate_emae_index()
    
    result = json.loads((tmp_path / "emae" / "index.json").read_text())
    assert "fuente" in result
    assert "2026" in result["datos"]
    assert "nivel_general" in result["datos"]["2026"]
    assert "sectores" in result["datos"]["2026"]
    assert "impuestos_netos_subsidios" in result["datos"]["2026"]
  
  
class TestGenerateIcaIndex:
  def test_generate_index(self, tmp_path, monkeypatch):
    monkeypatch.setattr("api.API_DIR", tmp_path)
    
    year_data = {
      "fuente": "INDEC",
      "unidad_medida": "Millones de dólares",
      "datos": [
          {
            "periodo": "2026-01",
            "exportaciones": {
              "mensual": 7245.296047,
              "acumulado": 7245.296047,
              "var_interanual_mensual": 22.493359,
              "var_interanual_acumulada": 22.493359
            },
            "importaciones": {
              "mensual": 5056.670157,
              "acumulado": 5056.670157,
              "var_interanual_mensual": -12.099952,
              "var_interanual_acumulada": -12.099952
            },
            "saldo": 2188.62589
          }
        ],
    }
    write_json(tmp_path / "ica" / "2026" / "index.json", year_data)
    
    generate_ica_index()
    
    result = json.loads((tmp_path / "ica" / "index.json").read_text())
    assert "fuente" in result
    assert "2026" in result["datos"]
    assert "periodo" in result["datos"]["2026"][0]
    assert "exportaciones" in result["datos"]["2026"][0]
    assert "importaciones" in result["datos"]["2026"][0]
    assert "saldo" in result["datos"]["2026"][0]
  
class TestGenerateAllIndexes:
  def test_creates_root_index(self, tmp_path, monkeypatch):
    monkeypatch.setattr("api.API_DIR", tmp_path)
    generate_all_indexes()
    assert (tmp_path / "index.json").exists()
    data = json.loads((tmp_path / "index.json").read_text())
    assert "indicadores" in data

  def test_creates_indicator_indexes(self, tmp_path, monkeypatch):
    monkeypatch.setattr("api.API_DIR", tmp_path)
    (tmp_path / "ipc").mkdir(parents=True)
    (tmp_path / "cba-cbt").mkdir(parents=True)
    (tmp_path / "emae").mkdir(parents=True)
    (tmp_path / "ica").mkdir(parents=True)
    generate_all_indexes()
    assert (tmp_path / "ipc" / "index.json").exists()
    assert (tmp_path / "cba-cbt" / "index.json").exists()
    assert (tmp_path / "emae" / "index.json").exists()
    assert (tmp_path / "ica" / "index.json").exists()


class TestGenerateMeta:
  def _seed(self, tmp_path):
    write_json(tmp_path / "ipc" / "2026" / "index.json", {
      "fuente": "INDEC",
      "datos": {
        "Nacional": {
          "COICOP": [
            {"codigo": "0", "nombre": "NIVEL GENERAL", "historico": [{"periodo": "2026-08", "indice": 100.0, "mensual": 2.0, "interanual": 30.0}]}
          ]
        }
      },
    })
    write_json(tmp_path / "cba-cbt" / "2026" / "index.json", {
      "fuente": "INDEC",
      "adulto_equivalente": [{"periodo": "2026-08", "cba": {"indice": 1.0}, "cbt": {"indice": 2.0}}],
      "hogares": [],
    })
    write_json(tmp_path / "emae" / "2026" / "index.json", {
      "fuente": "INDEC",
      "datos": {"nivel_general": [{"periodo": "2026-07", "original": {"indice": 1.0}}], "sectores": []},
    })
    write_json(tmp_path / "ica" / "2026" / "index.json", {
      "fuente": "INDEC",
      "unidad_medida": "Millones de dólares",
      "datos": [{"periodo": "2026-08", "saldo": 1.0}],
    })

  def test_creates_meta_file(self, tmp_path, monkeypatch):
    monkeypatch.setattr("api.API_DIR", tmp_path)
    self._seed(tmp_path)
    generate_meta()
    assert (tmp_path / "meta.json").exists()

  def test_reports_period_per_indicator(self, tmp_path, monkeypatch):
    monkeypatch.setattr("api.API_DIR", tmp_path)
    self._seed(tmp_path)
    generate_meta()
    data = json.loads((tmp_path / "meta.json").read_text())
    assert data["indicadores"]["ipc"]["periodo"] == "2026-08"
    assert data["indicadores"]["cba-cbt"]["periodo"] == "2026-08"
    assert data["indicadores"]["emae"]["periodo"] == "2026-07"
    assert data["indicadores"]["ica"]["periodo"] == "2026-08"

  def test_reports_year_range(self, tmp_path, monkeypatch):
    monkeypatch.setattr("api.API_DIR", tmp_path)
    self._seed(tmp_path)
    generate_meta()
    data = json.loads((tmp_path / "meta.json").read_text())
    assert data["indicadores"]["ipc"]["primer_anio"] == 2026
    assert data["indicadores"]["ipc"]["ultimo_anio"] == 2026

  def test_uses_last_modified_from_metadata(self, tmp_path, monkeypatch):
    monkeypatch.setattr("api.API_DIR", tmp_path)
    self._seed(tmp_path)
    generate_meta({"ipc": {"last-modified": "Thu, 10 Sep 2026 18:51:39 GMT"}})
    data = json.loads((tmp_path / "meta.json").read_text())
    assert data["indicadores"]["ipc"]["actualizado"] == "2026-09-10T18:51:39+00:00"
    assert data["actualizado"] == "2026-09-10T18:51:39+00:00"

  def test_handles_nested_last_modified(self, tmp_path, monkeypatch):
    monkeypatch.setattr("api.API_DIR", tmp_path)
    self._seed(tmp_path)
    generate_meta({"emae": {"last-modified": {"monthly": "Fri, 18 Sep 2026 18:52:55 GMT", "activity": "Thu, 24 Sep 2026 18:53:36 GMT"}}})
    data = json.loads((tmp_path / "meta.json").read_text())
    assert data["indicadores"]["emae"]["actualizado"] == "2026-09-24T18:53:36+00:00"

  def test_skips_indicators_without_data(self, tmp_path, monkeypatch):
    monkeypatch.setattr("api.API_DIR", tmp_path)
    self._seed(tmp_path)
    generate_meta()
    data = json.loads((tmp_path / "meta.json").read_text())
    assert "emae" in data["indicadores"]
    assert "inexistente" not in data["indicadores"]

  def test_all_indexes_generates_meta(self, tmp_path, monkeypatch):
    monkeypatch.setattr("api.API_DIR", tmp_path)
    self._seed(tmp_path)
    generate_all_indexes()
    assert (tmp_path / "meta.json").exists()


class TestGenerateErrorPage:
  def test_creates_404_page_with_problem_details(self, tmp_path, monkeypatch):
    monkeypatch.setattr("api.API_DIR", tmp_path)
    generate_error_page()
    path = tmp_path / "404.html"
    assert path.exists()
    data = json.loads(path.read_text())
    assert data["status"] == 404
    assert data["type"] == "https://pindec.dev/probs/not-found"
    assert "title" in data
    assert "detail" in data

  def test_error_page_is_valid_json(self, tmp_path, monkeypatch):
    monkeypatch.setattr("api.API_DIR", tmp_path)
    generate_error_page()
    json.loads((tmp_path / "404.html").read_text())

  def test_all_indexes_generates_error_page(self, tmp_path, monkeypatch):
    monkeypatch.setattr("api.API_DIR", tmp_path)
    generate_all_indexes()
    assert (tmp_path / "404.html").exists()
