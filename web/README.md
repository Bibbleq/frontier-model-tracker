# Web

Static pages published to GitHub Pages by `.github/workflows/publish-pages.yml`.
No build step and no dependencies: they fetch the generated JSON at runtime
rather than embedding historical claims in UI code.

- `index.html` — the data front door. Links every generated file and explains
  the three distinctions a consumer has to respect to read the data correctly.
- `dashboard.html` — the editorial dashboard. Build warnings as a work queue,
  open research questions, claims at `supported` confidence, coverage gaps and
  lag answerability.
- `style.css` — shared styling, light and dark.

## Why the dashboard is generated rather than tracked in Issues

Everything on the dashboard is derived from `data/events.yaml` and
`generated/status.json` on every build. Mirroring the validation backlog into
GitHub Issues would create a second copy of state the schema already models
(`open`, `promoted`, `rejected`, `blocked`), and the two would drift. Resolve an
item by editing the YAML; the row disappears on the next build.

## Local preview

The workflow assembles `_site/` with the generated files under `data/`. To
reproduce that locally:

```bash
mkdir -p web/data
cp generated/events.json generated/status.json generated/*.csv web/data/
python -m http.server 8815 --directory web
```

`web/data/` is gitignored; the published copy is assembled by CI.

## Still to come

The public timeline renderer. The 365Explained WordPress integration will
consume the published JSON from Pages rather than holding its own copy of the
data — see `../wordpress/README.md`.
