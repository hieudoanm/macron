"""Collect the top words with API results from data/eng/frequency/frequency_5000.csv.

Queries the WordsAPI for each word in zipf rank order and keeps the
first --target words whose response contains dictionary `results`
(default 1000). Writes data/eng/results/results.txt (one per line) and
data/eng/results/results.json (rank order).

Run directly:

    python3 pipeline/04-results.py [--target N] [--workers N] [--limit N]
"""

import argparse
import csv
import importlib.util
import json
import sys
import threading
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "libs"))

from log import get_logger

log = get_logger(__name__)

ROOT = Path(__file__).parent.parent
CSV_FILE = ROOT / "data" / "eng" / "frequency" / "frequency_5000.csv"
OUT_TXT = ROOT / "data" / "eng" / "results" / "results.txt"
OUT_JSON = ROOT / "data" / "eng" / "results" / "results.json"


def _load_words_api():
    """Load 01-words.py (hyphenated name -> importlib)."""
    spec = importlib.util.spec_from_file_location(
        "words_api", Path(__file__).parent / "01-words.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


fetch_word = _load_words_api().fetch_word


def read_csv_words(path: Path) -> list[str]:
    with path.open(newline="", encoding="utf-8") as f:
        return [row["word"] for row in csv.DictReader(f)]


def check_word(word: str) -> str:
    """Return "results" if the API has dictionary data, else "no_data"/"error"."""
    try:
        payload = fetch_word(word)
    except Exception as exc:
        log.warning("failed to fetch %r: %s", word, exc)
        return "error"
    return "results" if payload.get("results") else "no_data"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=int, default=1000, help="words with results to collect")
    parser.add_argument("--workers", type=int, default=8, help="parallel requests")
    parser.add_argument("--limit", type=int, default=None, help="max words to scan")
    args = parser.parse_args()

    words = read_csv_words(CSV_FILE)
    if args.limit:
        words = words[: args.limit]

    log.info(
        "scanning up to %d words for %d with results from %s "
        "with %d workers",
        len(words),
        args.target,
        CSV_FILE.name,
        args.workers,
    )

    state = {"with_results": 0}
    lock = threading.Lock()
    collected: list[tuple[int, str]] = []
    idx_of: dict = {}
    counts = {"results": 0, "no_data": 0, "over_target": 0, "error": 0}
    done = submitted = 0

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        inflight = set()

        def submit():
            nonlocal submitted
            if submitted < len(words) and state["with_results"] < args.target:
                idx = submitted
                fut = pool.submit(check_word, words[idx])
                idx_of[fut] = (idx, words[idx])
                inflight.add(fut)
                submitted += 1

        for _ in range(args.workers):
            submit()

        while inflight:
            finished, inflight = wait(inflight, return_when=FIRST_COMPLETED)
            for fut in finished:
                idx, word = idx_of.pop(fut)
                status = fut.result()
                if status == "results":
                    counts["results"] += 1
                else:
                    counts[status] += 1
                done += 1
                if status == "results":
                    with lock:
                        if state["with_results"] < args.target:
                            state["with_results"] += 1
                            collected.append((idx, word))
                        else:
                            counts["over_target"] += 1
                if state["with_results"] < args.target:
                    submit()
                if done % 100 == 0:
                    nxt = words[submitted] if submitted < len(words) else "-"
                    log.info(
                        "progress: %d scanned, %d with results, next: %r (%s)",
                        done,
                        state["with_results"],
                        nxt,
                        ", ".join(f"{k}={v}" for k, v in counts.items()),
                    )

    collected.sort()
    results = [w for _, w in collected]

    OUT_TXT.parent.mkdir(parents=True, exist_ok=True)
    OUT_TXT.write_text("\n".join(results) + "\n")
    OUT_JSON.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n")

    log.info(
        "done: %d with results (%d no data, %d over target, %d errors) -> %s and %s",
        len(results),
        counts["no_data"],
        counts["over_target"],
        counts["error"],
        OUT_TXT,
        OUT_JSON,
    )


if __name__ == "__main__":
    main()
