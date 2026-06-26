#!/usr/bin/env python3
"""Download Japanese subtitles from ゆる言語学ラジオ channel."""

import subprocess
import sys

CHANNEL_URL = "https://www.youtube.com/@yurugengo"
SUBTITLES_DIR = "subtitles"

def main():
    cmd = [
        "/opt/homebrew/bin/yt-dlp",
        "--write-auto-subs",
        "--sub-lang", "ja",
        "--sub-format", "vtt",
        "--skip-download",
        "--playlist-end", "10",
        "--output", f"{SUBTITLES_DIR}/%(upload_date)s_%(id)s_%(title)s.%(ext)s",
        "--ignore-errors",
        "--no-warnings",
        CHANNEL_URL,
    ]
    print(f"Downloading subtitles from {CHANNEL_URL} ...")
    print("This may take a while for a large channel.\n")
    result = subprocess.run(cmd)
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
