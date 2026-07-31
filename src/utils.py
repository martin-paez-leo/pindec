import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_DIR = ROOT / "api" / "v1"
CONFIG_DIR = ROOT / "config"

def to_native(value):
  if hasattr(value, "item"):
    return value.item()
  if isinstance(value, dict):
    return {k: to_native(v) for k, v in value.items()}
  if isinstance(value, list):
    return [to_native(v) for v in value]
  return value

def write_json(path: Path, data: dict | list):
  path.parent.mkdir(parents=True, exist_ok=True)
  with open(path, "w") as f:
    json.dump(to_native(data), f, indent=2, ensure_ascii=False)

def load_json(path: Path) -> dict | list | None:
  if path.exists():
    with open(path, "r") as f:
      return json.load(f)
  return None

def extract_year(date_str: str) -> int:
  return int(date_str[:4])

def group_by_year(records: list[dict], date_key: str) -> dict[int, list[dict]]:
  groups: dict[int, list[dict]] = {}
  for record in records:
    year = extract_year(record[date_key])
    groups.setdefault(year, []).append(record)
  return groups

def merge(existing: list[dict], new: list[dict], date_key: str) -> list[dict]:
  seen = {r[date_key] for r in existing}
  for record in new:
    if record[date_key] not in seen:
      existing.append(record)
      seen.add(record[date_key])
  return existing