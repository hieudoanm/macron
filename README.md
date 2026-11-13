# Macron = Markdown + Neuron

Generate a markdown knowledge base of English words from the WordsAPI,
link them together, and visualize the result as an interactive graph.

## Pipeline

```txt
WordsAPI ──► data/tokens.* ──► markdown/*.md ──► docs/graph*.json ──► docs/index.html
(words)      (word lists)      (one file/word)   (link graph)         (d3-force view)
```

1. **`scripts/words.py`** fetches the full word list (~325k entries) and
   writes `data/words.json` / `data/words.txt`, plus the single-word
   subset `data/tokens.json` / `data/tokens.txt` (~212k tokens).
2. **`scripts/tokens.py`** queries the API for each token and renders one
   markdown file per word into `markdown/`. Definitions and relation
   fields (synonyms, typeOf, partOf, entails, ...) are emitted as
   `[word](word.md)` links, validated against `data/tokens.json` so only
   real words are linked.
3. **`scripts/graph.py`** scans `markdown/` for links and writes
   `docs/graph.json` (readable) and `docs/graph.min.json` (compact).
4. **`docs/index.html`** renders the graph with d3-force. It shows a
   top-N subgraph (default 5000 nodes, min degree 2) since the full
   ~212k-node graph is too large for client-side force simulation.

## Usage

```bash
make words              # fetch word lists -> data/
make markdown           # generate markdown for all tokens (a -> z)
make markdown-reverse   # same, but z -> a
make graph              # build docs/graph.json + graph.min.json
make serve              # kill :8765, rebuild graph, serve docs/ at :8765
```

Useful options for `scripts/tokens.py`:

```bash
python3 scripts/tokens.py --limit 100          # test batch
python3 scripts/tokens.py --word serendipity   # single word
python3 scripts/tokens.py --reverse --workers 16
```

Everything is resumable — existing output files are skipped, so
interrupted runs can be continued by re-running the same command.

## Output format

`markdown/effect.md`:

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

- Stdlib only — no dependencies to install.
- WordsAPI ToS allows caching API data for up to 24 hours; the full run
  is ~212k requests, so check your plan's rate limits.
- `libs/log.py` provides the shared timestamped/colored logging used by
  all scripts.
