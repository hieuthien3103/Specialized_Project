# Claude Code instructions

## Read code first; load data only when needed

For ordinary code changes, debugging, and code review, focus on source and tests. Do not open, parse, summarize, or recursively scan datasets, generated artifacts, caches, or report documents unless the task explicitly asks about them or code behavior cannot be understood without them.

Treat these paths and file types as out of scope by default:

- `cache/**`
- `data/**`
- `dpdp_project/data/**`
- `pdp_100/**`
- `experiments/**/results/**`
- Root-level `*.pdf` and `*.docx`
- Large data/binary files such as `*.graphml`, `*.npz`, `*.osm`, `*.pbf`, and `*.zip`

Prefer reading the relevant files under `src/`, `dpdp_project/`, and `tests/`, plus `README.md`, `pyproject.toml`, and the specific documentation needed for the task. Use dataset README/schema files or a small sample when data format context is necessary; do not load complete datasets by default.

These are reading-scope instructions only. Do not delete, move, or modify excluded files unless explicitly requested.
