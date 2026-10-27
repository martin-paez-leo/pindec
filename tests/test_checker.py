import sys
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import checker
from checker import load_metadata, save_metadata, needs_update


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

  def test_creates_parent_directory(self, tmp_path):
    file = tmp_path / "config" / "metadata.json"
    save_metadata(file, {"a": 1})
    assert file.exists()


class TestNeedsUpdateSingleUrl:
  def test_unchanged(self, monkeypatch):
    monkeypatch.setattr(checker, "check_update", lambda url: "Mon, 01 Jan 2026 00:00:00 GMT")
    changed, remote = needs_update({"last-modified": "Mon, 01 Jan 2026 00:00:00 GMT"}, "http://x/a.xls")
    assert changed is False
    assert remote == "Mon, 01 Jan 2026 00:00:00 GMT"

  def test_changed(self, monkeypatch):
    monkeypatch.setattr(checker, "check_update", lambda url: "Tue, 02 Jan 2026 00:00:00 GMT")
    changed, remote = needs_update({"last-modified": "Mon, 01 Jan 2026 00:00:00 GMT"}, "http://x/a.xls")
    assert changed is True

  def test_first_run_without_metadata(self, monkeypatch):
    monkeypatch.setattr(checker, "check_update", lambda url: "Mon, 01 Jan 2026 00:00:00 GMT")
    changed, _ = needs_update({}, "http://x/a.xls")
    assert changed is True


class TestNeedsUpdateMultipleUrls:
  URLS = {"monthly": "http://x/m.xls", "activity": "http://x/a.xls"}

  def test_all_unchanged(self, monkeypatch):
    monkeypatch.setattr(checker, "check_update", lambda url: "Mon, 01 Jan 2026 00:00:00 GMT")
    local = {"last-modified": {"monthly": "Mon, 01 Jan 2026 00:00:00 GMT", "activity": "Mon, 01 Jan 2026 00:00:00 GMT"}}
    changed, _ = needs_update(local, self.URLS)
    assert changed is False

  def test_all_changed(self, monkeypatch):
    monkeypatch.setattr(checker, "check_update", lambda url: "Tue, 02 Jan 2026 00:00:00 GMT")
    local = {"last-modified": {"monthly": "Mon, 01 Jan 2026 00:00:00 GMT", "activity": "Mon, 01 Jan 2026 00:00:00 GMT"}}
    changed, _ = needs_update(local, self.URLS)
    assert changed is True

  def test_one_changed_is_enough(self, monkeypatch):
    remote = {"http://x/m.xls": "Mon, 01 Jan 2026 00:00:00 GMT", "http://x/a.xls": "Tue, 02 Jan 2026 00:00:00 GMT"}
    monkeypatch.setattr(checker, "check_update", lambda url: remote[url])
    local = {"last-modified": {"monthly": "Mon, 01 Jan 2026 00:00:00 GMT", "activity": "Mon, 01 Jan 2026 00:00:00 GMT"}}
    changed, _ = needs_update(local, self.URLS)
    assert changed is True

  def test_one_unchanged_is_not_enough(self, monkeypatch):
    remote = {"http://x/m.xls": "Tue, 02 Jan 2026 00:00:00 GMT", "http://x/a.xls": "Mon, 01 Jan 2026 00:00:00 GMT"}
    monkeypatch.setattr(checker, "check_update", lambda url: remote[url])
    local = {"last-modified": {"monthly": "Tue, 02 Jan 2026 00:00:00 GMT", "activity": "Mon, 01 Jan 2026 00:00:00 GMT"}}
    changed, _ = needs_update(local, self.URLS)
    assert changed is False

  def test_invalid_type_raises(self):
    import pytest
    with pytest.raises(ValueError):
      needs_update({}, ["http://x/a.xls"])


class TestNeedsUpdateMissingHeader:
  def test_missing_header_is_stale(self, monkeypatch):
    monkeypatch.setattr(checker, "check_update", lambda url: None)
    changed, remote = needs_update({"last-modified": None}, "http://x/a.xls")
    assert changed is True
    assert remote is None

  def test_missing_header_stays_stale_after_first_run(self, monkeypatch):
    monkeypatch.setattr(checker, "check_update", lambda url: None)
    first, _ = needs_update({}, "http://x/a.xls")
    second, _ = needs_update({"last-modified": None}, "http://x/a.xls")
    assert first is True
    assert second is True

  def test_missing_header_in_multipart_is_stale(self, monkeypatch):
    monkeypatch.setattr(checker, "check_update", lambda url: None)
    local = {"last-modified": {"monthly": None, "activity": None}}
    changed, _ = needs_update(local, TestNeedsUpdateMultipleUrls.URLS)
    assert changed is True

  def test_present_header_still_compares(self, monkeypatch):
    monkeypatch.setattr(checker, "check_update", lambda url: "Mon, 01 Jan 2026 00:00:00 GMT")
    changed, _ = needs_update({"last-modified": "Mon, 01 Jan 2026 00:00:00 GMT"}, "http://x/a.xls")
    assert changed is False
