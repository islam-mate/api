"""
modules/location/db.py
======================
Local SQLite helpers — city search, reverse geocode, and Nominatim cache.

Imported by:
  module.py      → db_search, db_reverse_geocode
  geocoding.py   → cache_to_db
"""

import sqlite3
from pathlib import Path


DB_PATH = Path("data/cities.db")


# ── Search ─────────────────────────────────────────────────────────────────────

def db_search(q: str, limit: int = 5) -> list[dict]:
    """Search cities.db — exact match first, then prefix, then full partial."""
    if not DB_PATH.exists():
        return []

    try:
        con = sqlite3.connect(DB_PATH)
        con.row_factory = sqlite3.Row

        # Exact match
        rows = con.execute("""
            SELECT
                ci.name,
                ci.name_local,
                ci.latitude,
                ci.longitude,
                ci.timezone,
                g.name AS governorate,
                c.name AS country,
                c.iso2
            FROM cities ci
            JOIN governorates g ON g.id = ci.governorate_id
            JOIN countries c ON c.id = g.country_id
            WHERE ci.name = ? OR ci.name_local = ?
            ORDER BY
                CASE WHEN ci.name = ? THEN 0 ELSE 1 END
            LIMIT ?
        """, (q, q, q, limit)).fetchall()

        # Prefix match
        if not rows:
            rows = con.execute("""
                SELECT
                    ci.name,
                    ci.name_local,
                    ci.latitude,
                    ci.longitude,
                    ci.timezone,
                    g.name AS governorate,
                    c.name AS country,
                    c.iso2
                FROM cities ci
                JOIN governorates g ON g.id = ci.governorate_id
                JOIN countries c ON c.id = g.country_id
                WHERE ci.name LIKE ? OR ci.name_local LIKE ?
                ORDER BY
                    CASE WHEN ci.name LIKE ? THEN 0 ELSE 1 END
                LIMIT ?
            """, (f"{q}%", f"{q}%", f"{q}%", limit)).fetchall()

        # Full partial match
        if not rows:
            rows = con.execute("""
                SELECT
                    ci.name,
                    ci.name_local,
                    ci.latitude,
                    ci.longitude,
                    ci.timezone,
                    g.name AS governorate,
                    c.name AS country,
                    c.iso2
                FROM cities ci
                JOIN governorates g ON g.id = ci.governorate_id
                JOIN countries c ON c.id = g.country_id
                WHERE ci.name LIKE ? OR ci.name_local LIKE ?
                LIMIT ?
            """, (f"%{q}%", f"%{q}%", limit)).fetchall()

        con.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


# ── Reverse geocode ─────────────────────────────────────────────────────────────

def db_reverse_geocode(lat: float, lng: float) -> dict | None:
    """Find nearest city in DB for given coordinates (within ~50 km)."""
    if not DB_PATH.exists():
        return None

    try:
        con = sqlite3.connect(DB_PATH)
        con.row_factory = sqlite3.Row

        delta = 0.5  # ~55 km bounding box
        rows = con.execute("""
            SELECT
                ci.name,
                ci.name_local,
                ci.latitude,
                ci.longitude,
                ci.timezone,
                g.name AS governorate,
                c.name AS country,
                c.iso2,
                (
                    (ci.latitude - ?) * (ci.latitude - ?) +
                    (ci.longitude - ?) * (ci.longitude - ?)
                ) AS dist_sq
            FROM cities ci
            JOIN governorates g ON g.id = ci.governorate_id
            JOIN countries c ON c.id = g.country_id
            WHERE
                ci.latitude BETWEEN ? AND ?
                AND ci.longitude BETWEEN ? AND ?
            ORDER BY dist_sq ASC
            LIMIT 1
        """, (
            lat, lat, lng, lng,
            lat - delta, lat + delta,
            lng - delta, lng + delta
        )).fetchone()

        con.close()
        return dict(rows) if rows else None
    except Exception:
        return None


# ── Cache ───────────────────────────────────────────────────────────────────────

def cache_to_db(result: dict) -> None:
    """Cache a Nominatim result into cities.db for offline use later."""
    if not DB_PATH.exists():
        return

    try:
        con = sqlite3.connect(DB_PATH)

        existing = con.execute(
            "SELECT id FROM cities WHERE name = ? AND source_type = 'nominatim_cache'",
            (result["name"],)
        ).fetchone()
        if existing:
            con.close()
            return

        # Country
        country_row = con.execute(
            "SELECT id FROM countries WHERE name = ?",
            (result["country"],)
        ).fetchone()

        if country_row:
            country_id = country_row[0]
        else:
            cur = con.execute(
                "INSERT OR IGNORE INTO countries (name, iso2, timezone) VALUES (?, ?, ?)",
                (result["country"], result.get("country_code", "XX").upper(),
                 result.get("timezone", "UTC"))
            )
            country_id = cur.lastrowid

        # Governorate
        gov_name = result.get("governorate") or result["country"]
        gov_row = con.execute(
            "SELECT id FROM governorates WHERE country_id = ? AND name = ?",
            (country_id, gov_name)
        ).fetchone()

        if gov_row:
            governorate_id = gov_row[0]
        else:
            cur = con.execute(
                "INSERT OR IGNORE INTO governorates (country_id, name) VALUES (?, ?)",
                (country_id, gov_name)
            )
            governorate_id = cur.lastrowid

        # City
        con.execute("""
            INSERT OR IGNORE INTO cities
            (governorate_id, name, name_local, latitude, longitude, timezone, source_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            governorate_id,
            result["name"],
            result.get("name_local"),
            result["latitude"],
            result["longitude"],
            result.get("timezone", "UTC"),
            "nominatim_cache"
        ))

        con.commit()
        con.close()
    except Exception:
        pass  # Cache failure is not critical
