import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from extractors.common import to_float, date_from_yyyymm, month_code


class TestMonthCode:
  def test_plain_month(self):
    assert month_code("Julio") == "07"

  def test_estimated_suffix(self):
    assert month_code("Julioe") == "07"
    assert month_code("Agostoe") == "08"

  def test_asterisk_suffix(self):
    assert month_code("Mayo*") == "05"

  def test_surrounding_whitespace(self):
    assert month_code("  Junio  ") == "06"

  def test_case_insensitive(self):
    assert month_code("septiembre") == "09"

  def test_all_months(self):
    assert [month_code(m) for m in
            ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
             "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
            ] == ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]

  def test_unknown_month_raises(self):
    import pytest
    with pytest.raises(ValueError):
      month_code("Foo")

  def test_empty_month_raises(self):
    import pytest
    with pytest.raises(ValueError):
      month_code("")


class TestToFloat:
  def test_integer(self):
    assert to_float(42) == 42.0

  def test_float(self):
    assert to_float(3.14) == 3.14

  def test_string_integer(self):
    assert to_float("100") == 100.0

  def test_string_float_with_dot(self):
    assert to_float("3.14") == 3.14

  def test_string_float_with_comma(self):
    assert to_float("3,14") == 3.14

  def test_none(self):
    assert to_float(None) is None

  def test_nan(self):
    import pandas as pd
    assert to_float(pd.NA) is None
    assert to_float(float("nan")) is None

  def test_placeholder_dots(self):
    assert to_float("..") is None
    assert to_float("...") is None
    assert to_float("///") is None

  def test_placeholder_na(self):
    assert to_float("na") is None
    assert to_float("n/a") is None

  def test_placeholder_dash(self):
    assert to_float("-") is None

  def test_empty_string(self):
    assert to_float("") is None

  def test_invalid_string(self):
    assert to_float("abc") is None

  def test_negative(self):
    assert to_float(-5.5) == -5.5

  def test_custom_decimals(self):
    assert to_float(3.14159, decimals=2) == 3.14


class TestDateFromYyyymm:
  def test_basic(self):
    assert date_from_yyyymm("201612") == "2016-12"

  def test_single_digit_month(self):
    assert date_from_yyyymm("201604") == "2016-04"

  def test_integer_input(self):
    assert date_from_yyyymm(201612) == "2016-12"

  def test_recent_date(self):
    assert date_from_yyyymm("202601") == "2026-01"
