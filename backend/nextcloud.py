#!/usr/bin/env python3
"""AI パーソナルラジオ局 - Nextcloud Talk通知モジュール (Phase 4)

環境変数が設定されている場合、Nextcloud Talkのルームへ
番組タイトル・要約・PWAページURLをMarkdown形式で投稿する。

対応する認証方式:
  1. Bot Webhook (HMAC-SHA256署名方式)
     - NEXTCLOUD_TALK_WEBHOOK_URL: Webhook エンドポイントURL
     - NEXTCLOUD_TALK_BOT_SECRET: HMAC-SHA256 署名用シークレット
  2. OCS API (アプリパスワード方式)
     - NEXTCLOUD_URL: Nextcloud ベースURL (例: https://cloud.example.com)
     - NEXTCLOUD_TALK_TOKEN: アプリパスワードまたは Bearer トークン
     - NEXTCLOUD_TALK_ROOM_ID: 通知先トークルームID
     - NEXTCLOUD_BOT_SECRET: OCS リクエスト署名用（オプション）

どちらか一方が設定されていれば通知を実行する。
両方未設定の場合は通知をスキップ（エラーにしない）。
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from typing import Any


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


def _is_configured() -> bool:
    """いずれかの通知方式が設定されているかを判定。"""
    webhook_url = _env("NEXTCLOUD_TALK_WEBHOOK_URL")
    nextcloud_url = _env("NEXTCLOUD_URL")
    talk_token = _env("NEXTCLOUD_TALK_TOKEN")
    return bool(webhook_url or (nextcloud_url and talk_token))


def _build_markdown(
    show_id: str,
    show_title: str,
    episode_title: str,
    summary: str,
    pwa_url: str,
    audio_url: str,
) -> str:
    """通知用Markdown本文を生成する。"""
    return (
        f"📻 **新エピソード公開: {show_title}**\n\n"
        f"• **エピソード**: {episode_title}\n"
        f"• **番組ID**: `{show_id}`\n"
        f"• **要約**: {summary}\n\n"
        f"🔗 [PWAページで聴く]({pwa_url})\n"
        f"🎵 [音声ファイル]({audio_url})\n\n"
        f"---\n"
        f"AI パーソナルラジオ局"
    )


def _send_via_webhook(
    webhook_url: str,
    bot_secret: str,
    markdown: str,
) -> bool:
    """Bot Webhook (HMAC-SHA256署名) で通知を送信する。"""
    import urllib.request

    payload = {
        "text": markdown,
        "format": "markdown",
    }
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    # HMAC-SHA256 署名を生成
    signature = hmac.new(
        bot_secret.encode("utf-8"), body, hashlib.sha256
    ).hexdigest()

    req = urllib.request.Request(
        webhook_url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-Webhook-Signature": f"sha256={signature}",
            "User-Agent": "ai-radio-station-bot",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            if 200 <= resp.status < 300:
                print("[OK] Nextcloud Talk Webhook 通知送信成功")
                return True
            else:
                print(f"[WARN] Webhook 通知失敗: HTTP {resp.status}")
                return False
    except Exception as exc:  # noqa: BLE001
        print(f"[WARN] Webhook 通知に失敗: {exc}")
        return False


def _send_via_ocs(
    nextcloud_url: str,
    talk_token: str,
    room_id: str,
    bot_secret: str,
    markdown: str,
) -> bool:
    """OCS API (アプリパスワード) で通知を送信する。"""
    import urllib.request
    import urllib.error

    # Nextcloud Talk OCS エンドポイント
    # /index.php/apps/spreed/api/v1/rooms/{room_id}/chat
    base = nextcloud_url.rstrip("/")
    api_url = f"{base}/index.php/apps/spreed/api/v1/rooms/{room_id}/chat"

    payload = {
        "message": markdown,
    }
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "ai-radio-station-bot",
    }

    # Bearer トークン認証
    if talk_token:
        headers["Authorization"] = f"Bearer {talk_token}"

    # オプション: HMAC-SHA256 署名ヘッダ
    if bot_secret:
        signature = hmac.new(
            bot_secret.encode("utf-8"), body, hashlib.sha256
        ).hexdigest()
        headers["X-Signature"] = f"sha256={signature}"

    req = urllib.request.Request(
        api_url,
        data=body,
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            if 200 <= resp.status < 300:
                print("[OK] Nextcloud Talk OCS API 通知送信成功")
                return True
            else:
                print(f"[WARN] OCS API 通知失敗: HTTP {resp.status}")
                return False
    except urllib.error.HTTPError as exc:
        print(f"[WARN] OCS API 通知失敗: HTTP {exc.code} {exc.read().decode('utf-8', errors='ignore')[:200]}")
        return False
    except Exception as exc:  # noqa: BLE001
        print(f"[WARN] OCS API 通知に失敗: {exc}")
        return False


def notify(
    show_id: str,
    show_title: str,
    episode_title: str,
    summary: str,
    pwa_url: str,
    audio_url: str,
) -> None:
    """Nextcloud Talk へ通知を送信する。

    設定されていない場合は静かにスキップする（エラーにしない）。
    """
    if not _is_configured():
        print("[INFO] Nextcloud Talk 通知設定が未構成のためスキップ")
        return

    markdown = _build_markdown(
        show_id=show_id,
        show_title=show_title,
        episode_title=episode_title,
        summary=summary,
        pwa_url=pwa_url,
        audio_url=audio_url,
    )

    webhook_url = _env("NEXTCLOUD_TALK_WEBHOOK_URL")
    bot_secret = _env("NEXTCLOUD_BOT_SECRET", "")

    # 方式1: Bot Webhook が優先
    if webhook_url:
        _send_via_webhook(webhook_url, bot_secret, markdown)
        return

    # 方式2: OCS API
    nextcloud_url = _env("NEXTCLOUD_URL")
    talk_token = _env("NEXTCLOUD_TALK_TOKEN")
    room_id = _env("NEXTCLOUD_TALK_ROOM_ID")

    if nextcloud_url and talk_token and room_id:
        _send_via_ocs(nextcloud_url, talk_token, room_id, bot_secret, markdown)
        return

    print("[INFO] 有効な Nextcloud Talk 通知設定が見つかりません")
