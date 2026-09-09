from pathlib import Path

from audiograbber.downloader import DownloadRequest, build_ytdlp_options
from audiograbber.settings import SettingsManager
from audiograbber.utils import generate_safe_filename, parse_metadata


def test_build_ytdlp_options_uses_audio_format() -> None:
    options = build_ytdlp_options(output_dir="/tmp/audio", output_format="mp3")

    assert options["format"] == "bestaudio/best"
    assert options["outtmpl"] == "/tmp/audio/%(title)s.%(ext)s"
    assert options["extractor_args"] == {"youtube": {"player_client": ["web"]}}
    assert options["retries"] == 3
    assert options["postprocessors"][0]["key"] == "FFmpegExtractAudio"


def test_settings_round_trip() -> None:
    settings_path = Path("/tmp/audiograbber_settings_test.json")
    settings_path.unlink(missing_ok=True)

    manager = SettingsManager(settings_path)
    manager.set_theme("dark")
    manager.set_download_dir("/tmp/downloads")
    manager.set_value("max_workers", 4)

    manager.save()
    reloaded = SettingsManager(settings_path)

    assert reloaded.get_theme() == "dark"
    assert reloaded.get_download_dir() == "/tmp/downloads"
    assert reloaded.get_value("max_workers") == 4


def test_filename_generation() -> None:
    name = generate_safe_filename("My Song / Intro: The Remix?", ".mp3")
    assert name == "My_Song_Intro_The_Remix.mp3"


def test_metadata_parsing() -> None:
    data = {
        "title": "Demo Track",
        "uploader": "Test User",
        "duration": 145,
        "webpage_url": "https://example.com/watch?v=123",
    }

    result = parse_metadata(data)

    assert result["title"] == "Demo Track"
    assert result["artist"] == "Test User"
    assert result["duration"] == 145
    assert result["source_url"] == "https://example.com/watch?v=123"
