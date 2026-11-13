"""Generate markdown files for words in data/eng/results/results.txt.

Fetches each word from the WordsAPI and renders markdown/eng/*.md with
[word](word.md) links validated against the results list — only the
words collected by 04-results.py are queried, wikified, and linked.
Resumable — existing .md files are skipped.

Run directly:

    python3 pipeline/05-md.py [--limit N] [--workers N]
"""

import argparse
import importlib.util
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "libs"))

from log import get_logger

log = get_logger(__name__)

ROOT = Path(__file__).parent.parent
OUT_DIR = ROOT / "markdown" / "eng"
RESULTS_FILE = ROOT / "data" / "eng" / "results" / "results.txt"

# Word characters allowed inside a token (punctuation like () , . is stripped).
TOKEN_RE = re.compile(r"^([^A-Za-z0-9'._-]*)([A-Za-z0-9'._-]+)([^A-Za-z0-9'._-]*)$")

# Relation fields rendered as links, in display order.
LINK_FIELDS = [
    "synonyms",
    "antonyms",
    "typeOf",
    "hasTypes",
    "partOf",
    "hasParts",
    "instanceOf",
    "hasInstances",
    "similarTo",
    "also",
    "entails",
    "memberOf",
    "hasMembers",
    "substanceOf",
    "hasSubstances",
    "inCategory",
    "hasCategories",
    "usageOf",
    "hasUsages",
    "inRegion",
    "regionOf",
    "pertainsTo",
    "derivation",
]

_VOCAB: set[str] | None = None


def _load_words_api():
    """Load 01-words.py (hyphenated name -> importlib)."""
    spec = importlib.util.spec_from_file_location(
        "words_api", Path(__file__).parent / "01-words.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


fetch_word = _load_words_api().fetch_word


def slug(word: str) -> str:
    """Filesystem-safe filename stem for a word."""
    return re.sub(r"[/\\:*?\"<>|]", "-", word)


def vocab() -> set[str]:
    """Known words used to validate link targets (the results list)."""
    global _VOCAB
    if _VOCAB is None:
        _VOCAB = set(read_results_words())
    return _VOCAB


def to_link(word: str) -> str:
    return f"[{word}]({slug(word)}.md)"


def wikify(text: str) -> str:
    """Link each token found in the vocabulary, preserving punctuation."""
    known = vocab()
    parts = []
    for token in text.split():
        if token in known:
            parts.append(to_link(token))
            continue
        if match := TOKEN_RE.match(token):
            pre, core, post = match.groups()
            if core in known:
                parts.append(f"{pre}{to_link(core)}{post}")
                continue
        parts.append(token)
    return " ".join(parts)


def link_list(values: list[str], known: set[str]) -> str:
    return ", ".join(to_link(v) if v in known else v for v in values)


def render(payload: dict) -> str:
    """Render a /words/{word} API response as markdown."""
    known = vocab()
    word = payload["word"]
    lines = [f"# {word}", ""]

    for result in payload.get("results", []):
        definition = result.get("definition")
        if definition:
            lines.append(f"## {wikify(definition)}")
            lines.append("")

        if pos := result.get("partOfSpeech"):
            lines.append(f"- **partOfSpeech**: {to_link(pos) if pos in known else pos}")
        for field in LINK_FIELDS:
            values = [v for v in result.get(field, []) if len(v.split()) == 1]
            if values:
                lines.append(f"- **{field}**: {link_list(values, known)}")
        if examples := result.get("examples"):
            lines.append("- **examples**:")
            lines.extend(f"  - {wikify(e)}" for e in examples)
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def process_word(word: str) -> str:
    """Fetch and write the markdown file for one word.

    Returns "written", "exists", "no_data", or "error".
    """
    path = OUT_DIR / f"{slug(word)}.md"
    if path.exists():
        return "exists"
    try:
        payload = fetch_word(word)
    except Exception as exc:
        log.warning("failed to fetch %r: %s", word, exc)
        return "error"
    if not payload.get("results"):
        return "no_data"
    path.write_text(render(payload), encoding="utf-8")
    return "written"


def read_results_words() -> list[str]:
    return [
        w.strip()
        for w in RESULTS_FILE.read_text(encoding="utf-8").splitlines()
        if w.strip()
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=None, help="max words to process")
    parser.add_argument("--workers", type=int, default=8, help="parallel requests")
    args = parser.parse_args()

    words = read_results_words()
    if args.limit:
        words = words[: args.limit]

    OUT_DIR.mkdir(exist_ok=True)
    log.info(
        "processing %d words from %s with %d workers -> %s",
        len(words),
        RESULTS_FILE.name,
        args.workers,
        OUT_DIR,
    )

    counts = {"written": 0, "exists": 0, "no_data": 0, "error": 0}
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for i, status in enumerate(pool.map(process_word, words), 1):
            counts[status] += 1
            if i % 100 == 0 or i == len(words):
                nxt = words[i] if i < len(words) else "-"
                log.info(
                    "progress: %d/%d (%s), next: %r",
                    i,
                    len(words),
                    ", ".join(f"{k}={v}" for k, v in counts.items()),
                    nxt,
                )

    log.info(
        "done: %d written, %d already existed, %d no data, %d errors",
        counts["written"],
        counts["exists"],
        counts["no_data"],
        counts["error"],
    )


if __name__ == "__main__":
    main()
