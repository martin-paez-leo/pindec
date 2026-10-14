import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from extractors.emae import _build_period


class TestBuildPeriod:
  def test_plain_month(self):
    assert _build_period({"mes": "Junio", "anio": 2026}) == "2026-06"

  def test_year_with_asterisk(self):
    assert _build_period({"mes": "Marzo", "anio": "2026*"}) == "2026-03"

  def test_year_with_asterisk_and_whitespace(self):
    assert _build_period({"mes": "Marzo", "anio": " 2026* "}) == "2026-03"

  def test_estimated_month_suffix(self):
    assert _build_period({"mes": "Mayoe", "anio": 2026}) == "2026-05"

  def test_unknown_month_raises(self):
    import pytest
    with pytest.raises(ValueError):
      _build_period({"mes": "Foo", "anio": 2026})

  def test_non_numeric_year_raises(self):
    import pytest
    with pytest.raises(ValueError):
      _build_period({"mes": "Mayo", "anio": "N/D"})