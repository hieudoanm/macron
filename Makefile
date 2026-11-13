.PHONY: words tokens frequency frequency-reverse convert results md meta graph analysis serve

PYTHON := $(shell [ -x .venv/bin/python ] && echo .venv/bin/python || echo python3)

# 01: Fetch the word list from WordsAPI -> data/eng/words/
words:
	python3 pipeline/01-words.py

# 02: Filter words to single-word tokens -> data/eng/tokens/
tokens: words
	python3 pipeline/02-tokens.py

# 03: Fetch frequency data for all tokens -> data/eng/frequency/frequency.sqlite + frequency.csv
frequency: tokens
	python3 pipeline/03-frequency.py

# Same as frequency but queries tokens in reverse (z -> a) order
frequency-reverse: tokens
	python3 pipeline/03-frequency.py --reverse

# Convert frequency.sqlite -> data/eng/frequency/frequency*.csv
convert:
	python3 scripts/convert.py

# 04: Collect top words with results -> data/eng/results/results.txt + results.json
results: convert
	python3 pipeline/04-results.py

# 05: Generate md files for results words -> markdown/*.md
md: results
	python3 pipeline/05-md.py

# 06: Report markdown/ folder stats -> data/eng/stats/metadata.json
meta:
	python3 pipeline/06-meta.py

# 07: Build the link graph from markdown/*.md -> docs/graph.json + graph.min.json
graph:
	python3 pipeline/07-graph.py

# Serve docs/ locally to view the graph (prints localhost / LAN / external URLs)
serve: graph
	-lsof -ti :8765 | xargs kill 2>/dev/null
	$(PYTHON) scripts/serve.py

# Analyze tokens.txt: word counts by first character -> data/eng/stats/analysis.json
analysis: tokens
	python3 scripts/analysis.py

push:
	git add -A
	git commit --amend --no-edit
	git push -f
