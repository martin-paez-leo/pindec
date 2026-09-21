import sys
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from main import _save_ipc, _save_cba_cbt, _save_ica, _save_emae, _merge_into_existing, _merge_sectores, _update_emae_skiprows, _update_cba_cbt_skiprows, _update_default_skiprows


class TestUpdateSkiprows:
  def test_update_emae_skiprows(self, tmp_path, monkeypatch):
    sheets = {
      "monthly": [{"name": "Tabla", "skiprows": 270, "columns": []}],
      "activity": [
        {"name": "Tabla Letras", "skiprows": 270, "columns": []},
        {"name": "Tabla Var Letras", "skiprows": 260, "columns": []},
      ]
    }
    new_skiprows = {
      "monthly": [{"name": "Tabla", "skiprows": 275, "columns": []}],
      "activity": [
        {"name": "Tabla Letras", "skiprows": 274, "columns": []},
        {"name": "Tabla Var Letras", "skiprows": 263, "columns": []},
      ]
    }
    _update_emae_skiprows(sheets, new_skiprows)
    assert sheets["monthly"][0]["skiprows"] == 275
    assert sheets["activity"][0]["skiprows"] == 274
    assert sheets["activity"][1]["skiprows"] == 263

  def test_update_cba_cbt_skiprows(self, tmp_path, monkeypatch):
    sheets = [
      {"name": "CBA-CBT", "skiprows": 130, "columns": []},
      {"name": "Variaciones", "skiprows": 131, "columns": []},
      {"name": "Hogares", "skiprows": 130, "columns": []},
    ]
    new_skiprows = {"CBA-CBT": 132, "Variaciones": 133, "Hogares": 132}
    _update_cba_cbt_skiprows(sheets, new_skiprows)
    assert sheets[0]["skiprows"] == 132
    assert sheets[1]["skiprows"] == 133
    assert sheets[2]["skiprows"] == 132

  def test_update_default_skiprows(self, tmp_path, monkeypatch):
    sheets = [{"name": "FOB-CIF", "skiprows": 479, "columns": []}]
    new_skiprows = {"sheets": [{"name": "FOB-CIF", "skiprows": 481, "columns": []}]}
    _update_default_skiprows(sheets, new_skiprows)
    assert sheets[0]["skiprows"] == 481
  

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


class TestMergeIntoExistingComplete:
  def test_overlap_merges_historico(self):
    datos = {
      "Nacional": {
        "COICOP": [{"codigo": "0", "nombre": "Nivel", "historico": [{"periodo": "2026-01", "indice": 100}]}]
      }
    }
    new = {
      "Nacional": {
        "COICOP": [{"codigo": "0", "nombre": "Nivel", "historico": [{"periodo": "2026-02", "indice": 102}]}]
      }
    }
    _merge_into_existing(datos, new)
    
    hist = datos["Nacional"]["COICOP"][0]["historico"]
    assert len(hist) == 2
    assert hist[0]["periodo"] == "2026-01"
    assert hist[1]["periodo"] == "2026-02"

  def test_new_code_added(self):
    datos = {
      "Nacional": {
        "COICOP": [{"codigo": "0", "nombre": "Nivel", "historico": [{"periodo": "2026-01", "indice": 100}]}]
      }
    }
    new = {
      "Nacional": {
        "COICOP": [
          {"codigo": "1", "nombre": "Alimentos", "historico": [{"periodo": "2026-01", "indice": 90}]}
        ]
      }
    }
    _merge_into_existing(datos, new)
    
    codes = [c["codigo"] for c in datos["Nacional"]["COICOP"]]
    assert "0" in codes
    assert "1" in codes

  def test_old_code_preserved(self):
    datos = {
      "Nacional": {
        "COICOP": [{"codigo": "0", "historico": [{"periodo": "2026-01", "indice": 100}]},
                   {"codigo": "1", "historico": [{"periodo": "2026-01", "indice": 90}]}]
      }
    }
    new = {
      "Nacional": {
        "COICOP": [{"codigo": "0", "historico": [{"periodo": "2026-02", "indice": 102}]}]
      }
    }
    _merge_into_existing(datos, new)
    
    codes = [c["codigo"] for c in datos["Nacional"]["COICOP"]]
    assert "0" in codes
    assert "1" in codes

  def test_no_duplicates_in_historico(self):
    datos = {
      "Nacional": {
        "COICOP": [{"codigo": "0", "historico": [{"periodo": "2026-01", "indice": 100}]}]
      }
    }
    new = {
      "Nacional": {
        "COICOP": [{"codigo": "0", "historico": [{"periodo": "2026-01", "indice": 999}]}]
      }
    }
    _merge_into_existing(datos, new)
    
    hist = datos["Nacional"]["COICOP"][0]["historico"]
    assert len(hist) == 1
    assert hist[0]["indice"] == 100

  def test_multiple_regions_independent(self):
    datos = {
      "Nacional": {"COICOP": [{"codigo": "0", "historico": [{"periodo": "2026-01", "indice": 100}]}]},
      "GBA": {"COICOP": [{"codigo": "0", "historico": [{"periodo": "2026-01", "indice": 200}]}]},
    }
    new = {
      "Nacional": {"COICOP": [{"codigo": "0", "historico": [{"periodo": "2026-02", "indice": 102}]}]},
      "GBA": {"COICOP": [{"codigo": "0", "historico": [{"periodo": "2026-02", "indice": 202}]}]},
    }
    _merge_into_existing(datos, new)
    
    nac_hist = datos["Nacional"]["COICOP"][0]["historico"]
    gba_hist = datos["GBA"]["COICOP"][0]["historico"]
    assert len(nac_hist) == 2
    assert len(gba_hist) == 2
    assert nac_hist[1]["indice"] == 102
    assert gba_hist[1]["indice"] == 202

  def test_empty_existing(self):
    datos = {}
    new = {
      "Nacional": {"COICOP": [{"codigo": "0", "historico": [{"periodo": "2026-01", "indice": 100}]}]}
    }
    _merge_into_existing(datos, new)
    
    assert "Nacional" in datos
    assert len(datos["Nacional"]["COICOP"]) == 1


