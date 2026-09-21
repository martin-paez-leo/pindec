import sys
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from utils import write_json
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
