#!/usr/bin/env python3
"""GitHub Issues お便り機能 (Phase 2)

リポジトリの Issue（ラベル `letter` と `<show_id>` が付いた Open 状態）を
GitHub API で取得し、生成完了後に Issue へコメント投稿して Close する。
"""

from __future__ import annotations

import os
from typing import Any

import requests


def _repo_info() -> tuple[str, str]:
    """GitHub Actions 環境からリポジトリ オーナー名とリポジトリ名を取得。"""
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if "/" not in repo:
        raise ValueError("GITHUB_REPOSITORY 環境変数が設定されていません")
    owner, name = repo.split("/", 1)
    return owner, name


def _api_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "ai-radio-station-bot",
    }


def fetch_letters(show_id: str, token: str) -> list[dict[str, Any]]:
    """ラベル `letter` と `<show_id>` が付いた Open Issue を取得する。

    Returns:
        Issue の一覧。各項目は GitHub API の Issue オブジェクト。
    """
    owner, name = _repo_info()
    # ラベル `letter` と `<show_id>` の両方が付いた Open Issue を検索
    params = {
        "state": "open",
        "labels": f"letter,{show_id}",
        "sort": "created",
        "direction": "asc",
        "per_page": 20,
    }
    url = f"https://api.github.com/repos/{owner}/{name}/issues"
    resp = requests.get(url, headers=_api_headers(token), params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def post_comment(issue_number: int, body: str, token: str) -> None:
    """指定 Issue へコメントを投稿する。"""
    owner, name = _repo_info()
    url = f"https://api.github.com/repos/{owner}/{name}/issues/{issue_number}/comments"
    resp = requests.post(
        url, headers=_api_headers(token), json={"body": body}, timeout=30
    )
    resp.raise_for_status()


def close_issue(issue_number: int, token: str) -> None:
    """指定 Issue を Close する。"""
    owner, name = _repo_info()
    url = f"https://api.github.com/repos/{owner}/{name}/issues/{issue_number}"
    resp = requests.patch(
        url,
        headers=_api_headers(token),
        json={"state": "closed"},
        timeout=30,
    )
    resp.raise_for_status()


def build_comment_body(show_id: str, episode_id: str, episode_title: str) -> str:
    """お便りへの返信コメント本文を生成する。"""
    return (
        f"📻 **お便りをありがとうございました！**\n\n"
        f"本放送（`{episode_id}`: {episode_title}）にて、\n"
        f"お送りいただいたお便りをご紹介させていただきました。\n\n"
        f"---\n"
        f"AI パーソナルラジオ局（{show_id}）"
    )
