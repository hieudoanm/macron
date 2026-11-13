"""Extract NLTK stopwords present in the token vocabulary.

Intersects NLTK's English stopword list with data/eng/tokens/tokens.txt
and writes data/eng/stopwords/stopwords.txt (one per line) and
data/eng/stopwords/stopwords.json.

Run directly:

    uv run python scripts/stopwords.py
    # or: .venv/bin/python scripts/stopwords.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "libs"))

from log import get_logger

log = get_logger(__name__)

ROOT = Path(__file__).parent.parent
TOKENS_FILE = ROOT / "data" / "eng" / "tokens" / "tokens.txt"
OUT_TXT = ROOT / "data" / "eng" / "stopwords" / "stopwords.txt"
OUT_JSON = ROOT / "data" / "eng" / "stopwords" / "stopwords.json"


def nltk_stopwords() -> set[str]:
    """Return NLTK's English stopword list, downloading the corpus if needed."""
    from nltk.corpus import stopwords

    try:
        return set(stopwords.words("english"))
    except LookupError:
        import nltk

        log.info("downloading NLTK 'stopwords' corpus...")
        nltk.download("stopwords", quiet=True)
        return set(stopwords.words("english"))


def main() -> None:
    tokens = set(TOKENS_FILE.read_text(encoding="utf-8").split())
    stopwords = sorted(tokens & nltk_stopwords())

    OUT_TXT.parent.mkdir(parents=True, exist_ok=True)
    OUT_TXT.write_text("\n".join(stopwords) + "\n")
    OUT_JSON.write_text(json.dumps(stopwords, ensure_ascii=False, indent=2) + "\n")

    log.info(
        "%d stopwords found in %d tokens -> %s and %s",
        len(stopwords),
        len(tokens),
        OUT_TXT,
        OUT_JSON,
    )


if __name__ == "__main__":
    main()
