"""Analyze data/eng/tokens/tokens.txt: count words by first character.

Writes the histogram to data/eng/stats/analysis.json and logs a summary.

Run directly:

    python3 scripts/analysis.py
"""

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "libs"))

from log import get_logger

log = get_logger(__name__)

ROOT = Path(__file__).parent.parent
TOKENS_FILE = ROOT / "data" / "eng" / "tokens" / "tokens.txt"
OUT_FILE = ROOT / "data" / "eng" / "stats" / "analysis.json"


def first_char(word: str) -> str:
    ch = word[0]
    return ch.lower() if ch.isalpha() else ch


def main() -> None:
    words = TOKENS_FILE.read_text(encoding="utf-8").splitlines()
    counts = Counter(first_char(w) for w in words if w)

    # sort: letters a-z first, then digits/symbols by count desc
    ordered = sorted(
        counts.items(),
        key=lambda kv: (kv[0] not in "abcdefghijklmnopqrstuvwxyz", -kv[1], kv[0]),
    )

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(
        json.dumps(dict(ordered), ensure_ascii=False, indent=2) + "\n"
    )

    log.info("%d tokens across %d distinct first characters", len(words), len(counts))
    for ch, n in ordered:
        log.info("  %r: %d", ch, n)
    log.info("wrote %s", OUT_FILE)


if __name__ == "__main__":
    main()
