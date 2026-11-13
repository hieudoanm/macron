"""Fetch word frequency data from WordsAPI into SQLite, export sorted CSV.

Queries /words/{word}/frequency for every token in
data/eng/tokens/tokens.json and stores results in
data/eng/frequency/frequency.sqlite (resumable — already-queried
words are skipped). Then exports data/eng/frequency/frequency.csv
sorted by zipf
score, highest to lowest.

Run directly:

    python3 scripts/frequency.py [--limit N] [--workers N] [--word WORD]
"""

import argparse
import csv
import importlib.util
import json
import sqlite3
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "libs"))

from log import get_logger

_spec = importlib.util.spec_from_file_location(
    "words_api", Path(__file__).parent / "01-words.py"
)
_words_api = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_words_api)
fetch_frequency = _words_api.fetch_frequency

log = get_logger(__name__)

ROOT = Path(__file__).parent.parent
TOKENS_FILE = ROOT / "data" / "eng" / "tokens" / "tokens.json"
DB_FILE = ROOT / "data" / "eng" / "frequency" / "frequency.sqlite"
CSV_FILE = ROOT / "data" / "eng" / "frequency" / "frequency.csv"

SCHEMA = """
CREATE TABLE IF NOT EXISTS frequency (
    word TEXT PRIMARY KEY,
    zipf REAL,
    per_million REAL,
    diversity REAL
)
"""


def fetch_one(word: str) -> tuple:
    """Return (word, zipf, per_million, diversity); NULLs when unavailable."""
    try:
        payload = fetch_frequency(word)
    except Exception as exc:
        log.warning("failed to fetch frequency for %r: %s", word, exc)
        return (word, None, None, None)
    freq = payload.get("frequency") or {}
    return (
        word,
        freq.get("zipf"),
        freq.get("perMillion"),
        freq.get("diversity"),
    )


def export_csv(conn: sqlite3.Connection) -> None:
    """Write frequency.csv sorted by zipf descending (NULLs last)."""
    with CSV_FILE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["word", "zipf", "per_million", "diversity"])
        writer.writerows(
            conn.execute(
                "SELECT word, zipf, per_million, diversity "
                "FROM frequency ORDER BY zipf DESC"
            )
        )
    log.info("wrote %s", CSV_FILE)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=None, help="max words to query")
    parser.add_argument("--workers", type=int, default=8, help="parallel requests")
    parser.add_argument("--word", help="query a single word instead of the list")
    parser.add_argument(
        "--reverse", action="store_true", help="query tokens in reverse order"
    )
    parser.add_argument(
        "--letter",
        help="only query tokens starting with this character (e.g. --letter s)",
    )
    args = parser.parse_args()

    if args.word:
        words = [args.word]
    else:
        words = json.loads(TOKENS_FILE.read_text(encoding="utf-8"))
    if args.letter:
        letter = args.letter[0].lower()
        words = [w for w in words if w[:1].lower() == letter]
    if args.reverse:
        words = words[::-1]
    if args.limit:
        words = words[: args.limit]

    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    conn.execute(SCHEMA)

    done = {row[0] for row in conn.execute("SELECT word FROM frequency")}
    pending = [w for w in words if w not in done]
    log.info(
        "%d tokens total, %d already in %s, %d to query",
        len(words),
        len(done),
        DB_FILE.name,
        len(pending),
    )

    fetched = 0
    batch: list[tuple] = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for row in pool.map(fetch_one, pending):
            batch.append(row)
            fetched += 1
            if len(batch) >= 1000:
                conn.executemany(
                    "INSERT OR REPLACE INTO frequency VALUES (?, ?, ?, ?)", batch
                )
                conn.commit()
                batch.clear()
            if fetched % 1000 == 0:
                nxt = pending[fetched] if fetched < len(pending) else "-"
                log.info("progress: %d/%d fetched, next: %r", fetched, len(pending), nxt)
    if batch:
        conn.executemany("INSERT OR REPLACE INTO frequency VALUES (?, ?, ?, ?)", batch)
        conn.commit()

    total = conn.execute("SELECT COUNT(*) FROM frequency").fetchone()[0]
    with_freq = conn.execute(
        "SELECT COUNT(*) FROM frequency WHERE zipf IS NOT NULL"
    ).fetchone()[0]
    log.info("db now holds %d rows (%d with frequency data)", total, with_freq)

    export_csv(conn)
    conn.close()


if __name__ == "__main__":
    main()
