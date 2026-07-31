import sys
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from api import (
  generate_ipc_filters,
  generate_ipc_index,
  generate_cba_cbt_filters,
  generate_cba_cbt_index,
  generate_emae_filters,
  generate_emae_index,
  generate_ica_index,
  generate_all_filters,
  generate_all_indexes,
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
