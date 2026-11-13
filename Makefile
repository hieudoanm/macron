.PHONY: words markdown markdown-reverse graph serve

# Fetch the word list from WordsAPI -> data/words.* and data/tokens.*
words:
	python3 scripts/words.py

# Generate markdown files for every token -> markdown/*.md
# (depends on words so tokens.json exists; resumable, skips existing files)
markdown: words
	python3 scripts/tokens.py

# Same as markdown but processes tokens in reverse (z -> a) order
markdown-reverse: words
	python3 scripts/tokens.py --reverse

# Build the link graph from markdown/*.md -> docs/graph.json + graph.min.json
graph:
	python3 scripts/graph.py

# Serve docs/ locally to view the graph (open http://localhost:8765)
serve: graph
	-lsof -ti :8765 | xargs kill 2>/dev/null
	python3 -m http.server 8765 --directory docs
