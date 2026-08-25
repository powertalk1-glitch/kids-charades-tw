#!/usr/bin/env python3
"""將 cards.js 使用到的 Emoji 對應 OpenMoji PNG 同步到本機 PWA。"""
from __future__ import annotations

import io
import json
import re
import shutil
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARDS = ROOT / "cards.js"
OUTPUT = ROOT / "assets" / "openmoji"
DOWNLOAD_URL = "https://github.com/hfg-gmuend/openmoji/releases/latest/download/openmoji-72x72-color.zip"


def codepoints(emoji: str, keep_variation: bool) -> str:
    values = [f"{ord(character):04X}" for character in emoji]
    if not keep_variation:
        values = [value for value in values if value != "FE0F"]
    return "-".join(values)


def main() -> int:
    source = CARDS.read_text(encoding="utf-8")
    emojis = list(dict.fromkeys(re.findall(r'emoji:"([^"]+)"', source)))
    print(f"下載 OpenMoji 素材包，準備同步 {len(emojis)} 種 Emoji……")
    request = urllib.request.Request(DOWNLOAD_URL, headers={"User-Agent": "kids-charades-tw/1.0"})
    with urllib.request.urlopen(request, timeout=120) as response:
        archive = zipfile.ZipFile(io.BytesIO(response.read()))

    names = set(archive.namelist())
    OUTPUT.mkdir(parents=True, exist_ok=True)
    expected: set[str] = set()
    missing: list[str] = []
    for emoji in emojis:
        full = codepoints(emoji, keep_variation=True) + ".png"
        compact = codepoints(emoji, keep_variation=False) + ".png"
        source_name = full if full in names else compact if compact in names else ""
        if not source_name:
            missing.append(emoji)
            continue
        expected.add(compact)
        with archive.open(source_name) as source_file, (OUTPUT / compact).open("wb") as target:
            shutil.copyfileobj(source_file, target)

    for existing in OUTPUT.glob("*.png"):
        if existing.name not in expected:
            existing.unlink()

    manifest = [f"assets/openmoji/{filename}" for filename in sorted(expected)]
    (OUTPUT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"已同步 {len(expected)} 張本機 OpenMoji 圖片。")
    if missing:
        print("找不到對應素材：" + " ".join(missing))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
