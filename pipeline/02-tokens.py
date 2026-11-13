"""Filter the word list down to single-word tokens.

Reads data/eng/words/words.json and writes data/eng/tokens/tokens.json /
data/eng/tokens/tokens.txt
containing only entries without whitespace (e.g. keeps "state-of-the-art",
drops "'tween decks").

Run directly:

    python3 scripts/02-tokens.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "libs"))

from log import get_logger

log = get_logger(__name__)

ROOT = Path(__file__).parent.parent
WORDS_FILE = ROOT / "data" / "eng" / "words" / "words.json"
TOKENS_JSON = ROOT / "data" / "eng" / "tokens" / "tokens.json"
TOKENS_TXT = ROOT / "data" / "eng" / "tokens" / "tokens.txt"


def is_single_word(word: str) -> bool:
    return len(word.split()) == 1


def main() -> None:
    words = json.loads(WORDS_FILE.read_text(encoding="utf-8"))
    tokens = [w for w in words if is_single_word(w)]

    TOKENS_JSON.parent.mkdir(parents=True, exist_ok=True)
    TOKENS_JSON.write_text(json.dumps(tokens, ensure_ascii=False, indent=2) + "\n")
    TOKENS_TXT.write_text("\n".join(tokens) + "\n")

    log.info(
        "wrote %d tokens (%d of %d words are single-word) to %s and %s",
        len(tokens),
        len(tokens),
        len(words),
        TOKENS_JSON,
        TOKENS_TXT,
    )


if __name__ == "__main__":
    main()
