# Audio Grabber

Audio Grabber is a polished desktop application for downloading and converting YouTube audio into local MP3 files. It is designed for local use with a clean PySide6 interface, a queue-based downloader, and strong persistence for unfinished jobs.

## Features

- Queue-based YouTube downloads with multiple workers
- yt-dlp integration for high-quality audio extraction
- FFmpeg conversion pipeline for clean audio output
- Progress tracking with ETA and status updates
- Resume-safe queue persistence across app restarts
- Dark/light theme switching
- Settings management for download directory, theme, and worker count
- Logging and runtime diagnostics for troubleshooting
- Unit tests for downloader settings, filenames, and metadata normalization

## Project Structure

- [audiograbber/__init__.py](audiograbber/__init__.py)
- [audiograbber/__main__.py](audiograbber/__main__.py)
- [audiograbber/app.py](audiograbber/app.py)
- [audiograbber/downloader.py](audiograbber/downloader.py)
- [audiograbber/audio_conversion.py](audiograbber/audio_conversion.py)
- [audiograbber/settings.py](audiograbber/settings.py)
- [audiograbber/utils.py](audiograbber/utils.py)
- [audiograbber/logging.py](audiograbber/logging.py)
- [audiograbber/ui/main_window.py](audiograbber/ui/main_window.py)
- [tests/test_app_logic.py](tests/test_app_logic.py)

## Requirements

- Python 3.11+
- FFmpeg installed and available on PATH
- PySide6
- yt-dlp
- PyInstaller (optional for packaging)

## Local Setup

1. Clone the project.
2. Create and activate a virtual environment.
3. Install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

4. Ensure FFmpeg is installed:

```bash
ffmpeg -version
```

5. Launch the app:

```bash
python -m audiograbber
```

## Running Tests

```bash
test -f .venv/bin/activate && . .venv/bin/activate
python -m pytest -q
```

## Packaging with PyInstaller

Build a packaged desktop app for local use:

```bash
pyinstaller --noconfirm --onedir --windowed \
  --name "AudioGrabber" \
  --add-data "audiograbber:./audiograbber" \
  --paths . \
  -m audiograbber
```

If you want a single-file executable instead:

```bash
pyinstaller --noconfirm --onefile --windowed \
  --name "AudioGrabber" \
  --paths . \
  -m audiograbber
```

The executable will be generated under the `dist/` directory.

## Usage Notes

- Add a YouTube URL to the queue using the input field.
- Select a destination folder for downloads in the app settings area.
- Multiple workers can be configured in the settings manager.
- Unfinished jobs persist in the queue state file and can be resumed on the next launch.
- Logs are written to the user profile under `.audiograbber` for diagnostics.

## Troubleshooting

- If downloads fail, verify that FFmpeg is installed and on PATH.
- If yt-dlp cannot parse a URL, try a standard YouTube watch URL.
- If the app cannot start, check the generated log file in the user config directory.

## License

This project is provided for local desktop use and can be adapted for your own workflow.