class TestMergeSectoresComplete:
  def test_overlap_merges_historico(self):
    old = [{"codigo": "A", "nombre": "Agricultura", "historico": [{"periodo": "2026-01", "indice": 95}]}]
    new = [{"codigo": "A", "nombre": "Agricultura", "historico": [{"periodo": "2026-02", "indice": 97}]}]
    
    result = _merge_sectores(old, new)
    assert len(result) == 1
    assert len(result[0]["historico"]) == 2

  def test_new_code_added(self):
    old = [{"codigo": "A", "nombre": "Agricultura", "historico": [{"periodo": "2026-01", "indice": 95}]}]
    new = [{"codigo": "B", "nombre": "Pesca", "historico": [{"periodo": "2026-01", "indice": 110}]}]
    
    result = _merge_sectores(old, new)
    codes = [s["codigo"] for s in result]
    assert "A" in codes
    assert "B" in codes

  def test_old_code_preserved(self):
    old = [{"codigo": "A", "historico": [{"periodo": "2026-01", "indice": 95}]},
           {"codigo": "B", "historico": [{"periodo": "2026-01", "indice": 110}]}]
    new = [{"codigo": "A", "historico": [{"periodo": "2026-02", "indice": 97}]}]
    
    result = _merge_sectores(old, new)
    codes = [s["codigo"] for s in result]
    assert "A" in codes
    assert "B" in codes

  def test_no_duplicates(self):
    old = [{"codigo": "A", "historico": [{"periodo": "2026-01", "indice": 95}]}]
    new = [{"codigo": "A", "historico": [{"periodo": "2026-01", "indice": 999}]}]
    
    result = _merge_sectores(old, new)
    assert len(result[0]["historico"]) == 1
    assert result[0]["historico"][0]["indice"] == 95

  def test_empty_old(self):
    old = []
    new = [{"codigo": "A", "historico": [{"periodo": "2026-01", "indice": 95}]}]
    
    result = _merge_sectores(old, new)
    assert len(result) == 1
    assert result[0]["codigo"] == "A"


class TestRunEndToEnd:
  def test_extracts_and_saves_all_indicators(self, tmp_path, monkeypatch):
    monkeypatch.setattr("main.API_DIR", tmp_path)
    monkeypatch.setattr("main.CONFIG_PATH", tmp_path / "config.json")
    monkeypatch.setattr("main.METADATA_PATH", tmp_path / "metadata.json")

    config = {
      "ipc": {"url": "http://fake/url.csv", "separator": ";", "encoding": "latin-1", "sheets": []},
      "cba-cbt": {"url": "http://fake/url.xls", "sheets": [{"name": "CBA-CBT", "skiprows": 130, "columns": []}]},
      "emae": {"urls": {"monthly": "http://fake/m.xls", "activity": "http://fake/a.xls"}, "sheets": {"monthly": [{"name": "Tabla", "skiprows": 270, "columns": []}], "activity": [{"name": "Tabla Letras", "skiprows": 270, "columns": []}, {"name": "Tabla Var Letras", "skiprows": 260, "columns": []}]}},
      "ica": {"url": "http://fake/ica.xls", "sheets": [{"name": "FOB-CIF", "skiprows": 479, "columns": []}]},
    }
    (tmp_path / "config.json").write_text(json.dumps(config))
    (tmp_path / "metadata.json").write_text("{}")

    calls = {"ipc": 0, "cba-cbt": 0, "emae": 0, "ica": 0}

    def extract_ipc(config):
      calls["ipc"] += 1
      return [], None

    def extract_cba(config):
      calls["cba-cbt"] += 1
      return {"adulto_equivalente": [], "hogares": []}, {"CBA-CBT": 131, "Variaciones": 132, "Hogares": 131}

    def extract_emae(config):
      calls["emae"] += 1
      return {"nivel_general": [], "sectores": [], "impuestos_netos_subsidios": {"historico": []}}, {"monthly": [{"name": "Tabla", "skiprows": 275, "columns": []}], "activity": [{"name": "Tabla Letras", "skiprows": 274, "columns": []}, {"name": "Tabla Var Letras", "skiprows": 263, "columns": []}]}

    def extract_ica(config):
      calls["ica"] += 1
      return [], {"sheets": [{"name": "FOB-CIF", "skiprows": 481, "columns": []}]}

    monkeypatch.setattr("checker.check_update", lambda url: "Mon, 01 Sep 2026 00:00:00 GMT")
    monkeypatch.setattr("main.EXTRACTORS", {
      "ipc": type("E", (), {"extract": staticmethod(extract_ipc)})(),
      "cba-cbt": type("E", (), {"extract": staticmethod(extract_cba)})(),
      "emae": type("E", (), {"extract": staticmethod(extract_emae)})(),
      "ica": type("E", (), {"extract": staticmethod(extract_ica)})(),
    })

    from main import run
    run()

    assert calls["ipc"] == 1
    assert calls["cba-cbt"] == 1
    assert calls["emae"] == 1
    assert calls["ica"] == 1

    saved_config = json.loads((tmp_path / "config.json").read_text())
    assert saved_config["cba-cbt"]["sheets"][0]["skiprows"] == 131

    saved_metadata = json.loads((tmp_path / "metadata.json").read_text())
    assert saved_metadata["ipc"]["last-modified"] == "Mon, 01 Sep 2026 00:00:00 GMT"
