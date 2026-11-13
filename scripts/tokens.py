"""Generate one markdown file per word from the WordsAPI.

Run directly:

    python3 scripts/word.py [--limit N] [--workers N] [--word WORD]

Existing .md files are skipped, so the script can be re-run to resume.
"""

import argparse
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "libs"))

from log import get_logger
from words import fetch_word

log = get_logger(__name__)

ROOT = Path(__file__).parent.parent
OUT_DIR = ROOT / "markdown"
WORDS_FILE = ROOT / "data" / "tokens.json"

_VOCAB: set[str] | None = None

# Word characters allowed inside a token (punctuation like () , . is stripped).
TOKEN_RE = re.compile(r"^([^A-Za-z0-9'._-]*)([A-Za-z0-9'._-]+)([^A-Za-z0-9'._-]*)$")

# Relation fields rendered as wikilink lists, in display order.
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


def slug(word: str) -> str:
    """Filesystem-safe filename stem for a word."""
    return re.sub(r"[/\\:*?\"<>|]", "-", word)


def vocab() -> set[str]:
    """Known single words used to validate link targets."""
    global _VOCAB
    if _VOCAB is None:
        _VOCAB = set(json.loads(WORDS_FILE.read_text(encoding="utf-8")))
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


def link_list(values: list[str]) -> str:
    return ", ".join(to_link(v) for v in values)


def render(payload: dict) -> str:
    """Render a /words/{word} API response as markdown."""
    word = payload["word"]
    lines = [f"# {word}", ""]

    for result in payload.get("results", []):
        definition = result.get("definition")
        if definition:
            lines.append(f"## {wikify(definition)}")
            lines.append("")

        if pos := result.get("partOfSpeech"):
            lines.append(f"- **partOfSpeech**: {to_link(pos)}")
        for field in LINK_FIELDS:
            values = [v for v in result.get(field, []) if len(v.split()) == 1]
            if values:
                lines.append(f"- **{field}**: {link_list(values)}")
        if examples := result.get("examples"):
            lines.append("- **examples**:")
            lines.extend(f"  - {wikify(e)}" for e in examples)
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def process_word(word: str) -> str:
    """Fetch and write the markdown file for one word.

    Returns "written", "skipped" (file exists or no data), or "error".
    """
    path = OUT_DIR / f"{slug(word)}.md"
    if path.exists():
        return "skipped"
    try:
        payload = fetch_word(word)
    except Exception as exc:
        log.warning("failed to fetch %r: %s", word, exc)
        return "error"
    if not payload.get("results"):
        return "skipped"
    path.write_text(render(payload), encoding="utf-8")
    return "written"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=None, help="max words to process")
    parser.add_argument("--workers", type=int, default=8, help="parallel requests")
    parser.add_argument("--word", help="process a single word instead of the list")
    parser.add_argument("--reverse", action="store_true", help="process tokens in reverse order")
    args = parser.parse_args()

    if args.word:
        words = [args.word]
    else:
        words = json.loads(WORDS_FILE.read_text(encoding="utf-8"))
    if args.reverse:
        words = words[::-1]
    if args.limit:
        words = words[: args.limit]

    log.info("processing %d tokens with %d workers -> %s", len(words), args.workers, OUT_DIR)

    counts = {"written": 0, "skipped": 0, "error": 0}
    done = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for status in pool.map(process_word, words):
            counts[status] += 1
            done += 1
            if done % 100 == 0:
                log.info(
                    "progress: %d/%d (%s)",
                    done,
                    len(words),
                    ", ".join(f"{k}={v}" for k, v in counts.items()),
                )

    log.info(
        "done: %d written, %d skipped, %d errors",
        counts["written"],
        counts["skipped"],
        counts["error"],
    )


if __name__ == "__main__":
    main()
