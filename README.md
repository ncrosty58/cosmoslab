# cosmoslab — Node-RED flows

Version-controlled mirror of the Node-RED flows running on `bodhi.lab:1880`.

## Layout

```
flows/                    # Flow JSON snapshots (one file per tab)
scripts/
  fetch_flow.py           # Pull current flow from bodhi.lab → flows/
  validate_flow.py        # Structural validator (runs in CI)
.github/workflows/
  validate-flow.yml       # CI: runs validator on every push/PR
```

## Syncing after live edits

Node-RED is the source of truth. After making changes in the editor:

```bash
NODE_RED_URL=http://bodhi.lab:1880 python3 scripts/fetch_flow.py
python3 scripts/validate_flow.py flows/website_leads_tab.json
git add flows/ && git commit -m "sync: <description>" && git push
```

## CI

GitHub Actions runs `validate_flow.py` on every push or PR touching `flows/**.json`.
It checks structural integrity only — it cannot deploy to `bodhi.lab` (private LAN).

## Gotchas

- **`nodes` vs `flows` key**: `GET /flow/<id>` returns `{id, label, env, nodes, ...}`.
  `PUT /flow/<id>` persists only `nodes`. A stray top-level `flows` key causes silent
  data loss on deploy — `fetch_flow.py` strips it automatically.
- **Credentials**: Flow-level secrets (`CURBCLASS_TWENTY_TOKEN`, `CHASSISSHIELD_TWENTY_TOKEN`,
  `GEMINI_API_KEY`, `CURBCLASS_INVOICENINJA_TOKEN`) are stored as `type: cred` env entries,
  encrypted at rest in `flows_cred.json` on the Node-RED host. They never appear in the
  flow JSON returned by the API and are not committed here.
