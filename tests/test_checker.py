import sys
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from checker import load_metadata, save_metadata


class TestLoadMetadata:
  def test_load_existing(self, tmp_path):
    file = tmp_path / "metadata.json"
    file.write_text(json.dumps({"ipc": {"last-modified": "Mon, 01 Jan 2026 00:00:00 GMT"}}))
    result = load_metadata(file)
    assert result == {"ipc": {"last-modified": "Mon, 01 Jan 2026 00:00:00 GMT"}}

  def test_load_nonexistent(self, tmp_path):
    file = tmp_path / "metadata.json"
    result = load_metadata(file)
    assert result == {}

  def test_load_empty(self, tmp_path):
    file = tmp_path / "metadata.json"
    file.write_text("{}")
    result = load_metadata(file)
    assert result == {}


class TestSaveMetadata:
  def test_save_and_reload(self, tmp_path):
    file = tmp_path / "metadata.json"
    data = {"ica": {"last-modified": "Tue, 14 Jul 2026 19:06:04 GMT"}}
    save_metadata(file, data)
    loaded = load_metadata(file)
    assert loaded == data

  def test_overwrite(self, tmp_path):
    file = tmp_path / "metadata.json"
    save_metadata(file, {"a": 1})
    save_metadata(file, {"b": 2})
    loaded = load_metadata(file)
    assert loaded == {"b": 2}
