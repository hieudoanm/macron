"""Convert data/eng/frequency/frequency.sqlite to CSV files.

Exports only rows that have frequency numbers (zipf IS NOT NULL),
sorted by zipf descending (stopwords are kept):

    data/eng/frequency/frequency.csv        all frequency-bearing words
    data/eng/frequency/frequency_1000.csv   top 1,000 by zipf
    data/eng/frequency/frequency_5000.csv   top 5,000 by zipf
    data/eng/frequency/frequency_10000.csv  top 10,000 by zipf
    data/eng/frequency/frequency_20000.csv  top 20,000 by zipf

Run directly:

    python3 scripts/convert.py
"""

import csv
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "libs"))

from log import get_logger

log = get_logger(__name__)

ROOT = Path(__file__).parent.parent
DB_FILE = ROOT / "data" / "eng" / "frequency" / "frequency.sqlite"
TOP_N = (1_000, 5_000, 10_000, 20_000)


def export_csv(path: Path, rows: list[tuple]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["word", "zipf", "per_million", "diversity"])
        writer.writerows(rows)
    log.info("wrote %d rows to %s", len(rows), path)


def main() -> None:
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    rows = conn.execute(
        "SELECT word, zipf, per_million, diversity FROM frequency "
        "WHERE zipf IS NOT NULL ORDER BY zipf DESC"
    ).fetchall()
    conn.close()

    FREQ_DIR = ROOT / "data" / "eng" / "frequency"
    export_csv(FREQ_DIR / "frequency.csv", rows)
    for n in TOP_N:
        export_csv(FREQ_DIR / f"frequency_{n}.csv", rows[:n])


if __name__ == "__main__":
    main()
