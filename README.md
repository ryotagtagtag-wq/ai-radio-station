# AI パーソナルラジオ局

完全無料・クレジットカード不要で稼働する、AI パーソナルラジオ局システムです。

GitHub Actions（定期実行）＋ GitHub Pages（配信）のみで構成され、常時稼働のサーバーや有料 VPS は不要です。

## 機能一覧

| 項目 | 内容 |
|------|------|
| **複数番組の自動生成** | `shows/*.yaml` で番組ごとにテーマ・パーソナリティ・RSS フィード・BGM などを定義。cron スケジュール（複数時間帯）または手動実行で切り替え可能 |
| **RSS 取得と重複排除** | 対象 RSS から最新記事を取得し、過去放送済み URL（`data/history.json`）を除外 |
| **記憶（コンテキスト引き継ぎ）** | `data/memory/<show_id>.json` に前回要約・雑談トピック・持ち越し話題を保存し、次回台本に注入 |
| **お便り機能** | GitHub Issues（ラベル `letter` + `<show_id>`）をお便りとして取得。生成後に Issue へコメント投稿し自動 Close |
| **構造化台本生成** | オープニング雑談 → ニュース解説 → お便りコーナー → エンディング。各セリフに `speaker` / `text` / `pause_ms` / `sfx` を含む |
| **音声合成・音響処理** | edge-tts（日本語マルチスピーカー）＋ ffmpeg でセリフ結合・間・SFX・ジングル挿入・BGMダッキング。BGM未配置時もフォールバック |
| **Podcast 互換 RSS** | `feeds/<show_id>.xml` を出力。iTunes タグ対応 |
| **Web ラジオ局 PWA** | Vite + React + TypeScript + Tailwind CSS。番組切り替え・オーディオプレイヤー（再生速度・15秒スキップ・再生位置 `localStorage` 保存）・Media Session API（ロック画面・イヤホン制御）・台本表示・紹介記事リンク・お便り投稿ボタン |
| **オフラインキャッシュ** | Service Worker + manifest.json。catalog.json / MP3 は NetworkFirst で常に最新取得 |
| **ストレージローテーション** | 番組ごと最新 10 エピソードより古い MP3 を自動削除 |
| **Nextcloud Talk 通知** | 生成完了時にルームへ Markdown 通知（Bot Webhook HMAC-SHA256 または OCS API アプリパスワード方式）。未設定時はスキップ |
| **マルチ環境対応** | GitHub Pages サブパス（`/<repo>/`）とルートパス（`./`）の両方で動作。Vite `base` で切替 |

## 技術スタック

| 層 | 技術 |
|----|------|
| 実行基盤・ホスティング | GitHub Actions（定期・手動・ビルド）＋ GitHub Pages |
| バックエンド | Python 3.11+ |
| LLM（台本生成） | Google Gemini API（Google AI Studio 無料枠 / `google-genai` SDK） |
| 音声合成（TTS） | `edge-tts`（無料・APIキー不要・日本語マルチスピーカー） |
| 音声処理 | `ffmpeg`（セリフ結合・間・SFX・BGMダッキング） |
| フロントエンド | Vite + React (TypeScript) + Tailwind CSS + PWA（`vite-plugin-pwa` / Service Worker） |
| データ永続化 | リポジトリ内 JSON ファイル（GitHub Actions から自動コミット） |
| 通知連携 | Nextcloud Talk（Bot Webhook または OCS API） |

## ディレクトリ構成

