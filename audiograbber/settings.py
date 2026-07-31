from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class SettingsManager:
    """Manage persisted application settings in a JSON file."""

    DEFAULTS: dict[str, Any] = {
        "theme": "dark",
        "download_dir": str(Path.home() / "Downloads" / "audiograbber"),
        "max_workers": 3,
        "keep_queue_on_restart": True,
    }

    def __init__(self, settings_path: str | Path | None = None) -> None:
        self.settings_path = Path(settings_path or Path.home() / ".audiograbber" / "settings.json")
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        self._data: dict[str, Any] = dict(self.DEFAULTS)
        self.load()

    def load(self) -> dict[str, Any]:
        if not self.settings_path.exists():
            self.save()
            return dict(self._data)
        try:
            with self.settings_path.open("r", encoding="utf-8") as file:
                loaded = json.load(file)
        except (json.JSONDecodeError, OSError):
            self._data = dict(self.DEFAULTS)
            self.save()
            return dict(self._data)

        self._data = {**self.DEFAULTS, **loaded}
        return dict(self._data)

    def save(self) -> None:
        with self.settings_path.open("w", encoding="utf-8") as file:
            json.dump(self._data, file, indent=2, sort_keys=True)

    def set_value(self, key: str, value: Any) -> None:
        self._data[key] = value
        self.save()

    def get_value(self, key: str, default: Any | None = None) -> Any:
        return self._data.get(key, default)

    def set_theme(self, theme: str) -> None:
        self._data["theme"] = theme.lower()
        self.save()

    def get_theme(self) -> str:
        return str(self._data.get("theme", self.DEFAULTS["theme"]))

    def set_download_dir(self, path: str | Path) -> None:
        self._data["download_dir"] = str(Path(path))
        self.save()

    def get_download_dir(self) -> str:
        return str(self._data.get("download_dir", self.DEFAULTS["download_dir"]))

    def set_max_workers(self, workers: int) -> None:
        self._data["max_workers"] = max(1, int(workers))
        self.save()

    def get_max_workers(self) -> int:
        return int(self._data.get("max_workers", self.DEFAULTS["max_workers"]))
