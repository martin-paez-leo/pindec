import sys
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from main import _save_ipc, _save_cba_cbt, _save_ica, _save_emae
from api import API_DIR


class TestSaveIpc:
  def test_creates_year_files(self, tmp_path, monkeypatch):
    monkeypatch.setattr("main.API_DIR", tmp_path)
    records = [
      {"region": "Nacional", "clasificacion": "COICOP", "codigo": "0", "nombre": "NIVEL GENERAL", "periodo": "2026-01", "indice": 100.0, "mensual": 2.0, "interanual": 30.0},
      {"region": "Nacional", "clasificacion": "COICOP", "codigo": "0", "nombre": "NIVEL GENERAL", "periodo": "2026-02", "indice": 102.0, "mensual": 2.0, "interanual": 31.0},
      {"region": "GBA", "clasificacion": "COICOP", "codigo": "0", "nombre": "NIVEL GENERAL", "periodo": "2026-01", "indice": 101.0, "mensual": 2.5, "interanual": 32.0},
    ]
    _save_ipc(records)
    assert (tmp_path / "ipc" / "2026" / "index.json").exists()
    data = json.loads((tmp_path / "ipc" / "2026" / "index.json").read_text())
    assert "Nacional" in data["datos"]
    assert "GBA" in data["datos"]
    assert data["datos"]["Nacional"]["COICOP"][0]["codigo"] == "0"
    assert len(data["datos"]["Nacional"]["COICOP"][0]["historico"]) == 2

  def test_structure_matches_docs(self, tmp_path, monkeypatch):
    monkeypatch.setattr("main.API_DIR", tmp_path)
    records = [
      {"region": "Nacional", "clasificacion": "COICOP", "codigo": "0", "nombre": "NIVEL GENERAL", "periodo": "2026-01", "indice": 100.0, "mensual": 2.0, "interanual": 30.0},
      {"region": "Nacional", "clasificacion": "categorias", "codigo": "Estacional", "nombre": None, "periodo": "2026-01", "indice": 90.0, "mensual": 5.0, "interanual": 20.0},
    ]
    _save_ipc(records)
    data = json.loads((tmp_path / "ipc" / "2026" / "index.json").read_text())
    assert data["fuente"] == "INDEC - Índice de Precios al Consumidor"
    nac = data["datos"]["Nacional"]
    assert "COICOP" in nac
    assert "categorias" in nac
    coicop = nac["COICOP"][0]
    assert coicop["codigo"] == "0"
    assert coicop["nombre"] == "NIVEL GENERAL"
    assert "historico" in coicop
    assert coicop["historico"][0]["periodo"] == "2026-01"


class TestSaveCbaCbt:
  def test_creates_year_files(self, tmp_path, monkeypatch):
    monkeypatch.setattr("main.API_DIR", tmp_path)
    data = {
      "adulto_equivalente": [
        {"fecha": "2026-01", "cba": 100.0, "coef_engel": 2.18, "cbt": 200.0, "cba_mensual": 5.0, "cba_interanual": 30.0, "cbt_mensual": 3.0, "cbt_interanual": 25.0}
      ],
      "hogares": [
        {"fecha": "2026-01", "cba_h1": 500.0, "cba_h2": 600.0, "cba_h3": 700.0, "cbt_h1": 1000.0, "cbt_h2": 1200.0, "cbt_h3": 1400.0}
      ],
    }
    _save_cba_cbt(data)
    assert (tmp_path / "cba-cbt" / "2026" / "index.json").exists()
    result = json.loads((tmp_path / "cba-cbt" / "2026" / "index.json").read_text())
    assert result["fuente"] == "INDEC - Canasta Básica Alimentaria y Canasta Básica Total"
    assert "adulto_equivalente" in result
    assert "hogares" in result
    adulto = result["adulto_equivalente"][0]
    assert adulto["periodo"] == "2026-01"
    assert adulto["cba"] == {"indice": 100.0, "mensual": 5.0, "interanual": 30.0}
    assert adulto["cbt"] == {"indice": 200.0, "mensual": 3.0, "interanual": 25.0}
    hogar = result["hogares"][0]
    assert hogar["hogar_1"] == {"cba": 500.0, "cbt": 1000.0}


class TestSaveIca:
  def test_creates_year_files_with_unidad_medida(self, tmp_path, monkeypatch):
    monkeypatch.setattr("main.API_DIR", tmp_path)
    records = [
      {"periodo": "1990-01", "exportaciones": {"mensual": 795.0, "acumulado": 795.0, "var_interanual_mensual": None, "var_interanual_acumulada": None}, "importaciones": {"mensual": 385.0, "acumulado": 385.0, "var_interanual_mensual": None, "var_interanual_acumulada": None}, "saldo": 410.0},
    ]
    _save_ica(records)
    assert (tmp_path / "ica" / "1990" / "index.json").exists()
    result = json.loads((tmp_path / "ica" / "1990" / "index.json").read_text())
    assert result["fuente"] == "INDEC - Intercambio Comercial Argentino (Balanza Comercial)"
    assert result["unidad_medida"] == "Millones de dólares"
    assert len(result["datos"]) == 1
    assert result["datos"][0]["saldo"] == 410.0


class TestSaveEmae:
  def test_creates_year_files(self, tmp_path, monkeypatch):
    monkeypatch.setattr("main.API_DIR", tmp_path)
    data = {
      "nivel_general": [
        {"periodo": "2004-01", "original": {"indice": 92.0, "interanual": None}, "desestacionalizada": {"indice": 98.0, "mensual": None}, "tendencia_ciclo": {"indice": 96.0, "mensual": None}}
      ],
      "sectores": [
        {"codigo": "A", "nombre": "Agricultura", "historico": [{"periodo": "2004-01", "indice": 65.0, "interanual": None}]}
      ],
      "impuestos_netos_subsidios": {
        "historico": [{"periodo": "2004-01", "indice": 104.0, "interanual": None}]
      },
    }
    _save_emae(data)
    assert (tmp_path / "emae" / "2004" / "index.json").exists()
    result = json.loads((tmp_path / "emae" / "2004" / "index.json").read_text())
    assert result["fuente"] == "INDEC - Estimador Mensual de Actividad Económica (EMAE)"
    datos = result["datos"]
    assert "nivel_general" in datos
    assert "sectores" in datos
    assert "impuestos_netos_subsidios" in datos
    assert datos["nivel_general"][0]["periodo"] == "2004-01"
    assert datos["sectores"][0]["codigo"] == "A"
    assert datos["impuestos_netos_subsidios"]["historico"][0]["indice"] == 104.0
