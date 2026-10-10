#!/usr/bin/env python3
"""
Islamic Stories — YouTube Playlist Scraper
==========================================
Pulls playlist metadata using yt-dlp and outputs to source/videos/{category}.json.
No API key required.

Usage:
    python scraper.py --playlist <URL> --category <category_id> --channel <channel_id> [OPTIONS]

Examples:
    # Scrape Yousef Elkott prophet stories playlist
    python scraper.py \
        --playlist "https://www.youtube.com/playlist?list=PL6mMw2piuhMzvk--derzlpgPu8Cv5hJm3" \
        --category prophet_stories \
        --channel yousef_elkott \
        --depth detailed

    # Append to existing file (keeps previously curated entries)
    python scraper.py \
        --playlist "https://www.youtube.com/playlist?list=PLaiWvL5dLn1Dgvmx7taT8SuwMmMx8VBvS" \
        --category miracles \
        --channel abdulrahman_babgi \
        --depth detailed \
        --append

    # Append with skip list — auto-filters non-Islamic videos
    python scraper.py \
        --playlist "https://www.youtube.com/playlist?list=PLuBdGv4ne5nd2t-qF0g0UhjP5iyVZgbjE" \
        --category prophet_stories \
        --channel omar_abdulrahman \
        --depth detailed \
        --append \
        --skip-file data/islamic_stories/source/skip/omar_abdulrahman.json

    # Dry run — print JSON to stdout without writing
    python scraper.py \
        --playlist "https://youtu.be/..." \
        --category seerah \
        --channel yousef_elkott \
        --dry-run

Fields auto-filled by scraper:
    id, provider, video_id, channel_id, category_id,
    title.ar, language, duration_seconds, sort_order

Fields left for manual fill (edit output file after scraping):
    title.en       — English translation of title
    depth          — set via --depth flag (default: detailed)
    prophet_id     — optional, fill manually per video
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).parent
SOURCE_VIDEOS_DIR = SCRIPT_DIR.parent / "source" / "videos"

VALID_CATEGORIES = {
    "prophet_stories",
    "seerah",
    "companions",
    "miracles",
    "quran_creatures",
    "islamic_history",
    "afterlife",
}

VALID_CHANNELS = {
    "yousef_elkott",
    "abdulrahman_babgi",
    "omar_abdulrahman",
}

VALID_DEPTHS = {"summary", "detailed", "series"}

YOUTUBE_VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")


# ---------------------------------------------------------------------------
# yt-dlp helpers
# ---------------------------------------------------------------------------

def check_ytdlp() -> None:
    """Raise if yt-dlp is not installed."""
    try:
        subprocess.run(
            ["yt-dlp", "--version"],
            check=True,
            capture_output=True,
        )
    except FileNotFoundError:
        print("ERROR: yt-dlp not found. Install it with:  pip install yt-dlp", file=sys.stderr)
        sys.exit(1)


def fetch_playlist(url: str) -> list[dict]:
    """
    Run yt-dlp and return list of video metadata dicts.
    Fields used: id, title, duration, playlist_index.
    """
    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--dump-json",
        "--no-warnings",
        "--ignore-errors",
        url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")

    if result.returncode not in (0, 1):  # 1 = some errors but partial success
        print(f"ERROR: yt-dlp failed:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)

    entries = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
            entries.append(entry)
        except json.JSONDecodeError:
            continue

    return entries


# ---------------------------------------------------------------------------
# Conversion
# ---------------------------------------------------------------------------

def make_video_id(raw_id: str) -> str | None:
    """Return YouTube video ID if valid, else None."""
    if YOUTUBE_VIDEO_ID_RE.match(raw_id or ""):
        return raw_id
    return None


def entry_to_record(
    entry: dict,
    channel_id: str,
    category_id: str,
    depth: str,
    playlist_index: int,
) -> dict | None:
    """
    Convert a yt-dlp flat-playlist entry to our schema record.
    Returns None if the entry cannot be used (missing/invalid video ID).
    """
    video_id = make_video_id(entry.get("id") or entry.get("url", "").split("v=")[-1])
    if not video_id:
        print(f"  SKIP: invalid or missing video_id — {entry.get('title', '?')}", file=sys.stderr)
        return None

    title_ar = (entry.get("title") or "").strip()
    duration = entry.get("duration") or 0

    record = {
        "id": f"youtube:{video_id}",
        "provider": "youtube",
        "video_id": video_id,
        "channel_id": channel_id,
        "category_id": category_id,
        "title": {
            "ar": title_ar,
            # "en": ""  <-- fill manually after scraping
        },
        "language": "ar",
        "depth": depth,
        "duration_seconds": int(duration),
        "sort_order": playlist_index,
    }
    return record


# ---------------------------------------------------------------------------
# Skip list
# ---------------------------------------------------------------------------

def load_skip_ids(path: Path | None) -> set[str]:
    """
    Load a set of video_ids to skip from a JSON file.
    File format: a JSON array of strings (video_ids), with optional inline comments
    using a 'comment' key — those are ignored.

    Example:
        [
          "6IIF8lZxpAg",
          "ehnt5oG6Ukc"
        ]

    Returns an empty set if path is None or file doesn't exist.
    """
    if path is None:
        return set()
    if not path.exists():
        print(f"WARNING: skip file not found: {path}", file=sys.stderr)
        return set()
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(data, list):
            print(f"WARNING: skip file must be a JSON array, got {type(data).__name__}", file=sys.stderr)
            return set()
        ids = {item for item in data if isinstance(item, str)}
        print(f"  skip list: {len(ids)} video_ids loaded from {path.name}")
        return ids
    except json.JSONDecodeError as e:
        print(f"WARNING: invalid JSON in skip file {path}: {e}", file=sys.stderr)
        return set()


# ---------------------------------------------------------------------------
# File I/O
# ---------------------------------------------------------------------------

def load_existing(path: Path) -> list[dict]:
    """Load existing JSON array from file. Returns [] if file empty or missing."""
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def save(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(records, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Merge logic (append mode)
# ---------------------------------------------------------------------------

def merge_records(
    existing: list[dict],
    new: list[dict],
    skip_ids: set[str],
) -> tuple[list[dict], int, int, int]:
    """
    Merge new records into existing, skipping duplicates by video_id
    and removing any entries (existing or new) whose video_id is in skip_ids.

    Returns (merged_list, added_count, skipped_duplicates, skipped_by_list).
    """
    # First: purge any existing entries that are now in the skip list
    cleaned_existing = [r for r in existing if r["video_id"] not in skip_ids]
    purged = len(existing) - len(cleaned_existing)

    existing_ids = {r["video_id"] for r in cleaned_existing}
    added = 0
    skipped_dup = 0
    skipped_list = purged

    merged = list(cleaned_existing)

    for record in new:
        vid = record["video_id"]
        if vid in skip_ids:
            skipped_list += 1
        elif vid in existing_ids:
            skipped_dup += 1
        else:
            merged.append(record)
            existing_ids.add(vid)
            added += 1

    return merged, added, skipped_dup, skipped_list


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scrape a YouTube playlist and output to source/videos/{category}.json",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--playlist", "-p",
        required=True,
        metavar="URL",
        help="YouTube playlist or video URL",
    )
    parser.add_argument(
        "--category", "-c",
        required=True,
        choices=sorted(VALID_CATEGORIES),
        metavar="CATEGORY",
        help=f"Target category: {', '.join(sorted(VALID_CATEGORIES))}",
    )
    parser.add_argument(
        "--channel", "-ch",
        required=True,
        choices=sorted(VALID_CHANNELS),
        metavar="CHANNEL",
        help=f"Channel ID: {', '.join(sorted(VALID_CHANNELS))}",
    )
    parser.add_argument(
        "--depth", "-d",
        default="detailed",
        choices=sorted(VALID_DEPTHS),
        help="Content depth (default: detailed)",
    )
    parser.add_argument(
        "--append", "-a",
        action="store_true",
        help="Append to existing file instead of overwriting",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print records to stdout without writing to disk",
    )
    parser.add_argument(
        "--start-order",
        type=int,
        default=1,
        metavar="N",
        help="Starting sort_order value (default: 1). Use with --append to continue numbering.",
    )
    parser.add_argument(
        "--skip-file",
        metavar="PATH",
        help="Path to a JSON file containing an array of video_ids to exclude. "
             "Matching entries are filtered from both new and existing records.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    check_ytdlp()

    output_path = SOURCE_VIDEOS_DIR / f"{args.category}.json"
    skip_path = Path(args.skip_file) if args.skip_file else None
    skip_ids = load_skip_ids(skip_path)

    print(f"Fetching playlist: {args.playlist}")
    print(f"  channel:  {args.channel}")
    print(f"  category: {args.category}")
    print(f"  depth:    {args.depth}")
    print(f"  output:   {output_path}")
    print()

    raw_entries = fetch_playlist(args.playlist)
    print(f"Fetched {len(raw_entries)} entries from yt-dlp")

    new_records: list[dict] = []
    for i, entry in enumerate(raw_entries, start=args.start_order):
        record = entry_to_record(
            entry=entry,
            channel_id=args.channel,
            category_id=args.category,
            depth=args.depth,
            playlist_index=i,
        )
        if record:
            new_records.append(record)

    print(f"Converted {len(new_records)} valid records")

    # Apply skip list to new records (dry-run shows filtered result)
    if skip_ids:
        before = len(new_records)
        new_records = [r for r in new_records if r["video_id"] not in skip_ids]
        filtered = before - len(new_records)
        if filtered:
            print(f"Filtered {filtered} records matched by skip list")

    if args.dry_run:
        print("\n--- DRY RUN OUTPUT ---")
        print(json.dumps(new_records, ensure_ascii=False, indent=2))
        return

    if args.append:
        existing = load_existing(output_path)
        merged, added, skipped_dup, skipped_list = merge_records(existing, new_records, skip_ids)
        save(output_path, merged)
        print(f"\nDone. Added {added} new records.")
        if skipped_dup:
            print(f"       Skipped {skipped_dup} duplicates.")
        if skipped_list:
            print(f"       Removed/skipped {skipped_list} entries matched by skip list.")
        print(f"Total in file: {len(merged)}")
    else:
        save(output_path, new_records)
        print(f"\nDone. Wrote {len(new_records)} records to {output_path}")

    print()
    print("Next: edit the output file to fill in:")
    print("  - title.en     (English translation)")
    print("  - prophet_id   (optional, for prophet-specific filtering)")
    print("  - depth        (if you need to override per-video)")


if __name__ == "__main__":
    main()