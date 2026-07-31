from __future__ import annotations

import re
from typing import Any, Mapping


def generate_safe_filename(base_name: str, extension: str = ".mp3") -> str:
    """Create a safe file name by stripping invalid filesystem characters."""
    cleaned = re.sub(r"[^a-zA-Z0-9_\-\s]", "_", base_name.strip())
    cleaned = re.sub(r"[\s]+", "_", cleaned).strip("_")
    cleaned = cleaned or "audio"
    if extension and not extension.startswith("."):
        extension = f".{extension}"
    return f"{cleaned}{extension}"


def parse_metadata(data: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize metadata payload from yt-dlp into a consistent dictionary."""
    title = str(data.get("title") or "Untitled Track")
    artist = data.get("uploader") or data.get("artist") or "Unknown Artist"
    duration = data.get("duration")
    return {
        "title": title,
        "artist": str(artist),
        "duration": int(duration) if duration is not None else 0,
        "source_url": str(data.get("webpage_url") or data.get("url") or ""),
    }


def format_eta(seconds: float) -> str:
    if seconds <= 0:
        return "--:--"
    total_seconds = int(seconds)
    minutes = total_seconds // 60
    hours = minutes // 60
    minutes = minutes % 60
    seconds = total_seconds % 60
    if hours:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"
