# Macron = Markdown + Neuron

Generate a markdown knowledge base of English words from the WordsAPI,
link them together, and visualize the result as an interactive graph.

## Pipeline

```txt
WordsAPI ──► data/eng/words/ ──► data/eng/tokens/ ──► data/eng/frequency/ ──► data/eng/results/ ──► markdown/eng/*.md ──► docs/
 (words)       (all words)       (single words)      (zipf scores)       (with results)    (one file/word)   (graph site)
```

`data/` and `markdown/` are grouped by language (`eng`) to allow future
expansions into other languages.

1. **`pipeline/01-words.py`** fetches the full word list (~325k entries)
   and writes `data/eng/words/words.json` / `data/eng/words/words.txt`.
2. **`pipeline/02-tokens.py`** filters that list down to single-word
   tokens (~212k) → `data/eng/tokens/tokens.json` /
   `data/eng/tokens/tokens.txt`.
3. **`pipeline/03-frequency.py`** queries `/words/{word}/frequency` for
   every token → `data/eng/frequency/frequency.sqlite`, then exports
   `data/eng/frequency/frequency.csv` (sorted by zipf descending).
4. **`scripts/convert.py`** rewrites `frequency.csv` keeping only
   frequency-bearing words, plus top-N cutoffs
   (`frequency_1000.csv` … `frequency_20000.csv`).
5. **`pipeline/04-results.py`** queries each word in
   `frequency_5000.csv` and keeps the first 1000 whose API response
   contains dictionary `results` → `data/eng/results/results.txt` /
   `results.json`.
6. **`pipeline/05-md.py`** queries each results word and renders one
   markdown file per word into `markdown/eng/`. Definitions and relation
   fields (synonyms, typeOf, partOf, entails, ...) are emitted as
   `[word](word.md)` links, validated against
   `data/eng/results/results.txt` so only collected words are linked.
7. **`pipeline/06-meta.py`** reports `markdown/eng/` folder stats →
   `data/eng/stats/metadata.json`.
8. **`pipeline/07-graph.py`** scans `markdown/eng/` for links and writes
   `docs/graph.json` (readable) and `docs/graph.min.json` (compact).
9. **`docs/3d.html`** renders the graph with 3d-force-graph
   (three.js/WebGL); `docs/2d.html` has the 2D d3-force variant.
   `docs/index.html` redirects to the 2D view. Both fit the whole
   graph to the viewport after a loading screen and cycle node/link
   colors every few seconds.

## Usage

```bash
# pipeline (01 -> 07)
make words                        # 01 -> data/eng/words/
make tokens                       # 02 -> data/eng/tokens/
make frequency                    # 03 -> data/eng/frequency/frequency.sqlite + frequency.csv
make results                      # 04 -> data/eng/results/results.* (top 1000 with API results)
make md                           # 05 -> markdown/eng/*.md
make meta                         # 06 -> data/eng/stats/metadata.json
make graph                        # 07 -> docs/graph*.json

# utilities
make frequency-reverse            # 03 variant, z -> a order
make frequency-letter LETTER=s    # 03 variant, query only s-words
make convert                      # frequency.sqlite -> data/eng/frequency/frequency*.csv
make analysis                     # tokens.txt -> data/eng/stats/analysis.json (first-char histogram)
make serve                        # kill :8765, rebuild graph, serve docs/ at :8765
```

`make serve` prints localhost / LAN / external URLs plus a scannable
QR code for the LAN address (`scripts/serve.py`).

Everything is resumable — existing output files / DB rows are skipped,
so interrupted runs can be continued by re-running the same command.

## Frequency metrics

`frequency.csv` columns (from WordsAPI `/words/{word}/frequency`):

| column        | meaning                                                                                                                                                       |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `zipf`        | Zipf frequency score (~1–7): `log10` of occurrences per billion words. Higher = more common. `a` ≈ 7.28, rare words ≈ 1–2. Only ~18% of words have this data. |
| `per_million` | Expected occurrences per million words of English text (e.g. `effect` ≈ 26 per million).                                                                      |
| `diversity`   | 0–1 score: likelihood the word appears in a document drawn from a corpus. High diversity = appears across many different texts/domains.                       |

Rows with empty values are words the API has no frequency data for;
`convert.py` drops them so `frequency.csv` only lists measurable words.

## Output format

`markdown/eng/effect.md`:

```markdown
# effect

## [a](a.md) [phenomenon](phenomenon.md) [that](that.md) [follows](follows.md) ...

- **partOfSpeech**: [noun](noun.md)
- **synonyms**: [consequence](consequence.md), [event](event.md), ...
- **typeOf**: [phenomenon](phenomenon.md)
- **examples**:
  - [the](the.md) [effect](effect.md) [of](of.md) [sleep](sleep.md) [loss](loss.md)
```

## Deploy

`docs/` is set up for GitHub Pages: push `master`, then in
**Settings → Pages** choose *Deploy from a branch* → `master` → `/docs`.

## Notes

- Pipeline scripts are stdlib-only; `scripts/stopwords.py` needs `nltk`
  and `scripts/serve.py` uses `segno` for the QR code — both in
  `pyproject.toml`, installed into `.venv` (`make serve` prefers
  `.venv/bin/python` automatically).
- WordsAPI ToS allows caching API data for up to 24 hours; the full run
  is ~212k requests, so check your plan's rate limits.
- `libs/log.py` provides the shared timestamped/colored logging used by
  all scripts.
