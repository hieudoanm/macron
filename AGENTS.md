# AGENTS.md — Macron

Guidance for AI agents working in this repository.

## What this is

Macron ("Markdown + Neuron") is a data pipeline that turns the WordsAPI
word list into a linked markdown knowledge base and an interactive
word-relationship graph published via GitHub Pages from `docs/`.

## Repository layout

| Path                    | Contents                                                              |
| ----------------------- | --------------------------------------------------------------------- |
| `pipeline/`             | Numbered stages `01`–`07` (words → tokens → frequency → results → md → meta → graph) |
| `scripts/`              | Utilities: `convert.py`, `stopwords.py`, `analysis.py`, `serve.py`    |
| `libs/log.py`           | Shared timestamped/colored `logging` helper — always use it           |
| `data/eng/`            | Generated outputs grouped by stage: `words/`, `tokens/`, `frequency/` (sqlite + csv), `results/`, `stopwords/`, `stats/` — language code subdirs allow future expansions |
| `markdown/eng/`        | One `.md` file per results word (language code subdir)                 |
| `docs/`                 | GitHub Pages site: `index.html` (redirect → `2d.html`), `3d.html`, `2d.js`, `3d.js`, `styles.css`, `graph*.json`, `favicon.svg`, `.nojekyll` |
| `Makefile`              | Source of truth for stage orchestration                               |

## Commands

```bash
make words / tokens / frequency / frequency-reverse / frequency-letter LETTER=x
make convert / results / md / meta / graph / analysis / serve
```

- `make serve` prefers `.venv/bin/python` when present (needed for
  `nltk`/`segno`), kills :8765 first, prints LAN URLs + terminal QR.
- Python scripts also run directly, e.g. `python3 pipeline/05-md.py --limit 10`.
- Frontend check: `node --check docs/2d.js docs/3d.js`.

## Conventions

- Scripts are mostly stdlib-only; deps (`nltk`, `segno`) live in
  `.venv` via `pyproject.toml`.
- Every stage must be **resumable**: skip existing files/DB rows;
  use `INSERT OR REPLACE`/primary keys for caches.
- WordsAPI requests need the browser `User-Agent` header and
  `urllib.parse.quote(word, safe="")` encoding. Reuse `fetch_word` /
  `fetch_frequency` from `pipeline/01-words.py` via `importlib`
  (filenames contain hyphens — not importable normally).
- Pipeline scripts insert `pipeline/` and `libs/` into `sys.path`
  before importing `log`.
- Markdown generation links only words present in
  `data/eng/results/results.txt`;
  punctuation inside definitions must be preserved by the tokenizer.
- `docs/` frontend: no build step, no frameworks — plain HTML/CSS/JS,
  CDN libs only (d3, 3d-force-graph). Arrow functions only. `index.html`
  stays a redirect page.
- Don't commit `data/` artifacts or `markdown/` output unless asked.

## Gotchas

- WordsAPI returns metadata-only payloads (no `results`) for many
  frequent words — always check `payload.get("results")`.
- `data/eng/frequency/frequency_5000.csv` etc. include NLTK stopwords;
  `data/eng/stopwords/` holds the NLTK-derived list (`scripts/stopwords.py`).
- The graph JSON is a top-N subgraph; the viewers fit it to the
  viewport behind a loading screen and cycle colors on an interval.
