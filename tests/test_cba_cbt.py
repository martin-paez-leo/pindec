import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd
import pytest

from extractors.cba_cbt import _data_window


def _sheet(dates, values, footnotes):
  """Reconstruye una hoja: cabecera, filas de datos y pie de notas."""
  rows = [["Fuente de prueba", None, None, None]]
  for date, value in zip(dates, values):
    rows.append([pd.Timestamp(date), value, value * 2, None])
  rows.extend(footnotes)
  return pd.DataFrame(rows)


class TestDataWindow:
  def test_returns_only_dates(self):
    df = _sheet(
      ["2026-01-01", "2026-02-01"],
      [100.0, 110.0],
      [["Fuente: INDEC", None, None, None]],
    )
    window = _data_window(df, 8)
    assert window.iloc[:, 0].tolist() == [pd.Timestamp("2026-01-01"), pd.Timestamp("2026-02-01")]

  def test_excludes_footnote_block(self):
    """El pie de notas no es una fecha, asi que nunca debe entrar."""
    df = _sheet(
      ["2026-01-01", "2026-02-01"],
      [100.0, 110.0],
      [
        ["Nota:", None, None, None],
        ["Hogar 1: de tres integrantes", None, None, None],
        ["Fuente: INDEC", None, None, None],
      ],
    )
    window = _data_window(df, 8)
    assert len(window) == 2
    assert "Nota:" not in window.iloc[:, 0].astype(str).tolist()

  def test_limits_to_window(self):
    dates = pd.date_range("2025-01-01", periods=20, freq="MS").strftime("%Y-%m-%d")
    df = _sheet(dates, range(20), [["Fuente: INDEC", None, None, None]])
    assert len(_data_window(df, 8)) == 8

  def test_window_larger_than_data(self):
    df = _sheet(
      ["2026-01-01", "2026-02-01"],
      [100.0, 110.0],
      [["Fuente: INDEC", None, None, None]],
    )
    assert len(_data_window(df, 50)) == 2

  def test_window_starts_at_last_dates(self):
    df = _sheet(
      ["2026-01-01", "2026-02-01", "2026-03-01"],
      [100.0, 110.0, 120.0],
      [["Fuente: INDEC", None, None, None]],
    )
    window = _data_window(df, 2)
    assert window.iloc[:, 0].tolist() == [pd.Timestamp("2026-02-01"), pd.Timestamp("2026-03-01")]

  def test_sheet_without_dates_is_empty(self):
    df = pd.DataFrame([["Solo notas", None], ["Fuente: INDEC", None]])
    assert _data_window(df, 8).empty

  def test_empty_sheet(self):
    assert _data_window(pd.DataFrame(), 8).empty

  def test_drops_all_empty_columns(self):
    """La columna fantasma entre cba y cbt debe caer antes de mapear."""
    df = pd.DataFrame(
      [
        ["2026-01-01", 100.0, None, 200.0],
        ["2026-02-01", 110.0, None, 220.0],
        ["Fuente: INDEC", None, None, None],
      ]
    )
    window = _data_window(df, 8)
    assert len(window.columns) == 3