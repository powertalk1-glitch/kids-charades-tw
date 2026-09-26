#!/usr/bin/env python3
"""不需第三方套件的專案完整性驗證。"""
from __future__ import annotations

import json
import re
import struct
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "index.html",
    "styles.css",
    "app.js",
    "cards.js",
    "manifest.webmanifest",
    "sw.js",
    "README.md",
    "credits.html",
    "啟動遊戲伺服器.bat",
    "icons/icon-192.png",
    "icons/icon-512.png",
]


def check(condition: bool, message: str, errors: list[str]) -> None:
    if condition:
        print(f"[通過] {message}")
    else:
        print(f"[失敗] {message}")
        errors.append(message)


def png_size(path: Path) -> tuple[int, int] | None:
    try:
        with path.open("rb") as handle:
            header = handle.read(24)
        if header[:8] != b"\x89PNG\r\n\x1a\n" or len(header) < 24:
            return None
        return struct.unpack(">II", header[16:24])
    except OSError:
        return None


def main() -> int:
    errors: list[str] = []
    for relative in REQUIRED:
        check((ROOT / relative).is_file(), f"必要檔案：{relative}", errors)

    if errors:
        print(f"\n驗證中止：缺少 {len(errors)} 個必要檔案。")
        return 1

    manifest = json.loads((ROOT / "manifest.webmanifest").read_text(encoding="utf-8"))
    check(manifest.get("name") == "比手畫腳・家庭同樂版", "manifest 名稱正確", errors)
    check(manifest.get("display") == "standalone", "manifest 可獨立顯示", errors)
    check(manifest.get("orientation") == "any", "manifest 支援直向與橫向", errors)
    icon_sizes = {icon.get("sizes") for icon in manifest.get("icons", [])}
    check({"192x192", "512x512"}.issubset(icon_sizes), "manifest 包含 192 與 512 圖示", errors)
    check(png_size(ROOT / "icons/icon-192.png") == (192, 192), "192 PNG 尺寸正確", errors)
    check(png_size(ROOT / "icons/icon-512.png") == (512, 512), "512 PNG 尺寸正確", errors)

    cards_source = (ROOT / "cards.js").read_text(encoding="utf-8")
    card_pattern = re.compile(
        r'\{\s*"?id"?\s*:\s*"(?P<id>[^"]+)"\s*,\s*'
        r'"?category"?\s*:\s*"(?P<category>[^"]+)"\s*,\s*'
        r'"?answer"?\s*:\s*"(?P<answer>[^"]+)"\s*,\s*'
        r'"?emoji"?\s*:\s*"(?P<emoji>[^"]+)"\s*,\s*'
        r'"?hint"?\s*:\s*"(?P<hint>[^"]+)"'
        r'(?:\s*,\s*"?zhuyin"?\s*:\s*"(?P<zhuyin>[^"]+)")?\s*\}'
    )
    cards = [match.groupdict() for match in card_pattern.finditer(cards_source)]
    ids = [card["id"] for card in cards]
    answers = [card["answer"] for card in cards]
    emojis = [card["emoji"] for card in cards]
    categories = {card["category"] for card in cards}
    expansion_cards = [card for card in cards if card["category"] == "綜合擴充題"]
    check(len(cards) == 328, f"字卡總數恰好 328 張（目前 {len(cards)} 張）", errors)
    check(len(expansion_cards) == 200, f"綜合擴充題恰好 200 張（目前 {len(expansion_cards)} 張）", errors)
    check(
        [card["id"] for card in expansion_cards] == [f"擴充-{number:03d}" for number in range(1, 201)],
        "綜合擴充題 id 完整且連續",
        errors,
    )
    check(len(ids) == len(set(ids)), "字卡 id 全部唯一", errors)
    check(len(answers) == len(set(answers)), "全部 328 張字卡答案皆不重複", errors)
    check(len(categories) == 9, f"恰好 9 個字卡類別（目前 {len(categories)} 個）", errors)
    check(all(card["hint"].strip() and card["emoji"].strip() for card in cards), "每張字卡都有圖片與提示", errors)
    check(all((card["zhuyin"] or "").strip() for card in cards), "每張字卡都有注音", errors)
    expansion_by_answer = {card["answer"]: card for card in expansion_cards}
    reviewed_image_choices = {
        "盪鞦韆": "↔️",
        "司機": "🚘",
        "服務生": "🍽️",
        "燈塔": "💡",
        "毛巾": "🧖",
        "走樓梯": "🚶",
    }
    check(
        all(expansion_by_answer.get(answer, {}).get("emoji") == emoji for answer, emoji in reviewed_image_choices.items()),
        "已修正人工審查發現的六張不符題意圖片",
        errors,
    )

    def openmoji_candidates(emoji: str) -> list[str]:
        codepoints = [f"{ord(character):04X}" for character in emoji]
        candidates = ["-".join(codepoints) + ".png"]
        without_variation = [codepoint for codepoint in codepoints if codepoint != "FE0F"]
        fallback = "-".join(without_variation) + ".png"
        if fallback not in candidates:
            candidates.append(fallback)
        return candidates

    missing_openmoji = [
        emoji for emoji in set(emojis)
        if not any((ROOT / "assets" / "openmoji" / filename).is_file() for filename in openmoji_candidates(emoji))
    ]
    check(not missing_openmoji, f"每種 Emoji 都有本機 OpenMoji 圖片（缺少 {len(missing_openmoji)} 種）", errors)
    check((ROOT / "CREDITS.md").is_file(), "包含 OpenMoji 素材授權與來源說明", errors)
    openmoji_manifest_path = ROOT / "assets" / "openmoji" / "manifest.json"
    openmoji_manifest = json.loads(openmoji_manifest_path.read_text(encoding="utf-8")) if openmoji_manifest_path.is_file() else []
    expected_openmoji = {
        "assets/openmoji/" + next(
            filename for filename in openmoji_candidates(emoji)
            if (ROOT / "assets" / "openmoji" / filename).is_file()
        )
        for emoji in set(emojis)
        if any((ROOT / "assets" / "openmoji" / filename).is_file() for filename in openmoji_candidates(emoji))
    }
    check(set(openmoji_manifest) == expected_openmoji, "OpenMoji 離線素材清單完整且無多餘項目", errors)

    html = (ROOT / "index.html").read_text(encoding="utf-8")
    css = (ROOT / "styles.css").read_text(encoding="utf-8")
    app = (ROOT / "app.js").read_text(encoding="utf-8")
    sw = (ROOT / "sw.js").read_text(encoding="utf-8")
    check("viewport-fit=cover" in html, "設定 viewport-fit=cover", errors)
    check("apple-touch-icon" in html and "apple-mobile-web-app-capable" in html, "包含 Apple PWA 設定", errors)
    check('id="card-image"' in html, "字卡包含圖片顯示元件", errors)
    check('id="zhuyin-toggle"' in html and 'id="zhuyin"' in html, "介面包含注音開關與字卡注音", errors)
    check('href="credits.html"' in html, "遊戲介面提供圖片素材授權入口", errors)
    check("safe-area-inset" in css, "CSS 支援裝置安全區", errors)
    check("min-height: 64px" in css, "觸控元件至少 64px", errors)
    check("prefers-reduced-motion" in css, "支援減少動態效果偏好", errors)
    check("performance.now()" in app and "deadline" in app, "計時採用 performance.now 絕對截止時間", errors)
    check("speechSynthesis" not in app and "speech-toggle" not in html, "已完整移除朗讀功能", errors)
    check('value="0" checked' in html and 'value="60" checked' not in html, "預設時間為無限", errors)
    check("不分類別（綜合）" in app and "ALL_CATEGORIES" in app, "提供不分類別（綜合）選項", errors)
    check("state.category===ALL_CATEGORIES?window.CARDS" in app, "綜合模式會使用全部字卡", errors)
    check("openMojiPath" in app and "card-image" in app, "字卡使用本機 OpenMoji 並保留 Emoji 備援", errors)
    check("imageRequest" in app and "requestToken" in app, "圖片 callback 只處理目前字卡請求", errors)
    check("AudioContext" in app and "pointerdown" in app, "Web Audio 由使用者操作啟用", errors)
    check("localStorage" in app and "try" in app and "catch" in app, "localStorage 具例外保護", errors)
    check("charades-zhuyin" in app and "state.zhuyin" in app, "注音顯示偏好會保存", errors)
    for asset in ["index.html", "styles.css", "cards.js", "app.js", "manifest.webmanifest", "icons/icon-192.png", "icons/icon-512.png"]:
        check(asset in sw, f"離線快取包含 {asset}", errors)
    check("skipWaiting" in sw and "clients.claim" in sw and "CACHE_VERSION" in sw, "Service Worker 支援版本更新", errors)
    check("assets/openmoji/manifest.json" in sw and "openmojiAssets" in sw, "Service Worker 首次載入會快取全部字卡圖片", errors)
    check("credits.html" in sw, "圖片素材授權說明可離線開啟", errors)

    forbidden_terms = ["TO" + "DO", "FIX" + "ME", "place" + "holder"]
    forbidden = re.compile(r"\b(" + "|".join(forbidden_terms) + r")\b", re.IGNORECASE)
    text_extensions = {".html", ".css", ".js", ".json", ".webmanifest", ".md", ".py", ".bat"}
    offenders: list[str] = []
    for path in ROOT.rglob("*"):
        if path.is_file() and ".git" not in path.parts and path.suffix.lower() in text_extensions:
            try:
                if forbidden.search(path.read_text(encoding="utf-8")):
                    offenders.append(str(path.relative_to(ROOT)))
            except UnicodeDecodeError:
                pass
    check(not offenders, f"沒有未完成標記{': ' + ', '.join(offenders) if offenders else ''}", errors)

    if errors:
        print(f"\n共 {len(errors)} 項驗證失敗。")
        return 1
    print(f"\n全部驗證通過：{len(cards)} 張完整字卡，PWA 必要檔案齊全。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
