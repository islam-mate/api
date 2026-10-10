#!/usr/bin/env python3
"""
Islamic Stories — Catalog Builder
===================================
Reads source/ (manually maintained) and generates all output files.

Input  (source of truth):
    source/channels.json
    source/categories.json
    source/videos/{category_id}.json   (one file per category)

Output (generated — do not edit manually):
    index.json                          <- complete catalog
    channels/{channel_id}.json          <- filtered by channel
    categories/{category_id}.json       <- filtered by category

Usage:
    python build_catalog.py
    python build_catalog.py --validate  # run validate_catalog.py after build
    python build_catalog.py --dry-run   # print stats only, no writes

Notes:
    - A video can appear in multiple categories (cross-listed).
      In the generated catalog, its id is scoped to the category:
      "{category_id}:youtube:{video_id}" — globally unique.
    - Source files store id as "youtube:{video_id}"; the build overrides it.
"""

import argparse
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).parent
ROOT = SCRIPT_DIR.parent  # data/islamic_stories/

SOURCE_DIR = ROOT / "source"
CHANNELS_JSON = SOURCE_DIR / "channels.json"
CATEGORIES_JSON = SOURCE_DIR / "categories.json"
VIDEOS_DIR = SOURCE_DIR / "videos"

OUTPUT_INDEX = ROOT / "index.json"
OUTPUT_CHANNELS_DIR = ROOT / "channels"
OUTPUT_CATEGORIES_DIR = ROOT / "categories"

SCHEMA_VERSION = "1.0.0"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_json(path: Path) -> list | dict:
    if not path.exists():
        print(f"ERROR: Missing required file: {path}", file=sys.stderr)
        sys.exit(1)
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in {path}: {e}", file=sys.stderr)
        sys.exit(1)


def save_json(path: Path, data: list | dict, dry_run: bool = False) -> None:
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Derived URL helpers (for documentation — not stored in JSON)
# ---------------------------------------------------------------------------

def embed_url(video_id: str) -> str:
    return f"https://www.youtube.com/embed/{video_id}"


def watch_url(video_id: str) -> str:
    return f"https://youtube.com/watch?v={video_id}"


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

