#!/usr/bin/env python3
"""Build n-gram inverted index for subtitle search."""

import json
import re
from pathlib import Path

SUBTITLES_DIR = Path("subtitles")
VIDEOS_FILE   = Path("docs/videos.json")
NGRAMS_FILE   = Path("docs/ngrams.json")

def parse_vtt(filepath: Path) -> set[str]:
    """Extract unique subtitle lines from a .vtt file."""
    text = filepath.read_text(encoding="utf-8", errors="ignore")
    seen = set()
    blocks = re.split(r"\n{2,}", text)
    for block in blocks:
        lines = block.strip().splitlines()
        time_line = next((i for i, l in enumerate(lines) if "-->" in l), None)
        if time_line is None:
            continue
        raw = " ".join(lines[time_line + 1:])
        clean = re.sub(r"<[^>]+>", "", raw).strip()
        if clean:
            seen.add(clean)
    return seen

def normalize(text: str) -> str:
    """カタカナをひらがなに変換して検索を表記ゆれに対応させる。"""
    return "".join(
        chr(ord(ch) - 0x60) if "ァ" <= ch <= "ヶ" else ch
        for ch in text
    )

def get_ngrams(text: str, n: int = 2) -> set[str]:
    text = normalize(text)
    return {text[i:i+n] for i in range(len(text) - n + 1)}

def build_index():
    VIDEOS_FILE.parent.mkdir(exist_ok=True)
    vtt_files = sorted(SUBTITLES_DIR.glob("*.vtt"))
    print(f"Found {len(vtt_files)} subtitle files.")

    videos = []          # [{id, title}]
    seen_ids: dict[str, int] = {}
    video_texts: list[str] = []

    for vtt_path in vtt_files:
        stem = vtt_path.stem
        if stem.endswith(".ja"):
            stem = stem[:-3]
        if len(stem) >= 21 and stem[8] == "_" and stem[20] == "_":
            video_id = stem[9:20]
            title    = stem[21:]
        else:
            video_id = stem
            title    = stem

        lines = parse_vtt(vtt_path)
        text = " ".join(lines)

        if video_id in seen_ids:
            idx = seen_ids[video_id]
            video_texts[idx] += " " + text
        else:
            seen_ids[video_id] = len(videos)
            videos.append({"id": video_id, "title": title})
            video_texts.append(text)

    print(f"Parsed {len(videos)} unique videos. Building n-gram index...")

    # 転置インデックス: bigram → 動画インデックスのリスト
    inverted: dict[str, list[int]] = {}
    for idx, (video, text) in enumerate(zip(videos, video_texts)):
        # タイトルも含めてインデックス化
        combined = video["title"] + " " + text
        for ngram in get_ngrams(combined, n=2):
            if ngram not in inverted:
                inverted[ngram] = []
            inverted[ngram].append(idx)

    VIDEOS_FILE.write_text(json.dumps(videos, ensure_ascii=False), encoding="utf-8")
    NGRAMS_FILE.write_text(json.dumps(inverted, ensure_ascii=False), encoding="utf-8")

    print(f"videos.json : {VIDEOS_FILE.stat().st_size // 1024} KB  ({len(videos)} videos)")
    print(f"ngrams.json : {NGRAMS_FILE.stat().st_size / 1024 / 1024:.1f} MB  ({len(inverted):,} unique bigrams)")

if __name__ == "__main__":
    build_index()
