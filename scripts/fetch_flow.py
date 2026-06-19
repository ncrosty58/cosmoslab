#!/usr/bin/env python3
"""Fetch a flow from Node-RED and write it to flows/{id}.json.
Strips sensitive env var values (tokens, API keys) before saving.
"""
import json
import os
import re
import urllib.request

FLOW_IDS = [
    "website_leads_tab",
    "curbclass_ninja_tab",
    "crm_shared_tab",
]

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "flows")

SENSITIVE_ENV = re.compile(r"(token|key|secret|password)", re.IGNORECASE)


def _scrub_env(flow: dict) -> dict:
    """Remove values for env vars that look like tokens/keys."""
    for entry in flow.get("env", []):
        name = entry.get("name", "")
        if SENSITIVE_ENV.search(name):
            entry["value"] = ""
            if "type" in entry:
                entry.pop("type")
    return flow


def main():
    base_url = os.environ.get("NODE_RED_URL", "http://bodhi.lab:1880")

    os.makedirs(OUT_DIR, exist_ok=True)

    for flow_id in FLOW_IDS:
        url = f"{base_url}/flow/{flow_id}"
        req = urllib.request.Request(url, headers={"Node-RED-API-Version": "v2"})
        try:
            with urllib.request.urlopen(req) as resp:
                flow = json.load(resp)
        except Exception as e:
            print(f"Failed to fetch {flow_id}: {e}")
            continue

        flow.pop("flows", None)
        _scrub_env(flow)

        out_path = os.path.join(OUT_DIR, f"{flow_id}.json")
        with open(out_path, "w") as f:
            json.dump(flow, f, indent=2)

        print(f"Wrote {len(flow.get('nodes', []))} nodes (scrubbed) to {out_path}")


if __name__ == "__main__":
    main()
