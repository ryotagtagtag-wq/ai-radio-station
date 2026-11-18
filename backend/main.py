#!/usr/bin/env python3
"""AI パーソナルラジオ局 - 音声・データ生成パイプライン (Phase 1 スケルトン)

Phase 1 ゴール:
  - workflow_dispatch / cron で指定 show_id の番組を生成
  - output/audio/<show_id>/ に MP3 を出力
  - output/feeds/<show_id>.xml に Podcast 互換 RSS を出力
  - output/catalog.json にフロントエンド連携用メタデータを出力

本ファイルは Phase 1 の骨格であり、Gemini / edge-tts / ffmpeg の実際の呼び出しは
スケルトン（ダミー生成）で実装する。後続フェーズで本実装に置き換える。
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

# --- パス定義 ---
ROOT = Path(__file__).resolve().parent.parent
SHOWS_DIR = ROOT / "shows"
DATA_DIR = ROOT / "data"
HISTORY_FILE = DATA_DIR / "history.json"
MEMORY_DIR = DATA_DIR / "memory"
OUTPUT_DIR = ROOT / "output"
AUDIO_DIR = OUTPUT_DIR / "audio"
FEEDS_DIR = OUTPUT_DIR / "feeds"
CATALOG_FILE = OUTPUT_DIR / "catalog.json"

EPISODE_LIMIT = 10  # 番組ごと保持する最新エピソード数


def load_show(show_id: str) -> dict:
    show_file = SHOWS_DIR / f"{show_id}.yaml"
    if not show_file.exists():
        print(f"[ERROR] 番組定義が見つかりません: {show_file}", file=sys.stderr)
        sys.exit(1)
    with open(show_file, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_history() -> list[str]:
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []


def save_history(urls: list[str]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(urls, f, ensure_ascii=False, indent=2)


def load_memory(show_id: str) -> dict:
    mem_file = MEMORY_DIR / f"{show_id}.json"
    if mem_file.exists():
        with open(mem_file, encoding="utf-8") as f:
            return json.load(f)
    return {
        "show_id": show_id,
        "last_broadcast_at": None,
        "last_summary": "",
        "last_talk_topics": [],
        "carryover_topics": [],
        "last_letter_ids": [],
    }


def save_memory(show_id: str, memory: dict) -> None:
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    mem_file = MEMORY_DIR / f"{show_id}.json"
    with open(mem_file, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)


def fetch_rss_dummy(show: dict) -> list[dict]:
    """Phase 1 ダミー: RSS 取得の代わりに固定の記事候補を返す。"""
    return [
        {
            "url": f"https://example.com/article/{i}",
            "title": f"ダミー記事 {i}（{show['title']}）",
            "summary": f"これは {show['title']} 用のダミー記事要約 {i} です。",
            "rss_feed": show["rss_feeds"][0] if show.get("rss_feeds") else "",
        }
        for i in range(1, 4)
    ]


def dedup_articles(articles: list[dict], history: list[str]) -> list[dict]:
    seen = set(history)
    new = [a for a in articles if a["url"] not in seen]
    return new


def generate_script_dummy(show: dict, articles: list[dict], memory: dict) -> dict:
    """Phase 1 ダミー: Gemini Structured Outputs の代わりに固定台本JSONを生成。"""
    now = datetime.now(timezone.utc)
    episode_id = now.strftime("%Y%m%d-%H%M%S") + "-" + show["show_id"]

    lines = []
    p1, p2 = show["personalities"][0]["name"], show["personalities"][1]["name"]

    lines.append({"speaker": p1, "text": f"おはようございます、{p1}です。", "pause_ms": 400})
    lines.append({"speaker": p2, "text": f"そして {p2} です。{show['title']} へようこそ。", "pause_ms": 400})

    for a in articles[:3]:
        lines.append({"speaker": p1, "text": f"まずはこちらのニュースです。{a['title']}", "pause_ms": 300})
        lines.append({"speaker": p2, "text": a["summary"], "pause_ms": 300})

    lines.append({"speaker": p1, "text": "本日はここまで。お便りありがとうございました。", "pause_ms": 500})
    lines.append({"speaker": p2, "text": "また明日お会いしましょう。", "pause_ms": 500})

    return {
        "show_id": show["show_id"],
        "episode_id": episode_id,
        "title": f"{now.strftime('%Y年%m月%d日')} {show['title']}",
        "summary": memory.get("last_summary", "") or f"{show['title']} の本日放送分です。",
        "segments": [
            {
                "id": "opening",
                "name": "オープニング雑談",
                "lines": lines[:2],
            },
            {
                "id": "news",
                "name": "ニュース解説",
                "lines": lines[2:-2],
            },
            {
                "id": "ending",
                "name": "エンディング",
                "lines": lines[-2:],
            },
        ],
        "source_articles": articles,
    }


def generate_dummy_mp3(output_path: Path, duration_sec: int = 10) -> None:
    """Phase 1 ダミー: ffmpeg で無音 MP3 を生成。ffmpeg 未導入時は空ファイルを出力。"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-f", "lavfi",
                "-i", f"anullsrc=r=44100:cl=stereo",
                "-t", str(duration_sec),
                "-q:a", "9",
                str(output_path),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print(f"[OK] ダミーMP3生成: {output_path}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"[WARN] ffmpeg が利用できないため空ファイルを出力: {output_path}")
        output_path.write_bytes(b"")


def write_podcast_feed(show_id: str, episodes: list[dict], base_url: str) -> None:
    """Phase 1: Podcast 互換 RSS (feeds/<show_id>.xml) を出力。"""
    FEEDS_DIR.mkdir(parents=True, exist_ok=True)
    feed_path = FEEDS_DIR / f"{show_id}.xml"

    items_xml = "\n".join(
        f"""  <item>
    <title>{ep['title']}</title>
    <description>{ep.get('summary','')}</description>
    <pubDate>{ep['published_at']}</pubDate>
    <enclosure url="{base_url}{ep['audio_url']}" length="0" type="audio/mpeg"/>
    <guid>{ep['episode_id']}</guid>
  </item>"""
        for ep in episodes
    )

    xml = f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
  <channel>
    <title>{show_id}</title>
    <link>{base_url}</link>
    <description>{show_id} ポッドキャストフィード</description>
    <language>ja-JP</language>
    {items_xml}
  </channel>
</rss>"""
    feed_path.write_text(xml, encoding="utf-8")
    print(f"[OK] Podcast RSS 出力: {feed_path}")


def write_catalog(show_id: str, episodes: list[dict], base_path: str) -> None:
    """Phase 1: catalog.json を出力。"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    catalog = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "base_path": base_path,
        "shows": [
            {
                "show_id": show_id,
                "title": f"{show_id} 番組",
                "description": "Phase 1 スケルトン番組",
                "feed_url": f"{base_path}feeds/{show_id}.xml",
                "episodes": episodes,
            }
        ],
    }
    CATALOG_FILE.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] catalog.json 出力: {CATALOG_FILE}")


