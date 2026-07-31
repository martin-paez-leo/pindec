import sys
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from utils import (
  to_native,
  write_json,
  load_json,
  extract_year,
  group_by_year,
  merge,
)

import numpy as np


class TestToNative:
  def test_numpy_int(self):
    assert to_native(np.int64(5)) == 5
    assert isinstance(to_native(np.int64(5)), int)

  def test_numpy_float(self):
    assert to_native(np.float64(3.14)) == 3.14
    assert isinstance(to_native(np.float64(3.14)), float)

  def test_numpy_array(self):
    result = to_native(np.array([1]))
    assert result == 1

  def test_dict(self):
    result = to_native({"a": np.int64(1), "b": np.float64(2.0)})
    assert result == {"a": 1, "b": 2.0}

  def test_nested(self):
    result = to_native({"a": [np.int64(1), {"b": np.float64(2.0)}]})
    assert result == {"a": [1, {"b": 2.0}]}

  def test_plain_python(self):
    assert to_native(42) == 42
    assert to_native("hello") == "hello"
    assert to_native(None) is None
    assert to_native([1, 2]) == [1, 2]


class TestWriteJson:
  def test_creates_file(self, tmp_path):
    path = tmp_path / "test.json"
    write_json(path, {"key": "value"})
    assert path.exists()
    assert json.loads(path.read_text()) == {"key": "value"}

  def test_creates_dirs(self, tmp_path):
    path = tmp_path / "sub" / "dir" / "test.json"
    write_json(path, {"nested": True})
    assert path.exists()

  def test_unicode(self, tmp_path):
    path = tmp_path / "test.json"
    write_json(path, {"nombre": "Índice"})
    data = json.loads(path.read_text())
    assert data["nombre"] == "Índice"


class TestLoadJson:
  def test_load_existing(self, tmp_path):
    path = tmp_path / "test.json"
    path.write_text('{"a": 1}')
    assert load_json(path) == {"a": 1}

  def test_load_nonexistent(self, tmp_path):
    path = tmp_path / "test.json"
    assert load_json(path) is None


class TestExtractYear:
  def test_basic(self):
    assert extract_year("2026-01") == 2026

  def test_earlier_year(self):
    assert extract_year("1990-12") == 1990

  def test_single_digit_month(self):
    assert extract_year("2004-1") == 2004


class TestGroupByYear:
  def test_basic(self):
    records = [
      {"periodo": "2026-01", "valor": 1},
      {"periodo": "2026-02", "valor": 2},
      {"periodo": "2025-12", "valor": 3},
    ]
    result = group_by_year(records, "periodo")
    assert 2026 in result
    assert 2025 in result
    assert len(result[2026]) == 2
    assert len(result[2025]) == 1

  def test_different_date_key(self):
    records = [
      {"fecha": "2026-01", "valor": 1},
      {"fecha": "2026-02", "valor": 2},
    ]
    result = group_by_year(records, "fecha")
    assert len(result[2026]) == 2

  def test_empty(self):
    result = group_by_year([], "periodo")
    assert result == {}


class TestMerge:
  def test_merge_new_records(self):
    existing = [{"periodo": "2026-01", "v": 1}]
    new = [{"periodo": "2026-02", "v": 2}]
    result = merge(existing, new, "periodo")
    assert len(result) == 2

  def test_dedup(self):
    existing = [{"periodo": "2026-01", "v": 1}]
    new = [{"periodo": "2026-01", "v": 99}]
    result = merge(existing, new, "periodo")
    assert len(result) == 1
    assert result[0]["v"] == 1

  def test_merge_preserves_existing(self):
    existing = [{"periodo": "2026-01", "v": 1}]
    new = [{"periodo": "2026-01", "v": 99}, {"periodo": "2026-02", "v": 2}]
    result = merge(existing, new, "periodo")
    assert len(result) == 2
    assert result[0]["v"] == 1

  def test_different_date_key(self):
    existing = [{"fecha": "2026-01"}]
    new = [{"fecha": "2026-02"}]
    result = merge(existing, new, "fecha")
    assert len(result) == 2
