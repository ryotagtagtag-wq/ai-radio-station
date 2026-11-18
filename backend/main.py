#!/usr/bin/env python3
"""AI パーソナルラジオ局 - 音声・データ生成パイプライン (Phase 2)

Phase 2 ゴール:
  - 複数 shows/*.yaml 定義に対応
  - cron 複数時間帯で異なる番組を自動生成
  - data/memory による記憶引き継ぎ（carryover_topics をプロンプトに注入）
  - GitHub Issues お便り機能（letter ラベル + show_id ラベル付き Open Issue を取得）
  - お便りコーナーセグメントを台本に追加
  - 生成完了後、対象 Issue へコメント投稿して Close
  - catalog.json に letters 情報を含め、フロントエンドのお便りボタンに連携
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

from letter import fetch_letters, post_comment, close_issue, build_comment_body

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
    """Phase 2 ダミー: RSS 取得の代わりに固定の記事候補を返す。"""
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
    return [a for a in articles if a["url"] not in seen]


def generate_script_dummy(
    show: dict,
    articles: list[dict],
    memory: dict,
    letters: list[dict],
) -> dict:
    """Phase 2 ダミー: Gemini Structured Outputs の代わりに固定台本JSONを生成。

    memory の carryover_topics をオープニングに注入し、
    letters をお便りコーナーセグメントに組み込む。
    """
    now = datetime.now(timezone.utc)
    episode_id = now.strftime("%Y%m%d-%H%M%S") + "-" + show["show_id"]

    p1, p2 = show["personalities"][0]["name"], show["personalities"][1]["name"]

    lines: list[dict] = []

    # --- オープニング雑談（記憶の引き継ぎを注入）---
    carryover = memory.get("carryover_topics", [])
    if carryover:
        topics_text = "、".join(carryover)
        lines.append(
            {
                "speaker": p1,
                "text": f"おはようございます、{p1}です。前回お伝えした「{topics_text}」について、今日は続きをお届けします。",
                "pause_ms": 500,
            }
        )
    else:
        lines.append(
            {"speaker": p1, "text": f"おはようございます、{p1}です。", "pause_ms": 400}
        )
    lines.append(
        {
            "speaker": p2,
            "text": f"そして {p2} です。{show['title']} へようこそ。",
            "pause_ms": 400,
        }
    )

    # --- ニュース解説（掛け合い）---
    for a in articles[:3]:
        lines.append(
            {
                "speaker": p1,
                "text": f"まずはこちらのニュースです。{a['title']}",
                "pause_ms": 300,
            }
        )
        lines.append(
            {"speaker": p2, "text": a["summary"], "pause_ms": 300}
        )

    # --- お便りコーナー ---
    if letters:
        lines.append(
            {"speaker": p2, "text": "それでは、お便りコーナーです。", "pause_ms": 400}
        )
        for letter in letters[:3]:
            issue_number = letter.get("number", "?")
            letter_title = letter.get("title", "(件名なし)")
            lines.append(
                {
                    "speaker": p1,
                    "text": f"Issue #{issue_number} より、{letter_title} というお便りをいただきました。",
                    "pause_ms": 300,
                    "sfx": "letter",
                }
            )
            lines.append(
                {
                    "speaker": p2,
                    "text": "ありがとうございます。さっそくご紹介します。",
                    "pause_ms": 300,
                }
            )
    else:
        lines.append(
            {
                "speaker": p1,
                "text": "本日はお便りはありませんでした。またのお便りをお待ちしています。",
                "pause_ms": 400,
            }
        )

    # --- エンディング ---
    lines.append(
        {"speaker": p1, "text": "本日はここまで。ありがとうございました。", "pause_ms": 500}
    )
    lines.append(
        {"speaker": p2, "text": "また明日お会いしましょう。", "pause_ms": 500}
    )

    return {
        "show_id": show["show_id"],
        "episode_id": episode_id,
        "title": f"{now.strftime('%Y年%m月%d日')} {show['title']}",
        "summary": memory.get("last_summary", "")
        or f"{show['title']} の本日放送分です。",
        "segments": [
            {
                "id": "opening",
                "name": "オープニング雑談",
                "lines": lines[: 2 + (1 if carryover else 0)],
            },
            {
                "id": "news",
                "name": "ニュース解説",
                "lines": lines[2 + (1 if carryover else 0) : -4 if letters else -2],
            },
            {
                "id": "letter_corner",
                "name": "お便りコーナー",
                "lines": (
                    lines[-4:-2] if letters else []
                ),
            },
            {
                "id": "ending",
                "name": "エンディング",
                "lines": lines[-2:],
            },
        ],
        "source_articles": articles,
        "letters": letters,
    }


def generate_dummy_mp3(output_path: Path, duration_sec: int = 10) -> None:
    """Phase 2 ダミー: ffmpeg で無音 MP3 を生成。ffmpeg 未導入時は空ファイルを出力。"""
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
    """Phase 2: Podcast 互換 RSS (feeds/<show_id>.xml) を出力。"""
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


def write_catalog(
    show_id: str,
    show: dict,
    episodes: list[dict],
    base_path: str,
    letters: list[dict],
) -> None:
    """Phase 2: catalog.json を出力。letters 情報を含める。"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 既存の catalog.json を読み込み、他番組の情報を保持する
    catalog: dict = {}
    if CATALOG_FILE.exists():
        try:
            catalog = json.loads(CATALOG_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            catalog = {}

    catalog["updated_at"] = datetime.now(timezone.utc).isoformat()
    catalog["base_path"] = base_path

    # 当番組のエントリを構築（既存の shows から重複排除して上書き）
    existing_shows = catalog.get("shows", [])
    other_shows = [s for s in existing_shows if s.get("show_id") != show_id]

    show_entry = {
        "show_id": show_id,
        "title": show.get("title", show_id),
        "description": show.get("description", ""),
        "feed_url": f"{base_path}feeds/{show_id}.xml",
        "episodes": episodes,
    }
    catalog["shows"] = other_shows + [show_entry]

    # letters 情報（番組ごとのお便り Issue 作成 URL）
    letter_entries = []
    for letter in letters:
        letter_entries.append(
            {
                "show_id": show_id,
                "issue_url": letter.get("html_url", ""),
            }
        )
    if letter_entries:
        catalog["letters"] = letter_entries

    CATALOG_FILE.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[OK] catalog.json 出力: {CATALOG_FILE}")


def rotate_episodes(show_id: str) -> None:
    """Phase 2: 番組ごと最新 EPISODE_LIMIT 件より古い MP3 を削除。"""
    show_audio_dir = AUDIO_DIR / show_id
    if not show_audio_dir.exists():
        return
    mp3s = sorted(
        show_audio_dir.glob("*.mp3"), key=lambda p: p.stat().st_mtime, reverse=True
    )
    for old in mp3s[EPISODE_LIMIT:]:
        old.unlink()
        print(f"[ROTATE] 削除: {old}")


def main() -> None:
    parser = argparse.ArgumentParser(description="AI パーソナルラジオ局 生成パイプライン")
    parser.add_argument(
        "--show-id",
        required=True,
        help="生成対象の番組ID (shows/*.yaml のファイル名拡張子抜き)",
    )
    parser.add_argument(
        "--base-path",
        default="./",
        help="フロントエンド連携用ベースパス (./ または /<repo>/)",
    )
    args = parser.parse_args()

    show = load_show(args.show_id)
    show_id = show["show_id"]

    history = load_history()
    memory = load_memory(show_id)

    # --- お便り取得（GitHub Issues API）---
    token = os.environ.get("GITHUB_TOKEN", "")
    letters: list[dict] = []
    if token:
        try:
            letters = fetch_letters(show_id, token)
            print(f"[INFO] お便り Issue {len(letters)} 件を取得しました（{show_id}）")
        except Exception as exc:
            print(f"[WARN] お便り取得に失敗しました: {exc}", file=sys.stderr)
            letters = []
    else:
        print("[INFO] GITHUB_TOKEN が未設定のためお便り取得をスキップします")

    # --- RSS 取得 + 重複排除 ---
    articles = fetch_rss_dummy(show)
    new_articles = dedup_articles(articles, history)

    # --- 台本生成（memory の carryover_topics と letters を注入）---
    script = generate_script_dummy(show, new_articles, memory, letters)

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

    # --- 履歴・記憶更新 ---
    new_urls = history + [a["url"] for a in new_articles]
    save_history(new_urls)

    # carryover_topics の更新（今回のニュースタイトルを次回へ持ち越し）
    next_carryover = [a["title"] for a in new_articles[:2]]
    memory["last_broadcast_at"] = published_at
    memory["last_summary"] = script["summary"]
    memory["last_talk_topics"] = next_carryover
    memory["carryover_topics"] = next_carryover
    # 処理済みお便りIDを記録
    processed_letter_ids = [l.get("number") for l in letters if l.get("number")]
    memory["last_letter_ids"] = processed_letter_ids
    save_memory(show_id, memory)

    # --- catalog.json / feed.xml 出力 ---
    episodes = [episode_record]
    write_catalog(show_id, show, episodes, args.base_path, letters)
    write_podcast_feed(show_id, episodes, args.base_path)

    # --- お便り Issue へコメント投稿・Close ---
    if token and letters:
        for letter in letters:
            issue_number = letter.get("number")
            if not issue_number:
                continue
            try:
                body = build_comment_body(
                    show_id, episode_id, script["title"]
                )
                post_comment(issue_number, body, token)
                close_issue(issue_number, token)
                print(f"[INFO] Issue #{issue_number} にコメント投稿・Close 完了")
            except Exception as exc:
                print(
                    f"[WARN] Issue #{issue_number} のフィードバックに失敗: {exc}",
                    file=sys.stderr,
                )

    # ローテーション
    rotate_episodes(show_id)

    print(f"[DONE] 番組 {show_id} エピソード {episode_id} を生成しました。")


if __name__ == "__main__":
    main()
