from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any


class AudioConverter:
    """Convert audio files to the requested output format using FFmpeg."""

    def __init__(self, ffmpeg_path: str = "ffmpeg") -> None:
        self.ffmpeg_path = ffmpeg_path

    def convert(self, source_path: str | Path, destination_path: str | Path, *, format_name: str = "mp3") -> Path:
        source = Path(source_path)
        destination = Path(destination_path)
        destination.parent.mkdir(parents=True, exist_ok=True)

        command = [
            self.ffmpeg_path,
            "-y",
            "-i",
            str(source),
            "-vn",
            "-acodec",
            "libmp3lame" if format_name.lower() == "mp3" else "pcm_s16le",
            "-q:a",
            "2",
            str(destination),
        ]

        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr.strip() or f"FFmpeg failed for {source}")
        return destination

    def convert_from_download(self, source_path: str | Path, output_dir: str | Path, target_format: str = "mp3") -> Path:
        source = Path(source_path)
        destination = Path(output_dir) / f"{source.stem}.{target_format.lower()}"
        return self.convert(source, destination, format_name=target_format)
