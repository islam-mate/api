#!/usr/bin/env python3
"""
Islamic Stories — Catalog Validator
=====================================
Checks index.json for schema consistency and cross-references.
Run after build_catalog.py or with: python build_catalog.py --validate

Checks:
    1. index.json is parseable JSON
    2. Required top-level keys present
    3. All channel_ids in videos exist in channels[]
    4. All category_ids in videos exist in categories[]
    5. No duplicate video IDs
    6. video.id == "{category_id}:youtube:{video_id}"
    7. sort_order is a positive integer
    8. duration_seconds is a non-negative integer
    9. depth is one of: summary, detailed, series
    10. language is one of: ar, en
    11. title.ar is present and non-empty
    12. prophet_id (if present) is a non-empty string
    13. counts.videos matches actual videos[] length
    14. counts.channels matches actual channels[] length

Usage:
    python validate_catalog.py
    python validate_catalog.py --catalog /path/to/index.json
    python validate_catalog.py --strict   # exit 1 on warnings too
"""

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
ROOT = SCRIPT_DIR.parent
DEFAULT_CATALOG = ROOT / "index.json"

VALID_DEPTHS = {"summary", "detailed", "series"}
VALID_LANGUAGES = {"ar", "en"}
VALID_PROVIDERS = {"youtube"}


# ---------------------------------------------------------------------------
# Collector
# ---------------------------------------------------------------------------

class Results:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(f"  ERROR   {msg}")

    def warn(self, msg: str) -> None:
        self.warnings.append(f"  WARN    {msg}")

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0

    def print_report(self) -> None:
        total = len(self.errors) + len(self.warnings)
        if total == 0:
            print("  All checks passed.")
            return
        for msg in self.errors:
            print(msg)
        for msg in self.warnings:
            print(msg)

    def summary(self) -> str:
        return f"{len(self.errors)} error(s), {len(self.warnings)} warning(s)"


# ---------------------------------------------------------------------------
# Validate
# ---------------------------------------------------------------------------

def validate(catalog_path: Path) -> Results:
    r = Results()

    # 1. Parse JSON
    if not catalog_path.exists():
        r.error(f"Catalog not found: {catalog_path}  (run build_catalog.py first)")
        return r

    try:
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        r.error(f"Invalid JSON: {e}")
        return r

    if not isinstance(catalog, dict):
        r.error("index.json must be a JSON object")
        return r

    # 2. Required top-level keys
    for key in ("schema_version", "generated_at", "counts", "categories", "channels", "videos"):
        if key not in catalog:
            r.error(f"Missing required key: '{key}'")

    if r.errors:
        return r  # can't continue without structure

    categories: list[dict] = catalog.get("categories", [])
    channels: list[dict] = catalog.get("channels", [])
    videos: list[dict] = catalog.get("videos", [])
    counts: dict = catalog.get("counts", {})

    # Index valid IDs for cross-reference
    valid_category_ids = {cat.get("id") for cat in categories}
    valid_channel_ids = {ch.get("id") for ch in channels}

    # 14. counts.channels
    if counts.get("channels") != len(channels):
        r.error(
            f"counts.channels={counts.get('channels')} but channels[] has {len(channels)} entries"
        )

    # 13. counts.videos
    if counts.get("videos") != len(videos):
        r.error(
            f"counts.videos={counts.get('videos')} but videos[] has {len(videos)} entries"
        )

    # 5. Duplicate IDs
    seen_ids: dict[str, int] = {}
    for i, v in enumerate(videos):
        vid_id = v.get("id", "")
        if vid_id in seen_ids:
            r.error(
                f"video[{i}]: duplicate id '{vid_id}' (first at index {seen_ids[vid_id]})"
            )
        else:
            seen_ids[vid_id] = i

    # Per-video checks
    for i, v in enumerate(videos):
        prefix = f"video[{i}] id='{v.get('id', '?')}'"

        # 3. channel_id cross-reference
        ch_id = v.get("channel_id")
        if ch_id not in valid_channel_ids:
            r.error(f"{prefix}: unknown channel_id '{ch_id}'")

        # 4. category_id cross-reference
        cat_id = v.get("category_id")
        if cat_id not in valid_category_ids:
            r.error(f"{prefix}: unknown category_id '{cat_id}'")

        # Provider
        provider = v.get("provider")
        if provider not in VALID_PROVIDERS:
            r.error(f"{prefix}: unknown provider '{provider}'")

        video_id = v.get("video_id", "")

        # 6. id == "{category_id}:{provider}:{video_id}"
        expected_id = f"{cat_id}:{provider}:{video_id}" if cat_id and provider and video_id else None
        if expected_id and v.get("id") != expected_id:
            r.error(f"{prefix}: id should be '{expected_id}' but is '{v.get('id')}'")

        # video_id format (YouTube 11 chars)
        if provider == "youtube" and (not video_id or len(video_id) != 11):
            r.error(f"{prefix}: youtube video_id must be 11 characters, got '{video_id}'")

        # 9. depth
        depth = v.get("depth")
        if depth not in VALID_DEPTHS:
            r.error(f"{prefix}: depth must be one of {sorted(VALID_DEPTHS)}, got '{depth}'")

        # 10. language
        lang = v.get("language")
        if lang not in VALID_LANGUAGES:
            r.error(f"{prefix}: language must be one of {sorted(VALID_LANGUAGES)}, got '{lang}'")

        # 11. title.ar
        title = v.get("title", {})
        if not isinstance(title, dict):
            r.error(f"{prefix}: title must be an object")
        elif not title.get("ar", "").strip():
            r.error(f"{prefix}: title.ar is missing or empty")

        # title.en warning (not required but useful)
        if isinstance(title, dict) and not title.get("en", "").strip():
            r.warn(f"{prefix}: title.en is missing (not required, but useful for EN users)")

        # 7. sort_order
        sort_order = v.get("sort_order")
        if not isinstance(sort_order, int) or sort_order < 1:
            r.error(f"{prefix}: sort_order must be a positive integer, got '{sort_order}'")

        # 8. duration_seconds
        dur = v.get("duration_seconds")
        if not isinstance(dur, int) or dur < 0:
            r.error(f"{prefix}: duration_seconds must be a non-negative integer, got '{dur}'")
        elif dur == 0:
            r.warn(f"{prefix}: duration_seconds=0 (unknown duration)")

        # 12. prophet_id if present
        prophet_id = v.get("prophet_id")
        if prophet_id is not None and not isinstance(prophet_id, str):
            r.error(f"{prefix}: prophet_id must be a string, got {type(prophet_id).__name__}")
        elif isinstance(prophet_id, str) and not prophet_id.strip():
            r.error(f"{prefix}: prophet_id is present but empty — remove the key or fill it")

    return r


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate the Islamic Stories index.json catalog",
    )
    parser.add_argument(
        "--catalog",
        type=Path,
        default=DEFAULT_CATALOG,
        metavar="PATH",
        help=f"Path to index.json (default: {DEFAULT_CATALOG})",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with code 1 if there are any warnings",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    print(f"\nIslamic Stories — Catalog Validator")
    print(f"Catalog: {args.catalog}\n")

    results = validate(args.catalog)
    results.print_report()

    print(f"\nResult: {results.summary()}")

    if not results.ok:
        print("Status: FAIL\n")
        sys.exit(1)

    if args.strict and results.warnings:
        print("Status: FAIL (--strict, warnings treated as errors)\n")
        sys.exit(1)

    print("Status: OK\n")
    sys.exit(0)


if __name__ == "__main__":
    main()