def build(dry_run: bool = False) -> dict:
    """Build the full catalog and return stats."""

    # --- Load source files ---
    channels: list[dict] = load_json(CHANNELS_JSON)
    categories: list[dict] = load_json(CATEGORIES_JSON)

    channel_ids = {ch["id"] for ch in channels}
    category_ids = {cat["id"] for cat in categories}

    # --- Load and merge all video source files ---
    all_videos: list[dict] = []
    video_counts_per_category: dict[str, int] = {}

    # Track video_id occurrences for cross-category reporting
    video_id_to_categories: dict[str, list[str]] = {}

    for cat in categories:
        cat_id = cat["id"]
        video_file = VIDEOS_DIR / f"{cat_id}.json"

        if not video_file.exists():
            print(f"  WARNING: Missing video file for category '{cat_id}' — skipping")
            video_counts_per_category[cat_id] = 0
            continue

        videos = load_json(video_file)
        if not isinstance(videos, list):
            print(f"  ERROR: {video_file} must be a JSON array", file=sys.stderr)
            sys.exit(1)

        # Validate required fields and cross-references
        seen_in_category: set[str] = set()
        for v in videos:
            vid = v.get("video_id", "?")

            # Intra-category duplicate check (always an error)
            if vid in seen_in_category:
                print(
                    f"  ERROR: Duplicate video_id '{vid}' appears twice in {cat_id}.json",
                    file=sys.stderr,
                )
                sys.exit(1)
            seen_in_category.add(vid)

            # Cross-reference checks
            if v.get("channel_id") not in channel_ids:
                print(
                    f"  ERROR: video '{vid}' in {cat_id}.json has unknown channel_id '{v.get('channel_id')}'"
                    f" — not in channels.json",
                    file=sys.stderr,
                )
                sys.exit(1)

            if v.get("category_id") != cat_id:
                print(
                    f"  ERROR: video '{vid}' in {cat_id}.json has category_id '{v.get('category_id')}'"
                    f" but filename implies '{cat_id}'",
                    file=sys.stderr,
                )
                sys.exit(1)

            # Override id to be globally unique: "{category_id}:youtube:{video_id}"
            # This allows the same YouTube video to appear in multiple categories.
            v = dict(v)  # shallow copy — don't mutate source
            v["id"] = f"{cat_id}:youtube:{vid}"

            # Track cross-category usage
            video_id_to_categories.setdefault(vid, []).append(cat_id)

            all_videos.append(v)

        video_counts_per_category[cat_id] = len(videos)

    # --- Report cross-listed videos (info only, not an error) ---
    cross_listed = {vid: cats for vid, cats in video_id_to_categories.items() if len(cats) > 1}
    if cross_listed:
        print(f"  INFO: {len(cross_listed)} video(s) cross-listed across categories:")
        for vid, cats in cross_listed.items():
            print(f"    youtube:{vid}  →  {', '.join(cats)}")

    # --- Build index.json ---
    index = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": str(date.today()),
        "counts": {
            "channels": len(channels),
            "videos": len(all_videos),
        },
        "categories": categories,
        "channels": channels,
        "videos": all_videos,
    }

    # --- Build channels/*.json ---
    channel_outputs: dict[str, list[dict]] = {ch["id"]: [] for ch in channels}
    for v in all_videos:
        ch_id = v["channel_id"]
        if ch_id in channel_outputs:
            channel_outputs[ch_id].append(v)

    # --- Build categories/*.json ---
    category_outputs: dict[str, list[dict]] = {cat["id"]: [] for cat in categories}
    for v in all_videos:
        cat_id = v["category_id"]
        if cat_id in category_outputs:
            category_outputs[cat_id].append(v)

    # --- Write outputs ---
    if not dry_run:
        # index.json
        save_json(OUTPUT_INDEX, index)

        # channels/
        for ch_id, videos in channel_outputs.items():
            save_json(OUTPUT_CHANNELS_DIR / f"{ch_id}.json", videos)

        # categories/
        for cat_id, videos in category_outputs.items():
            save_json(OUTPUT_CATEGORIES_DIR / f"{cat_id}.json", videos)

    # --- Stats ---
    return {
        "total_videos": len(all_videos),
        "channels": len(channels),
        "categories": len(categories),
        "per_category": video_counts_per_category,
        "per_channel": {ch_id: len(vids) for ch_id, vids in channel_outputs.items()},
    }


def print_stats(stats: dict) -> None:
    print(f"\n{'='*50}")
    print(f"  Total videos : {stats['total_videos']}")
    print(f"  Channels     : {stats['channels']}")
    print(f"  Categories   : {stats['categories']}")
    print(f"\n  By category:")
    for cat_id, count in stats["per_category"].items():
        print(f"    {cat_id:<25} {count:>4} videos")
    print(f"\n  By channel:")
    for ch_id, count in stats["per_channel"].items():
        print(f"    {ch_id:<25} {count:>4} videos")
    print(f"{'='*50}\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the Islamic Stories catalog from source files.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print stats without writing any files",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Run validate_catalog.py after a successful build",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    mode = "DRY RUN" if args.dry_run else "BUILD"
    print(f"\nIslamic Stories — Catalog Builder [{mode}]")
    print(f"Source : {SOURCE_DIR}")
    print(f"Output : {ROOT}")

    stats = build(dry_run=args.dry_run)
    print_stats(stats)

    if not args.dry_run:
        print(f"Generated: {OUTPUT_INDEX}")
        print(f"Generated: {OUTPUT_CHANNELS_DIR}/")
        print(f"Generated: {OUTPUT_CATEGORIES_DIR}/")
        print("\nDone.")

        if args.validate:
            print("\nRunning validator...")
            validator = SCRIPT_DIR / "validate_catalog.py"
            result = subprocess.run([sys.executable, str(validator)], check=False)
            sys.exit(result.returncode)
    else:
        print("(Dry run — no files written)")


if __name__ == "__main__":
    main()