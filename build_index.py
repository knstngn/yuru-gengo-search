#!/usr/bin/env python3
"""Parse downloaded .vtt subtitle files and build search index JSON."""

import json
import re
from pathlib import Path

SUBTITLES_DIR = Path("subtitles")
OUTPUT_FILE = Path("docs/index.json")

def parse_vtt(filepath: Path) -> list[dict]:
    """Extract cues from a .vtt file. Returns list of {start, end, text}."""
    text = filepath.read_text(encoding="utf-8", errors="ignore")
    cues = []
    # Split on double newline to get cue blocks
    blocks = re.split(r"\n{2,}", text)
    for block in blocks:
        lines = block.strip().splitlines()
        # Find timestamp line
        time_line = None
        for i, line in enumerate(lines):
            if "-->" in line:
                time_line = i
                break
        if time_line is None:
            continue
        ts = lines[time_line]
        match = re.match(r"([\d:\.]+)\s+-->\s+([\d:\.]+)", ts)
        if not match:
            continue
        start = timestamp_to_seconds(match.group(1))
        end = timestamp_to_seconds(match.group(2))
        # Text is everything after the timestamp line, stripping VTT tags
        raw_text = " ".join(lines[time_line + 1:])
        clean_text = re.sub(r"<[^>]+>", "", raw_text).strip()
        if clean_text:
            cues.append({"start": start, "end": end, "text": clean_text})
    return cues

def timestamp_to_seconds(ts: str) -> float:
    parts = ts.replace(",", ".").split(":")
    parts = [float(p) for p in parts]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    return parts[0] * 60 + parts[1]

def seconds_to_hhmmss(s: float) -> str:
    s = int(s)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{sec:02d}"
    return f"{m}:{sec:02d}"

def build_index():
    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    vtt_files = sorted(SUBTITLES_DIR.glob("*.vtt"))
    print(f"Found {len(vtt_files)} subtitle files.")

    records = []
    for vtt_path in vtt_files:
        # Filename: YYYYMMDD_VIDEOID_TITLE.ja.vtt
        # YouTube video IDs are always exactly 11 chars, so parse by position.
        stem = vtt_path.stem  # strips last .vtt
        if stem.endswith(".ja"):
            stem = stem[:-3]
        # stem = "YYYYMMDD_XXXXXXXXXXX_title"  (8 + 1 + 11 + 1 = 21 prefix chars)
        if len(stem) >= 21 and stem[8] == "_" and stem[20] == "_":
            video_id = stem[9:20]
            title = stem[21:]
        else:
            video_id = stem
            title = stem

        cues = parse_vtt(vtt_path)
        # Merge nearby cues into ~30-second chunks for better search snippets
        chunks = merge_cues(cues, window=30)
        for chunk in chunks:
            records.append({
                "id": video_id,
                "title": title,
                "start": chunk["start"],
                "ts": seconds_to_hhmmss(chunk["start"]),
                "text": chunk["text"],
            })
        print(f"  {title}: {len(chunks)} chunks")

    OUTPUT_FILE.write_text(json.dumps(records, ensure_ascii=False, indent=None), encoding="utf-8")
    print(f"\nWrote {len(records)} records to {OUTPUT_FILE}")

def merge_cues(cues: list[dict], window: float = 30) -> list[dict]:
    """Group cues into chunks of ~window seconds."""
    if not cues:
        return []
    chunks = []
    current_start = cues[0]["start"]
    current_texts = []
    for cue in cues:
        if cue["start"] - current_start > window and current_texts:
            chunks.append({"start": current_start, "text": " ".join(current_texts)})
            current_start = cue["start"]
            current_texts = []
        # Avoid duplicate consecutive lines (common in auto-subs)
        if not current_texts or current_texts[-1] != cue["text"]:
            current_texts.append(cue["text"])
    if current_texts:
        chunks.append({"start": current_start, "text": " ".join(current_texts)})
    return chunks

if __name__ == "__main__":
    build_index()
