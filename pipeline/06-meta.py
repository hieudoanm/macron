"""Report metadata for the markdown/eng/ folder.

Scans markdown/*.md and writes summary stats to data/stats/metadata.json:

    {"dir", "file_count", "total_bytes", "min_bytes", "max_bytes",
     "mean_bytes", "files": [{"name", "bytes"}, ...]}

Run directly:

    python3 scripts/metadata.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "libs"))

from log import get_logger

log = get_logger(__name__)

ROOT = Path(__file__).parent.parent
MD_DIR = ROOT / "markdown" / "eng"
OUT_FILE = ROOT / "data" / "eng" / "stats" / "metadata.json"


def collect() -> dict:
    files = sorted(p for p in MD_DIR.iterdir() if p.is_file() and p.suffix == ".md")
    sizes = [p.stat().st_size for p in files]

    return {
        "dir": str(MD_DIR),
        "file_count": len(files),
        "total_bytes": sum(sizes),
        "min_bytes": min(sizes, default=0),
        "max_bytes": max(sizes, default=0),
        "mean_bytes": round(sum(sizes) / len(sizes), 1) if sizes else 0,
        "files": [{"name": p.name, "bytes": p.stat().st_size} for p in files],
    }


def human_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024


def main() -> None:
    meta = collect()
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n")

    log.info("%s: %d files, %s total", MD_DIR, meta["file_count"], human_size(meta["total_bytes"]))
    log.info(
        "size: min %s, max %s, mean %s",
        human_size(meta["min_bytes"]),
        human_size(meta["max_bytes"]),
        human_size(int(meta["mean_bytes"])),
    )
    log.info("wrote %s", OUT_FILE)


if __name__ == "__main__":
    main()
