#!/usr/bin/env python3

import json
import os
import sys

BASE = sys.argv[1] if len(sys.argv) > 1 else "https://pindec.pages.dev"
API_DIR = os.path.join(os.path.dirname(__file__), "..", "api", "v1")


def load(path):
    with open(path) as f:
        return json.load(f)


def main():
    urls = ["/v1/", "/v1/index.json"]

    for ind in ("ipc", "cba-cbt", "emae", "ica"):
        index_path = os.path.join(API_DIR, ind, "index.json")
        index = load(index_path)
        urls.append(f"/v1/{ind}/")

        if ind == "ipc":
            for region in index.get("regiones", []):
                region_path = os.path.join(API_DIR, "ipc", region, "index.json")
                region_index = load(region_path)
                urls.append(f"/v1/ipc/{region}/")
                for year in region_index.get("anos_disponibles", []):
                    urls.append(f"/v1/ipc/{region}/{year}/")
        else:
            for year in index.get("anos_disponibles", []):
                urls.append(f"/v1/{ind}/{year}/")

    for url in urls:
        print(BASE + url)


if __name__ == "__main__":
    main()
