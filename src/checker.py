from pathlib import Path
import requests
import json

TIMEOUT_HEAD = 15

def load_metadata(file_path: Path) -> dict:
  if not file_path.exists():
    return {}

  with open(file_path, 'r') as file:
    return json.load(file)

def save_metadata(file_path: Path, metadata: dict):
  with open(file_path, 'w') as file:
    json.dump(metadata, file, indent=2)
    
def check_update(url: str) -> str | None:
  response = requests.head(url, timeout=TIMEOUT_HEAD, allow_redirects=True)
  response.raise_for_status()
  
  return response.headers.get('Last-Modified') 

def needs_update_simple(local_metadata: dict | None, url: str) -> tuple[bool, str | None]:
  local_last_modified = local_metadata.get('last_modified')
  remote_last_modified = check_update(url)
  
  return local_last_modified != remote_last_modified, remote_last_modified

def needs_update_multiple(local_metadata: dict | None, urls: dict) -> tuple[bool, dict | None]:
  local_last_modified = (local_metadata).get('last_modified')
  remote_last_modified = {}
  
  for key, url in urls.items():
    remote_last_modified[key] = check_update(url)

  all_changed = all(remote_last_modified[key] != local_last_modified.get(key) for key in urls)

  return all_changed, remote_last_modified