# AI ラジオ局システム

共有レンタルサーバー単体で完結する、完全無料・24時間自動の AI ラジオ局システムです。

## 特徴

- **マルチチャンネル**: 3〜5 局の独立チャンネルを、それぞれ異なるテーマ・更新頻度で運用
- **PWA 対応**: スマホ向け UI、ホーム画面追加、オフライン再生対応
- **ポッドキャスト RSS**: 各チャンネルが独立した RSS フィードを持ち、Apple Podcasts / Spotify 等で購読可能
- **無料音声合成**: edge-tts（uv 経由）による高品質な日本語音声合成。API キー不要
- **cron による完全自動化**: エピソード生成・配信を自動実行
- **軽量設計**: PHP + SQLite。重いローカル AI モデルは使用せず、共有サーバーでも安全に動作

## 動作要件

- SSH 接続可能な共有レンタルサーバー
- PHP (7.4+)
- SQLite (PHP 拡張)
- cron
- `curl` または `wget`
- `uv`（`install.sh` がユーザーディレクトリにインストール）

## クイックスタート

```bash
# リポジトリをクローン
git clone https://github.com/ryotagtagtag-wq/ai-radio-station.git
cd ai-radio-station

# インストーラーを実行（uv, Python, edge-tts のインストール、DB 初期化）
bash install.sh

# 設定ファイルをコピーして編集
cp config.example.php config/config.php
# config/config.php を自分の環境に合わせて編集

# cron を設定（例：30 分おき）
crontab -e
# */30 * * * * /path/to/ai-radio-station/cron/station_cron.sh
```

## ディレクトリ構成

```
ai-radio-station/
├── install.sh              # 一括インストーラー（uv, edge-tts, DB 導入）
├── config/config.php       # サイト・チャンネル設定
├── db/station.sqlite       # SQLite データベース（自動生成）
├── public/                 # 公開 HTML, PWA, 音声, RSS
├── lib/                    # PHP ライブラリ
├── cron/                   # cron エントリポイント
├── tmp/                    # 一時ファイルとログ
├── templates/              # 台本テンプレート
├── jingles/                # ジングル MP3 ファイル
└── run_station.php         # メイン実行スクリプト
```

## ライセンス

MIT License