def rotate_episodes(show_id: str) -> None:
    """Phase 1: 番組ごと最新 EPISODE_LIMIT 件より古い MP3 を削除。"""
    show_audio_dir = AUDIO_DIR / show_id
    if not show_audio_dir.exists():
        return
    mp3s = sorted(show_audio_dir.glob("*.mp3"), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in mp3s[EPISODE_LIMIT:]:
        old.unlink()
        print(f"[ROTATE] 削除: {old}")


def main() -> None:
    parser = argparse.ArgumentParser(description="AI パーソナルラジオ局 生成パイプライン")
    parser.add_argument("--show-id", required=True, help="生成対象の番組ID (shows/*.yaml のファイル名拡張子抜き)")
    parser.add_argument("--base-path", default="./", help="フロントエンド連携用ベースパス (./ または /<repo>/)")
    args = parser.parse_args()

    show = load_show(args.show_id)
    show_id = show["show_id"]

    history = load_history()
    memory = load_memory(show_id)

    # RSS 取得 + 重複排除
    articles = fetch_rss_dummy(show)
    new_articles = dedup_articles(articles, history)

    # 台本生成（ダミー）
    script = generate_script_dummy(show, new_articles, memory)

    # エピソードID・公開日時
    now = datetime.now(timezone.utc)
    episode_id = script["episode_id"]
    published_at = now.strftime("%a, %d %b %Y %H:%M:%S GMT")

    # MP3 生成（ダミー）
    mp3_filename = f"{episode_id}.mp3"
    mp3_path = AUDIO_DIR / show_id / mp3_filename
    generate_dummy_mp3(mp3_path, duration_sec=10)

    # エピソードレコード
    episode_record = {
        "episode_id": episode_id,
        "title": script["title"],
        "audio_url": f"audio/{show_id}/{mp3_filename}",
        "published_at": published_at,
        "duration_sec": 10,
        "summary": script["summary"],
        "script": script["segments"],
        "source_articles": script["source_articles"],
    }

    # 履歴・記憶更新
    new_urls = history + [a["url"] for a in new_articles]
    save_history(new_urls)

    memory["last_broadcast_at"] = published_at
    memory["last_summary"] = script["summary"]
    save_memory(show_id, memory)

    # catalog.json / feed.xml 出力（現状は単一番組・単一エピソード）
    episodes = [episode_record]
    write_catalog(show_id, episodes, args.base_path)
    write_podcast_feed(show_id, episodes, args.base_path)

    # ローテーション
    rotate_episodes(show_id)

    print(f"[DONE] 番組 {show_id} エピソード {episode_id} を生成しました。")


if __name__ == "__main__":
    main()
