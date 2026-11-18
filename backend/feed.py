#!/usr/bin/env python3
"""AI パーソナルラジオ局 - Podcast 互換 RSS 生成モジュール (Phase 3)

feedgen を使用して、iTunes / Apple Podcasts 互換の RSS フィードを生成する。
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from feedgen.feed import FeedGenerator

# --- パス定義 ---
ROOT = Path(__file__).resolve().parent.parent
FEEDS_DIR = ROOT / "output" / "feeds"


def write_podcast_feed(
    show_id: str,
    show: dict[str, Any],
    episodes: list[dict[str, Any]],
    base_url: str,
) -> Path:
    """Podcast 互換 RSS (feeds/<show_id>.xml) を出力する。

    Args:
        show_id: 番組ID
        show: 番組定義（title / description 等を参照）
        episodes: エピソードレコードのリスト
        base_url: 音声ファイルのベースURL（GitHub Pages URL 等）

    Returns:
        生成された RSS ファイルパス
    """
    FEEDS_DIR.mkdir(parents=True, exist_ok=True)
    feed_path = FEEDS_DIR / f"{show_id}.xml"

    fg = FeedGenerator()
    fg.load_extension("podcast")
    fg.id(f"https://example.com/ai-radio/{show_id}")
    fg.title(show.get("title", show_id))
    fg.description(show.get("description", ""))
    fg.link(href=base_url, rel="alternate")
    fg.language("ja-JP")
    fg.lastBuildDate(datetime.now(timezone.utc))
    fg.podcast.itunes_author("AI パーソナルラジオ局")
    fg.podcast.itunes_category("ニュース")
    fg.podcast.itunes_explicit("no")

    for ep in episodes:
        fe = fg.add_entry()
        fe.id(ep["episode_id"])
        fe.title(ep["title"])
        fe.description(ep.get("summary", ""))
        fe.pubDate(ep["published_at"])

        audio_url = f"{base_url}{ep['audio_url']}"
        fe.enclosure(audio_url, 0, "audio/mpeg")  # length は 0（未確定のため）
        fe.guid(ep["episode_id"], permalink=False)

        # エピソードの再生時間（秒）を iTunes 形式で追加
        if ep.get("duration_sec"):
            fe.podcast.itunes_duration(int(ep["duration_sec"]))

        fe.podcast.itunes_explicit("no")

    fg.rss_file(str(feed_path), pretty=True)
    print(f"[OK] Podcast RSS 出力: {feed_path}")
    return feed_path
