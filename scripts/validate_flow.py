#!/usr/bin/env python3
"""Structural validator for Node-RED flow JSON exported via the Admin API
(`GET /flow/<id>`).

Catches the classes of error that have historically caused silent failures
when editing and deploying this flow:

- A stray top-level `flows` key (in addition to `nodes`) — `PUT /flow/<id>`
  only persists `nodes`, so edits applied to a `flows` list silently vanish.
- Wires that reference node IDs which don't exist in the flow.
- `link call` nodes whose target doesn't exist or isn't a `link in` node.
- `link in` nodes that are never referenced by any `link call`/`link out`.
- `link out` nodes (mode "link") whose declared `links` targets don't exist
  or aren't `link in` nodes.

Usage: python3 validate_flow.py <path-to-flow.json>
Exits non-zero (with a list of problems) if any check fails.
"""
import json
import sys


def validate(flow: dict) -> list[str]:
    errors = []

    if "flows" in flow:
        errors.append(
            "Top-level 'flows' key present alongside 'nodes' — PUT /flow only "
            "persists 'nodes'; remove the stray 'flows' key before deploying."
        )

    nodes = flow.get("nodes")
    if nodes is None:
        errors.append("No top-level 'nodes' key found.")
        return errors

    ids = {n.get("id") for n in nodes if "id" in n}

    dupes = [n["id"] for n in nodes if nodes.count(n) > 1]
    seen = set()
    for n in nodes:
        nid = n.get("id")
        if nid in seen:
            errors.append(f"Duplicate node id: {nid}")
        seen.add(nid)

    for n in nodes:
        nid = n.get("id", "<no-id>")
        for wire_group in n.get("wires", []):
            for target in wire_group:
                if target not in ids:
                    errors.append(
                        f"Node '{nid}' ({n.get('type')}) wires to unknown node id '{target}'"
                    )

    link_in_ids = {n["id"] for n in nodes if n.get("type") == "link in"}
    link_call_targets = set()
    link_out_link_targets = set()

    for n in nodes:
        nid = n.get("id", "<no-id>")
        if n.get("type") == "link call":
            targets = n.get("links", [])
            if not targets:
                errors.append(f"link call '{nid}' has no target in 'links'")
            for t in targets:
                link_call_targets.add(t)
                if t not in ids:
                    errors.append(f"link call '{nid}' targets unknown node id '{t}'")
                elif t not in link_in_ids:
                    errors.append(f"link call '{nid}' targets '{t}', which is not a link in node")
        elif n.get("type") == "link out" and n.get("mode") == "link":
            for t in n.get("links", []):
                link_out_link_targets.add(t)
                if t not in ids:
                    errors.append(f"link out '{nid}' targets unknown node id '{t}'")
                elif t not in link_in_ids:
                    errors.append(f"link out '{nid}' targets '{t}', which is not a link in node")

    referenced_link_ins = link_call_targets | link_out_link_targets
    for lid in link_in_ids:
        if lid not in referenced_link_ins:
            errors.append(f"link in '{lid}' is never referenced by any link call/link out")

    return errors


def main():
    if len(sys.argv) != 2:
        print("Usage: validate_flow.py <path-to-flow.json>", file=sys.stderr)
        sys.exit(2)

    with open(sys.argv[1]) as f:
        flow = json.load(f)

    errors = validate(flow)
    if errors:
        print(f"Validation FAILED for {sys.argv[1]} ({len(errors)} issue(s)):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    print(f"Validation OK: {sys.argv[1]} ({len(flow.get('nodes', []))} nodes)")


if __name__ == "__main__":
    main()
