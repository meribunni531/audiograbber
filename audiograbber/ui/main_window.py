from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from PySide6 import QtCore, QtGui, QtWidgets

from audiograbber.downloader import AudioDownloader, DownloadQueue, DownloadRequest
from audiograbber.settings import SettingsManager


class DownloadTableModel(QtCore.QAbstractTableModel):
    def __init__(self, queue: DownloadQueue) -> None:
        super().__init__()
        self.queue = queue

    def rowCount(self, parent: QtCore.QModelIndex | QtCore.QPersistentModelIndex | None = None) -> int:
        return len(self.queue.all_requests())

    def columnCount(self, parent: QtCore.QModelIndex | QtCore.QPersistentModelIndex | None = None) -> int:
        return 5

    def data(self, index: QtCore.QModelIndex, role: int = QtCore.Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        request = self.queue.all_requests()[index.row()]
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            columns = [
                request.url,
                request.status,
                f"{request.progress:.0f}%",
                str(request.eta),
                request.filename or "",
            ]
            return columns[index.column()]
        return None

    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, role: int = QtCore.Qt.ItemDataRole.DisplayRole) -> Any:
        if orientation == QtCore.Qt.Orientation.Horizontal and role == QtCore.Qt.ItemDataRole.DisplayRole:
            headers = ["URL", "Status", "Progress", "ETA", "Output"]
            return headers[section]
        return None


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, settings: SettingsManager | None = None) -> None:
        super().__init__()
        self.settings = settings or SettingsManager()
        self.queue = DownloadQueue(self.settings.get_value("queue_path", Path.home() / ".audiograbber" / "queue.json"))
        self.downloader = AudioDownloader()
        self.setWindowTitle("Audio Grabber")
        self.resize(1100, 700)
        self._build_ui()
        self.apply_theme(self.settings.get_theme())

    def _build_ui(self) -> None:
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)

        toolbar = QtWidgets.QHBoxLayout()
        self.url_input = QtWidgets.QLineEdit()
        self.url_input.setPlaceholderText("Paste YouTube URL here")
        self.add_button = QtWidgets.QPushButton("Add to Queue")
        self.add_button.clicked.connect(self.add_url_to_queue)

        toolbar.addWidget(self.url_input)
        toolbar.addWidget(self.add_button)
        layout.addLayout(toolbar)

        controls = QtWidgets.QHBoxLayout()
        self.download_dir = QtWidgets.QLineEdit(self.settings.get_download_dir())
        self.download_dir_button = QtWidgets.QPushButton("Choose Folder")
        self.download_dir_button.clicked.connect(self.choose_download_dir)
        self.theme_combo = QtWidgets.QComboBox()
        self.theme_combo.addItems(["dark", "light"])
        self.theme_combo.setCurrentText(self.settings.get_theme())
        self.theme_combo.currentTextChanged.connect(self.apply_theme)
        controls.addWidget(QtWidgets.QLabel("Download folder:"))
        controls.addWidget(self.download_dir)
        controls.addWidget(self.download_dir_button)
        controls.addWidget(QtWidgets.QLabel("Theme:"))
        controls.addWidget(self.theme_combo)
        layout.addLayout(controls)

        self.table = QtWidgets.QTableView()
        self.table_model = DownloadTableModel(self.queue)
        self.table.setModel(self.table_model)
        self.table.resizeColumnsToContents()
        layout.addWidget(self.table)

        self.status_bar = QtWidgets.QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def add_url_to_queue(self) -> None:
        url = self.url_input.text().strip()
        if not url:
            self.status_bar.showMessage("Enter a URL first.")
            return
        output_dir = self.download_dir.text().strip() or self.settings.get_download_dir()
        request = DownloadRequest(url=url, output_dir=output_dir)
        self.queue.enqueue(request)
        self.table_model.beginResetModel()
        self.table_model.endResetModel()
        self.status_bar.showMessage(f"Queued: {url}")
        self.url_input.clear()

        QtCore.QTimer.singleShot(0, lambda: self.start_workers())

    def choose_download_dir(self) -> None:
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Choose download folder")
        if folder:
            self.download_dir.setText(folder)
            self.settings.set_download_dir(folder)
            self.status_bar.showMessage(f"Download directory set to {folder}")

    def start_workers(self) -> None:
        total_workers = self.settings.get_max_workers()
        if not hasattr(self, "_executor") or self._executor is None:
            self._executor = ThreadPoolExecutor(max_workers=max(1, total_workers))
        for _ in range(total_workers):
            self._executor.submit(self._download_worker)

    def _download_worker(self) -> None:
        request = self.queue.dequeue()
        if request is None:
            return
        result = self.downloader.download(request)
        self.queue.mark_done(result, result.filename)
        self.table_model.beginResetModel()
        self.table_model.endResetModel()
        self.status_bar.showMessage(f"Finished: {result.url}")

    def apply_theme(self, theme_name: str) -> None:
        self.settings.set_theme(theme_name)
        palette = QtGui.QPalette()
        if theme_name.lower() == "dark":
            palette.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor("#121212"))
            palette.setColor(QtGui.QPalette.ColorRole.WindowText, QtGui.QColor("#f5f5f5"))
            palette.setColor(QtGui.QPalette.ColorRole.Base, QtGui.QColor("#1e1e1e"))
            palette.setColor(QtGui.QPalette.ColorRole.AlternateBase, QtGui.QColor("#2b2b2b"))
            palette.setColor(QtGui.QPalette.ColorRole.ToolTipBase, QtGui.QColor("#ffffff"))
            palette.setColor(QtGui.QPalette.ColorRole.ToolTipText, QtGui.QColor("#ffffff"))
            palette.setColor(QtGui.QPalette.ColorRole.Text, QtGui.QColor("#f5f5f5"))
            palette.setColor(QtGui.QPalette.ColorRole.Button, QtGui.QColor("#2b2b2b"))
            palette.setColor(QtGui.QPalette.ColorRole.ButtonText, QtGui.QColor("#f5f5f5"))
            palette.setColor(QtGui.QPalette.ColorRole.BrightText, QtGui.QColor("#ff0000"))
            palette.setColor(QtGui.QPalette.ColorRole.Link, QtGui.QColor("#80cbc4"))
            palette.setColor(QtGui.QPalette.ColorRole.Highlight, QtGui.QColor("#1e88e5"))
            palette.setColor(QtGui.QPalette.ColorRole.HighlightedText, QtGui.QColor("#ffffff"))
        else:
            palette.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor("#f4f4f4"))
            palette.setColor(QtGui.QPalette.ColorRole.WindowText, QtGui.QColor("#222222"))
            palette.setColor(QtGui.QPalette.ColorRole.Base, QtGui.QColor("#ffffff"))
            palette.setColor(QtGui.QPalette.ColorRole.AlternateBase, QtGui.QColor("#eaeaea"))
            palette.setColor(QtGui.QPalette.ColorRole.ToolTipBase, QtGui.QColor("#ffffff"))
            palette.setColor(QtGui.QPalette.ColorRole.ToolTipText, QtGui.QColor("#222222"))
            palette.setColor(QtGui.QPalette.ColorRole.Text, QtGui.QColor("#222222"))
            palette.setColor(QtGui.QPalette.ColorRole.Button, QtGui.QColor("#ffffff"))
            palette.setColor(QtGui.QPalette.ColorRole.ButtonText, QtGui.QColor("#222222"))
            palette.setColor(QtGui.QPalette.ColorRole.BrightText, QtGui.QColor("#ff0000"))
            palette.setColor(QtGui.QPalette.ColorRole.Link, QtGui.QColor("#0055cc"))
            palette.setColor(QtGui.QPalette.ColorRole.Highlight, QtGui.QColor("#3da4ff"))
            palette.setColor(QtGui.QPalette.ColorRole.HighlightedText, QtGui.QColor("#ffffff"))
        QtWidgets.QApplication.setPalette(palette)


__all__ = ["MainWindow"]
