from __future__ import annotations

import sys
from pathlib import Path

from PySide6 import QtCore, QtWidgets

from audiograbber.logging import configure_logging
from audiograbber.settings import SettingsManager
from audiograbber.ui.main_window import MainWindow

logger = configure_logging(Path.home() / ".audiograbber" / "app.log")


def main() -> int:
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("Audio Grabber")
    app.setApplicationVersion("0.1.0")

    settings = SettingsManager()
    window = MainWindow(settings=settings)
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
