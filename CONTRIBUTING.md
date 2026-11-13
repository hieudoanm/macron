# Contributing to Macron

Thanks for helping build the word-graph pipeline. This guide covers
the dev workflow, conventions, and how to add new pipeline stages.

## Setup

```bash
uv venv && uv pip install -e .   # or: uv sync
# .venv is auto-detected by the Makefile (PYTHON := .venv/bin/python)
```

Pipeline scripts are stdlib-only and also run with plain `python3`.
Only `scripts/stopwords.py` (`nltk`) and `scripts/serve.py` (`segno`)
need the venv.

## Pipeline stages

Stages live in `pipeline/` with a numeric prefix that defines order:

| file                  | stage                                              |
| --------------------- | -------------------------------------------------- |
| `01-words.py`         | fetch word list from WordsAPI → `data/eng/words/`  |
| `02-tokens.py`        | filter to single-word tokens → `data/eng/tokens/`  |
| `03-frequency.py`     | per-word frequency → `data/eng/frequency/`         |
| `04-results.py`       | top-N words with API `results` → `data/eng/results/` |
| `05-md.py`            | render `markdown/eng/*.md` from results words      |
| `06-meta.py`          | markdown folder stats → `data/eng/stats/metadata.json` |
| `07-graph.py`         | link graph → `docs/graph*.json`                    |

Utility scripts live in `scripts/` (`convert.py`, `stopwords.py`,
`analysis.py`, `serve.py`) and are not part of the numbered chain.

## Adding a stage

1. Create `pipeline/NN-name.py` with the next free number.
2. Hyphenated filenames aren't importable — load them via
   `importlib.util.spec_from_file_location` (see `04-results.py`).
3. Add a `.PHONY` target + recipe to the `Makefile`, wiring
   prerequisites (e.g. `md: results`).
4. Log through `libs/log.py` (`get_logger(__name__)`), not `print`.

## Conventions

- **Resumable by default** — skip words/files/rows already produced so
  interrupted runs continue where they left off.
- **WordsAPI**: reuse `fetch_word`/`fetch_frequency` from `01-words.py`;
  always send the browser `User-Agent` header (requests 403 without it)
  and `urllib.parse.quote(word, safe="")` for URL encoding.
- **Markdown links** are inline `[word](word.md)` and must be validated
  against `data/eng/results/results.txt` — never emit links to words that won't
  have a file.
- **Frontend** (`docs/`): plain HTML/CSS/JS, no build step. Shared
  styles in `styles.css`; page logic in `2d.js`/`3d.js`; `index.html`
  is only a redirect. Arrow functions only.
- Keep scripts stdlib-only unless a dependency is truly needed (add it
  to `pyproject.toml` and install into `.venv`).

## Testing

There is no test suite yet. Verify changes by running the relevant
stage with a small limit, e.g.:

```bash
python3 pipeline/05-md.py --limit 10 --workers 4
node --check docs/2d.js docs/3d.js
make -n md meta graph   # dry-run the Makefile chain
```

## Pull requests

- Keep commits focused; one stage/feature per PR.
- Update `README.md` (pipeline list + usage) when adding targets.
- `data/` outputs and `markdown/` are generated artifacts — don't
  commit large regenerations unless intentional.
