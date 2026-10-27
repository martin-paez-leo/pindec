#!/usr/bin/env python3

import json
import os
import sys

BASE = sys.argv[1] if len(sys.argv) > 1 else "https://pindec.dev"
API_DIR = os.path.join(os.path.dirname(__file__), "..", "api", "v1")


def load(path):
    with open(path) as f:
        return json.load(f)


def is_year(name):
    return name.isdigit() and len(name) == 4


def collect():
    urls = ["/v1/", "/v1/index.json", "/v1/meta.json"]

    for root, dirs, files in os.walk(API_DIR):
        dirs.sort()
        if "index.json" not in files:
            continue

        rel = os.path.relpath(root, API_DIR).replace(os.sep, "/")
        if rel == "." or is_year(rel.rsplit("/", 1)[-1]):
            continue

        urls.append(f"/v1/{rel}/")

        index = load(os.path.join(root, "index.json"))
        years = index.get("anos_disponibles") or []
        if not years:
            years = [d for d in dirs if is_year(d)]
        if years:
            urls.append(f"/v1/{rel}/{max(years)}/")

    return sorted(set(urls))


def main():
    for url in collect():
        print(BASE + url)


if __name__ == "__main__":
    main()
