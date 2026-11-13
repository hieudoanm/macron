"""Build a link graph from the generated markdown files.

Scans markdown/eng/*.md for [word](word.md) links and writes:

    docs/graph.json      {"nodes": [{"id", "file"}], "links": [{"source", "target", "weight"}]}
    docs/graph.min.json  minified: {"nodes": [[id, file], ...], "links": [[src, dst, weight], ...]}

Run directly:

    python3 scripts/graph.py
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "libs"))

from log import get_logger

log = get_logger(__name__)

ROOT = Path(__file__).parent.parent
MD_DIR = ROOT / "markdown" / "eng"
OUT_DIR = ROOT / "docs"
OUT_FILE = OUT_DIR / "graph.json"
MIN_FILE = OUT_DIR / "graph.min.json"

LINK_RE = re.compile(r"\]\(([^)\s]+\.md)\)")


def stem(filename: str) -> str:
    return filename[: -len(".md")]


def build_graph() -> dict:
    files = sorted(p for p in MD_DIR.iterdir() if p.suffix == ".md")
    node_ids = {stem(p.name) for p in files}

    links: Counter[tuple[str, str]] = Counter()
    for path in files:
        src = stem(path.name)
        text = path.read_text(encoding="utf-8")
        for target_file in LINK_RE.findall(text):
            dst = stem(target_file)
            if dst in node_ids and dst != src:
                links[(src, dst)] += 1

    degree: Counter[str] = Counter()
    for src, dst in links:
        degree[src] += 1
        degree[dst] += 1

    nodes = [
        {
            "id": s,
            "file": f"{s}.md",
            "isolated": degree[s] == 0,
        }
        for s in sorted(node_ids)
    ]
    edges = [
        {"source": src, "target": dst, "weight": weight}
        for (src, dst), weight in sorted(links.items())
    ]
    return {"nodes": nodes, "links": edges}


def minify(graph: dict) -> dict:
    """Compact representation: nodes/links as tuples instead of objects."""
    return {
        "nodes": [[n["id"], n["file"]] for n in graph["nodes"]],
        "links": [[l["source"], l["target"], l["weight"]] for l in graph["links"]],
    }


def main() -> None:
    graph = build_graph()
    OUT_DIR.mkdir(exist_ok=True)
    OUT_FILE.write_text(json.dumps(graph, ensure_ascii=False) + "\n")
    MIN_FILE.write_text(
        json.dumps(minify(graph), ensure_ascii=False, separators=(",", ":")) + "\n"
    )
    isolated = [n["id"] for n in graph["nodes"] if n["isolated"]]
    log.info(
        "wrote %d nodes (%d isolated: %s) and %d links",
        len(graph["nodes"]),
        len(isolated),
        ", ".join(isolated) if isolated else "-",
        len(graph["links"]),
    )
    for path in (OUT_FILE, MIN_FILE):
        log.info("  %s: %s", path, human_size(path.stat().st_size))


def human_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024


if __name__ == "__main__":
    main()
