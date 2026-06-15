#!/usr/bin/env python3
"""Fetch the current `website_leads_tab` flow from a Node-RED instance and
write it to flows/website_leads_tab.json, for syncing this repo after
making live edits via the Admin API.

Usage:
  NODE_RED_URL=http://bodhi.lab:1880 python3 scripts/fetch_flow.py

NODE_RED_URL defaults to http://localhost:1880 if not set.
"""
import json
import os
import urllib.request

FLOW_ID = "website_leads_tab"
OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "flows", "website_leads_tab.json")


def main():
    base_url = os.environ.get("NODE_RED_URL", "http://localhost:1880")
    url = f"{base_url}/flow/{FLOW_ID}"

    req = urllib.request.Request(url, headers={"Node-RED-API-Version": "v2"})
    with urllib.request.urlopen(req) as resp:
        flow = json.load(resp)

    flow.pop("flows", None)

    with open(OUT_PATH, "w") as f:
        json.dump(flow, f, indent=2)
        f.write("\n")

    print(f"Wrote {len(flow.get('nodes', []))} nodes to {OUT_PATH}")


if __name__ == "__main__":
    main()
