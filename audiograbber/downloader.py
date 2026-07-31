from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from queue import Queue
from threading import Lock, Thread
from typing import Any, Callable

import yt_dlp

from audiograbber.logging import configure_logging
from audiograbber.utils import format_eta, generate_safe_filename, parse_metadata

logger = configure_logging()


@dataclass
class DownloadRequest:
    url: str
    output_dir: str
    output_format: str = "mp3"
    filename: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    status: str = "queued"
    progress: float = 0.0
    eta: float = 0.0
    eta_text: str = "--:--"
    error: str | None = None

    def __post_init__(self) -> None:
        if not self.eta_text:
            self.eta_text = format_eta(self.eta)


def build_ytdlp_options(output_dir: str, output_format: str = "mp3") -> dict[str, Any]:
    """Create yt-dlp options for audio extraction."""
    return {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s"),
        "quiet": True,
        "noplaylist": True,
        "ignoreerrors": False,
        "no_warnings": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": output_format,
                "preferredquality": "0",
            }
        ],
        "progress_hooks": [],
    }


class DownloadQueue:
    """Thread-safe queue with persistence support."""

    def __init__(self, state_path: str | Path | None = None) -> None:
        self.state_path = Path(state_path) if state_path else Path.home() / ".audiograbber" / "queue.json"
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self._queue: Queue[DownloadRequest] = Queue()
        self._lock = Lock()
        self._requests: list[DownloadRequest] = []
        self._load_state()

    def enqueue(self, request: DownloadRequest) -> None:
        with self._lock:
            self._requests.append(request)
            self._queue.put(request)
            self._persist_state()

    def dequeue(self) -> DownloadRequest | None:
        try:
            item = self._queue.get_nowait()
            with self._lock:
                if item in self._requests:
                    item.status = "running"
                    self._persist_state()
            return item
        except Exception:
            return None

    def mark_done(self, request: DownloadRequest, output_path: str | Path | None = None) -> None:
        with self._lock:
            request.status = "done"
            request.progress = 100.0
            request.eta = 0.0
            request.eta_text = "00:00"
            if output_path:
                request.filename = str(output_path)
            self._persist_state()

    def mark_failed(self, request: DownloadRequest, error: str) -> None:
        with self._lock:
            request.status = "failed"
            request.error = error
            request.progress = 0.0
            request.eta = 0.0
            request.eta_text = "--:--"
            self._persist_state()

    def all_requests(self) -> list[DownloadRequest]:
        with self._lock:
            return list(self._requests)

    def _persist_state(self) -> None:
        serializable = [
            {
                "url": item.url,
                "output_dir": item.output_dir,
                "output_format": item.output_format,
                "filename": item.filename,
                "metadata": item.metadata,
                "status": item.status,
                "progress": item.progress,
                "eta": item.eta,
                "eta_text": item.eta_text,
                "error": item.error,
            }
            for item in self._requests
        ]
        with self.state_path.open("w", encoding="utf-8") as file:
            json.dump(serializable, file, indent=2)

    def _load_state(self) -> None:
        if not self.state_path.exists():
            return
        try:
            with self.state_path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except (json.JSONDecodeError, OSError):
            return

        for item in data:
            request = DownloadRequest(
                url=item.get("url", ""),
                output_dir=item.get("output_dir", ""),
                output_format=item.get("output_format", "mp3"),
                filename=item.get("filename"),
                metadata=item.get("metadata", {}),
                status=item.get("status", "queued"),
                progress=float(item.get("progress", 0.0)),
                eta=float(item.get("eta", 0.0)),
                eta_text=str(item.get("eta_text", "--:--")),
                error=item.get("error"),
            )
            self._requests.append(request)
            if request.status in {"queued", "running"}:
                self._queue.put(request)


class AudioDownloader:
    """Download and convert a YouTube URL to audio using yt-dlp and FFmpeg."""

    def __init__(self, ffmpeg_path: str | None = None) -> None:
        self.ffmpeg_path = ffmpeg_path or "ffmpeg"

    def download(self, request: DownloadRequest) -> DownloadRequest:
        request.status = "running"
        request.error = None
        start_time = time.time()

        try:
            output_dir = Path(request.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            options = build_ytdlp_options(str(output_dir), request.output_format)
            options["progress_hooks"] = [self._make_progress_hook(request, start_time)]

            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(request.url, download=True)
                request.metadata = parse_metadata(info or {})
                request.filename = self._resolve_output_path(output_dir, request, info)
                request.status = "done"
                request.progress = 100.0
                request.eta = 0.0
                request.eta_text = "00:00"
                return request
        except Exception as exc:  # pragma: no cover - runtime diagnostics path
            logger.exception("Download failed for %s", request.url)
            request.status = "failed"
            request.error = str(exc)
            request.progress = 0.0
            request.eta = 0.0
            request.eta_text = "--:--"
            return request

    def _resolve_output_path(self, output_dir: Path, request: DownloadRequest, info: dict[str, Any] | None) -> str:
        title = str((info or {}).get("title") or request.metadata.get("title") or "audio")
        filename = generate_safe_filename(title, f".{request.output_format}")
        return str(output_dir / filename)

    def _make_progress_hook(self, request: DownloadRequest, start_time: float) -> Callable[[dict[str, Any]], None]:
        def _hook(event: dict[str, Any]) -> None:
            if event.get("status") == "downloading":
                total = event.get("total_bytes") or event.get("total_bytes_estimate") or 0
                downloaded = event.get("downloaded_bytes") or 0
                if total > 0:
                    request.progress = min(100.0, (downloaded / total) * 100)
                else:
                    request.progress = 0.0
                elapsed = max(time.time() - start_time, 1.0)
                rate = downloaded / elapsed if elapsed else 0
                remaining = max(total - downloaded, 0)
                request.eta = remaining / rate if rate > 0 and remaining > 0 else 0.0
                request.eta_text = format_eta(request.eta)
            elif event.get("status") == "finished":
                request.progress = 100.0
                request.eta = 0.0
                request.eta_text = "00:00"
        return _hook


__all__ = [
    "AudioDownloader",
    "DownloadQueue",
    "DownloadRequest",
    "build_ytdlp_options",
]
