"""Two tools. read_feedback reads the CSV. web_search reads the offline cache unless live mode is on."""
import csv, json, os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "fixtures" / "search_cache.json"

def read_feedback(path: str) -> dict:
    p = ROOT / path
    rows = list(csv.DictReader(open(p, newline="")))
    by_channel = {}
    for r in rows:
        by_channel[r["channel"]] = by_channel.get(r["channel"], 0) + 1
    return {"rows": len(rows), "by_channel": by_channel, "items": rows}

def _cache() -> dict:
    return json.load(open(CACHE))

def web_search(query: str, offline: bool = True) -> list[dict]:
    """Offline: return cached sources for the query. Live: not wired in this demo; falls back to cache."""
    c = _cache()
    ids = c["queries"].get(query, [])
    return [{"id": i, **c["sources"][i]} for i in ids]

def fetch_source(source_id: str) -> dict | None:
    """The gate re-fetches the cited source from the SAME cache the agent used."""
    return _cache()["sources"].get(source_id)

def recompute_internal(spec: dict) -> tuple[int, int]:
    rows = list(csv.DictReader(open(ROOT / "data" / "freshcart_feedback.csv", newline="")))
    n = sum(1 for r in rows if r[spec["column"]] == spec["value"])
    return n, len(rows)
