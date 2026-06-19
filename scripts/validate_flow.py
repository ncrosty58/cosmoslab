#!/usr/bin/env python3
"""Structural validator for Node-RED flow JSON exported via the Admin API.

Validates wires and link call targets within a single flow file.
Cross-tab references are allowed — unknown link-in IDs from other tabs
are not flagged.
"""
import json
import sys


def validate(flow: dict) -> list[str]:
    errors = []

    nodes = flow.get("nodes")
    if nodes is None:
        return ["No top-level 'nodes' key found."]

    ids = {n.get("id") for n in nodes if "id" in n}
    link_in_ids = {n["id"] for n in nodes if n.get("type") == "link in"}

    # Duplicate IDs within this file
    seen = set()
    for n in nodes:
        nid = n.get("id")
        if nid and nid in seen:
            errors.append(f"Duplicate node id: {nid}")
        if nid:
            seen.add(nid)

    # Broken wires to IDs that don't exist in THIS file
    for n in nodes:
        nid = n.get("id", "<no-id>")
        for wire_group in n.get("wires", []):
            for target in wire_group:
                if target not in ids:
                    errors.append(
                        f"Node '{nid}' ({n.get('type')}) wires to unknown node '{target}'"
                    )

    # Link calls to targets that don't exist in ANY file (can't validate cross-tab)
    # We only check that targets within this file are valid link-in nodes
    referenced_self_link_ins = set()
    for n in nodes:
        nid = n.get("id", "<no-id>")
        if n.get("type") == "link call":
            for t in n.get("links", []):
                if t in ids and t not in link_in_ids:
                    errors.append(f"link call '{nid}' targets '{t}' which is not a link in node")
        elif n.get("type") == "link out" and n.get("mode") == "link":
            for t in n.get("links", []):
                if t in ids and t not in link_in_ids:
                    errors.append(f"link out '{nid}' targets '{t}' which is not a link in node")
                referenced_self_link_ins.add(t)

    # Link-in nodes never referenced from within this file (cross-tab refs are OK)
    for lid in link_in_ids:
        in_same_file_call = False
        for n in nodes:
            if n.get("type") in ("link call",) and lid in n.get("links", []):
                in_same_file_call = True
                break
            if n.get("type") == "link out" and n.get("mode") == "link" and lid in n.get("links", []):
                in_same_file_call = True
                break
    # Only flag if also no wires from within this file target it
        wired_to = False
        for n in nodes:
            for w in n.get("wires", []):
                if lid in w:
                    wired_to = True
                    break
        if not in_same_file_call and not wired_to:
            # It could be called from another tab — only warn, don't fail
            pass  # cross-tab references are allowed

    return errors


def main():
    if len(sys.argv) != 2:
        print("Usage: validate_flow.py <path-to-flow.json>", file=sys.stderr)
        sys.exit(2)

    with open(sys.argv[1]) as f:
        flow = json.load(f)

    errors = validate(flow)
    if errors:
        print(f"FAIL {sys.argv[1]} ({len(errors)} issue(s)):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    print(f"OK   {sys.argv[1]} ({len(flow.get('nodes', []))} nodes)")


if __name__ == "__main__":
    main()