```
ai-radio-station/
├── .github/
│   └── workflows/
│       ├── generate.yml   # 生成パイプライン（cron / workflow_dispatch）
│       └── deploy.yml     # Vite ビルド → GitHub Pages デプロイ
├── shows/
│   ├── morning-show.yaml  # モーニング番組定義
│   └── evening-show.yaml  # イブニング番組定義
├── backend/
│   ├── main.py            # パイプライン統括エントリポイント
│   ├── audio.py           # edge-tts 合成・ffmpeg 音響処理
│   ├── feed.py            # Podcast 互換 RSS 生成
│   ├── letter.py          # GitHub Issues お便り機能
│   ├── nextcloud.py       # Nextcloud Talk 通知
│   └── requirements.txt   # Python 依存パッケージ
├── data/
│   ├── history.json       # 放送済み URL 履歴
│   └── memory/
│       └── <show_id>.json # 番組ごとの記憶
├── output/
│   ├── audio/<show_id>/   # エピソード MP3（ローテーション管理）
│   ├── feeds/<show_id>.xml # Podcast RSS
│   └── catalog.json       # フロントエンド連携用メタデータ
├── src/                   # React フロントエンド
│   ├── App.tsx            # メインページ
│   ├── components/
│   │   ├── Player.tsx     # オーディオプレイヤー
│   │   ├── ShowTabs.tsx   # 番組切り替えタブ
│   │   ├── EpisodeList.tsx# エピソード一覧
│   │   ├── Transcript.tsx # 台本表示
│   │   ├── Articles.tsx   # 紹介記事リンク
│   │   └── LetterButton.tsx# お便り投稿ボタン
│   ├── hooks/
│   │   └── useCatalog.ts  # catalog.json 取得
│   ├── lib/
│   │   ├── api.ts         # API ヘルパー（Issue URL 生成含む）
│   │   └── sw-register.ts # Service Worker 登録
│   ├── main.tsx           # エントリポイント
│   └── index.css          # Tailwind CSS
├── public/
│   ├── manifest.json      # PWA マニフェスト
│   ├── sw.js              # Service Worker
│   ├── favicon.svg        # ファビコン
│   └── robots.txt
├── .env.example           # 環境変数雛形
├── .gitignore             # Git 除外設定
├── package.json           # フロントエンド依存
├── vite.config.ts         # Vite 設定（base 切替対応）
├── tsconfig.json          # TypeScript 設定
└── README.md              # 本ファイル
```

## セットアップ手順

### 1. リポジトリのクローン

```bash
git clone <リポジトリURL>
cd ai-radio-station
```

### 2. 依存パッケージのインストール

#### フロントエンド（Node.js）

```bash
npm install
```

#### バックエンド（Python 3.11+）

```bash
pip install -r backend/requirements.txt
```

`ffmpeg` もインストールが必要です（macOS の場合）：

```bash
brew install ffmpeg
```

### 3. 環境変数の設定

`.env.example` をコピーして `.env` を作成し、必要に応じて値を設定します。

```bash
cp .env.example .env
```

`.env` は `.gitignore` で Git 管理対象外です。GitHub Actions で使用する値は GitHub Secrets に設定してください（後述）。

### 4. GitHub Secrets の設定

リポジトリの **Settings → Secrets and variables → Actions** に以下を追加します。

| シークレット名 | 内容 | 必須 |
|--------------|------|------|
| `NEXTCLOUD_URL` | Nextcloud ベースURL（例: `https://cloud.example.com`） | 任意 |
| `NEXTCLOUD_TALK_TOKEN` | Nextcloud Talk 用アプリパスワードまたは Bearer トークン | 任意 |
| `NEXTCLOUD_TALK_ROOM_ID` | 通知先トークルーム ID | 任意 |
| `NEXTCLOUD_BOT_SECRET` | Webhook / OCS 署名用シークレット | 任意 |
| `NEXTCLOUD_TALK_WEBHOOK_URL` | Bot Webhook エンドポイント URL | 任意 |

Nextcloud Talk 通知を使用しない場合は設定不要です（未設定時は自動スキップ）。

### 5. GitHub Pages の有効化

リポジトリの **Settings → Pages** で以下を設定します。

- **Build and deployment → Source**: GitHub Actions
- デプロイ後、`https://<owner>.github.io/<repo>/` でアクセス可能

## 番組定義の書き方（`shows/*.yaml`）

番組は `shows/<show_id>.yaml` で定義します。ファイル名と `show_id` は一致させてください。

例：`shows/morning-show.yaml`

