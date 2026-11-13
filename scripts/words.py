"""Fetch the full word list from the WordsAPI mashape endpoint.

Run directly to dump all words to data/words.json and data/words.txt,
plus single-word-only tokens to data/tokens.json and data/tokens.txt:

    python3 scripts/words.py
"""

import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "libs"))

from log import get_logger

log = get_logger(__name__)

BASE_URL = "https://www.wordsapi.com/mashape/words/"
AUTH_PARAMS = (
    "when=2026-11-13T18:19:44.190Z"
    "&encrypted=8cfdb18ce723929beb9207bee758bfb0aeb4290931f697b8"
)
API_URL = f"{BASE_URL}?{AUTH_PARAMS}&limit=1000000"

OUT_DIR = Path(__file__).parent.parent / "data"


def _get_json(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def fetch_words(url: str = API_URL):
    """GET the words endpoint and return the list of words."""
    return _get_json(url)["results"]["data"]


def fetch_word(word: str):
    """GET details for a single word."""
    url = f"{BASE_URL}{urllib.parse.quote(word, safe='')}?{AUTH_PARAMS}"
    return _get_json(url)


def main() -> None:
    log.info("fetching word list from %s", API_URL.split("?")[0])
    words = fetch_words()
    tokens = [w for w in words if len(w.split()) == 1]
    log.info("fetched %d words (%d single-word tokens)", len(words), len(tokens))

    outputs = [
        ("words", words),
        ("tokens", tokens),
    ]
    for name, items in outputs:
        json_path = OUT_DIR / f"{name}.json"
        txt_path = OUT_DIR / f"{name}.txt"
        json_path.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n")
        txt_path.write_text("\n".join(items) + "\n")
        log.info("wrote %d entries to %s and %s", len(items), json_path, txt_path)


if __name__ == "__main__":
    main()
