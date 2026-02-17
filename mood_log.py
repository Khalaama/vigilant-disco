#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

DATA_FILE = Path(__file__).with_name("data.json")


@dataclass
class MoodEntry:
    timestamp: str
    mood: str
    note: str


def ensure_data_file(path: Path) -> None:
    """Create the data file with an empty list when missing."""
    if not path.exists():
        path.write_text("[]\n", encoding="utf-8")


def load_entries(path: Path) -> list[MoodEntry]:
    """Load mood entries from JSON file."""
    ensure_data_file(path)
    try:
        raw: Any = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Databestand is ongeldig JSON: {path}. Controleer of het bestand geldig is."
        ) from exc

    if not isinstance(raw, list):
        raise ValueError(f"Dataformaat ongeldig in {path}: verwacht een lijst met entries.")

    entries: list[MoodEntry] = []
    for index, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Entry #{index} heeft ongeldig formaat (verwacht object).")

        timestamp = item.get("timestamp")
        mood = item.get("mood")
        note = item.get("note", "")

        if not isinstance(timestamp, str) or not isinstance(mood, str) or not isinstance(note, str):
            raise ValueError(
                f"Entry #{index} bevat ongeldige velden (timestamp/mood/note moeten tekst zijn)."
            )

        entries.append(MoodEntry(timestamp=timestamp, mood=mood, note=note))

    return entries


def save_entries(path: Path, entries: list[MoodEntry]) -> None:
    """Persist entries to JSON file."""
    payload = [entry.__dict__ for entry in entries]
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def add_entry(path: Path, mood: str, note: str) -> None:
    entries = load_entries(path)
    timestamp = datetime.now().isoformat(timespec="seconds")
    entries.append(MoodEntry(timestamp=timestamp, mood=mood.strip(), note=note.strip()))
    save_entries(path, entries)
    print(f"Toegevoegd: [{timestamp}] mood='{mood.strip()}' note='{note.strip()}'")


def list_entries(path: Path) -> None:
    entries = load_entries(path)
    if not entries:
        print("Nog geen entries gevonden.")
        return

    for index, entry in enumerate(entries, start=1):
        suffix = f" - {entry.note}" if entry.note else ""
        print(f"{index:>3}. {entry.timestamp} | {entry.mood}{suffix}")


def search_entries(path: Path, query: str) -> None:
    entries = load_entries(path)
    q = query.strip().lower()
    matches = [
        entry
        for entry in entries
        if q in entry.mood.lower() or q in entry.note.lower() or q in entry.timestamp.lower()
    ]

    if not matches:
        print(f"Geen resultaten voor '{query}'.")
        return

    for index, entry in enumerate(matches, start=1):
        suffix = f" - {entry.note}" if entry.note else ""
        print(f"{index:>3}. {entry.timestamp} | {entry.mood}{suffix}")


def show_stats(path: Path) -> None:
    entries = load_entries(path)
    total = len(entries)
    print(f"Totaal aantal entries: {total}")
    if total == 0:
        return

    counts: dict[str, int] = {}
    for entry in entries:
        key = entry.mood.lower().strip()
        counts[key] = counts.get(key, 0) + 1

    print("Verdeling per mood:")
    for mood, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
        pct = (count / total) * 100
        print(f"- {mood}: {count} ({pct:.1f}%)")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Eenvoudige mood logger CLI.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Voeg een nieuwe mood entry toe")
    add_parser.add_argument("mood", help="Mood label, bijv. blij of gestrest")
    add_parser.add_argument("note", nargs="?", default="", help="Optionele notitie")

    subparsers.add_parser("list", help="Toon alle mood entries")

    search_parser = subparsers.add_parser("search", help="Zoek in moods, notities of timestamps")
    search_parser.add_argument("query", help="Zoekterm")

    subparsers.add_parser("stats", help="Toon eenvoudige statistieken")

    return parser


def run_cli() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.command == "add":
            add_entry(DATA_FILE, args.mood, args.note)
        elif args.command == "list":
            list_entries(DATA_FILE)
        elif args.command == "search":
            search_entries(DATA_FILE, args.query)
        elif args.command == "stats":
            show_stats(DATA_FILE)
        else:
            parser.error("Onbekend commando.")
    except ValueError as exc:
        print(f"Fout: {exc}")
        return 1
    except OSError as exc:
        print(f"Bestandsfout: {exc}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli())