```yaml
show_id: morning-show
title: モーニングAIラジオ
description: 毎朝のニュースをAIパーソナリティがお届けします。
rss_feeds:
  - https://example.com/rss
personalities:
  - name: アキラ
    voice_id: ja-JP-NanamiNeural
    persona: 元気で明るいニュースキャスター
  - name: ミオ
    voice_id: ja-JP-AoiNeural
    persona: 落ち着いたアナウンサー
talk_ratio: 0.3
bgm:
  file: assets/bgm/lofi.mp3
  volume_db: -20
sfx:
  jingle: assets/sfx/jingle.mp3
schedule:
  cron: "0 7 * * *"
```

| フィールド | 説明 |
|-----------|------|
| `show_id` | 番組一意ID。ファイル名と一致させる |
| `title` | 番組タイトル |
| `description` | 番組紹介文 |
| `rss_feeds` | 取得対象 RSS フィード URL 一覧 |
| `personalities[].name` | パーソナリティ名（2名） |
| `personalities[].voice_id` | edge-tts ボイスID（日本語マルチスピーカー） |
| `personalities[].persona` | 性格・口調の指示 |
| `talk_ratio` | 雑談比率（0.0〜1.0） |
| `bgm.file` | BGM 音源ファイルパス（未配置時フォールバック） |
| `bgm.volume_db` | BGM 音量（dB、マイナス値で小音量） |
| `sfx.jingle` | オープニングジングルパス |
| `schedule.cron` | GitHub Actions cron 式 |

## 運用・スケジュール

### 定期実行（cron）

`.github/workflows/generate.yml` で以下のスケールが設定されています。

- **07:00 UTC**: モーニング番組（`morning-show`）
- **18:00 UTC**: イブニング番組（`evening-show`）

### 手動実行（workflow_dispatch）

GitHub Actions の **Actions → AI Radio Generate → Run workflow** から、生成対象の番組IDとベースパスを指定して手動実行できます。

## PWA の使い方

### ホーム画面追加

ブラウザで PWA ページを開き、「ホーム画面に追加」を実行すると、アプリのように利用できます。

### 主な操作

| 操作 | 説明 |
|------|------|
| 番組切り替え | 上部タブで番組を切り替え |
| 再生・一時停止 | プレイヤーの ▶/⏸ ボタン |
| 15秒スキップ | ⏪ / ⏩ ボタン |
| 再生速度変更 | 0.75× / 1× / 1.25× / 1.5× |
| 再生位置の保存 | ブラウザを閉じても前回の再生位置を保持 |
| ロック画面制御 | Media Session API 対応（スマホのロック画面・イヤホンから操作可能） |
| 台本表示 | 再生中のセリフを文字起こし表示 |
| 紹介記事リンク | 放送されたニュースの元記事へリンク |
| お便り投稿 | 「お便りを送る」ボタンから GitHub Issue 作成ページへ |

## トラブルシューティング

### 音声が再生されない

1. ブラウザのコンソールでエラーを確認
2. MP3 ファイルが `output/audio/<show_id>/` に存在するか確認
3. GitHub Pages サブパスの場合、`catalog.json` の `audio_url` が正しい相対パスか確認

### Nextcloud Talk 通知が送られない

1. GitHub Secrets に `NEXTCLOUD_URL` 等が設定されているか確認
2. Nextcloud 側でアプリパスワードが有効か確認
3. 通知設定が未構成の場合は自動スキップされるため、エラーにはなりません

### お便り Issue が反映されない

1. Issue にラベル `letter` と `<show_id>`（例: `morning-show`）が両方付いているか確認
2. Issue が Open 状態か確認
3. `GITHUB_TOKEN` が GitHub Actions で自動注入されているか確認

### ビルドエラー

1. `npm install` が正常に完了しているか確認
2. `vite.config.ts` の `base` が環境に合っているか確認（`./` または `/<repo>/`）

## 免責事項

- 本システムはデモ用の架空システムであり、実在の企業・サービスとは無関係です。
- 生成される音声・台本は AI による自動生成であり、事実と異なる場合があります。
- Google Gemini API の無料枠には利用制限があります。利用状況に応じて有料プランへの移行を検討してください。

## ライセンス

MIT License
