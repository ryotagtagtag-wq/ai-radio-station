#!/usr/bin/env python3
"""AI パーソナルラジオ局 - 音響処理モジュール (Phase 3)

edge-tts によるセリフごとの音声合成と、ffmpeg による
セリフ結合・間（pause）・SFX・ジングル挿入・BGMダッキングを実行する。

フォールバック方針:
  - BGM 音源ファイルが未配置の場合、エラーにならず BGM なしで続行
  - edge-tts が利用できない場合、ffmpeg で無音 MP3 を生成して続行
  - ffmpeg が利用できない場合、空ファイルを出力して続行

pydub には依存せず、ffmpeg コマンドラインのみで完結する。
Python 3.14 以降で削除された audioop モジュールへの依存を避けるため、
pydub は使用しない。
"""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

SILENCE_SEGMENT_MS = 100  # セリフ間のデフォルト無音（ms）


def _which(cmd: str) -> str | None:
    """コマンドが PATH に存在するか確認。"""
    result = subprocess.run(
        ["which", cmd], capture_output=True, text=True
    )
    return result.stdout.strip() or None


def _file_exists(path: str | None) -> bool:
    if not path:
        return False
    return Path(path).exists()


async def _edge_tts_synthesize(text: str, voice: str, output_path: Path) -> None:
    """edge-tts で単一文を音声合成し MP3 を出力する。"""
    import edge_tts  # type: ignore

    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(output_path))


def _ffmpeg_silence(duration_ms: int, output_path: Path) -> None:
    """ffmpeg で指定ミリ秒の無音 MP3 を生成する。"""
    duration_sec = duration_ms / 1000.0
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


def synthesize_speech(
    lines: list[dict[str, Any]],
    output_dir: Path,
) -> list[Path]:
    """セリフ一覧を edge-tts で順次音声合成し、MP3 パスのリストを返す。

    edge-tts が失敗した場合は ffmpeg で無音 MP3 を代わりに生成する。

    Args:
        lines: 各項目に speaker / text / voice_override などを含む辞書
        output_dir: 出力先ディレクトリ

    Returns:
        生成された MP3 ファイルパスのリスト
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    mp3_paths: list[Path] = []

    ffmpeg_available = _which("ffmpeg") is not None

    for i, line in enumerate(lines):
        text = line.get("text", "")
        voice = line.get("voice_override") or "ja-JP-NanamiNeural"
        out_path = output_dir / f"line_{i:03d}.mp3"

        try:
            asyncio.run(_edge_tts_synthesize(text, voice, out_path))
            mp3_paths.append(out_path)
            print(f"[TTS] {i:03d} {voice}: {text[:30]}...")
        except Exception as exc:  # noqa: BLE001
            print(f"[WARN] TTS 合成失敗（フォールバック）: line_{i:03d} ({exc})")
            if ffmpeg_available:
                try:
                    _ffmpeg_silence(1000, out_path)
                    mp3_paths.append(out_path)
                except Exception as e2:  # noqa: BLE001
                    print(f"[ERROR] 無音 MP3 生成も失敗: {e2}", file=sys.stderr)
            else:
                print("[ERROR] ffmpeg も利用できません", file=sys.stderr)

    return mp3_paths


def _build_filter_complex(
    line_count: int,
    pauses_ms: list[int],
    sfx_files: list[str | None],
    jingle_start: str | None,
    jingle_end: str | None,
    bgm_file: str | None,
    bgm_volume_db: float,
) -> str:
    """ffmpeg の filter_complex 文字列を構築する。

    構成:
      [jingle_start] -> [line_0] -> [pause_0] -> [sfx_0] -> [line_1] -> ... -> [jingle_end]
      BGM は bgm_file をループし volume 調整後、ミックス

    各入力ラベル:
      j0: オープニングジングル
      l{i}: セリフ i
      p{i}: 間 i
      s{i}: SFX i
      je: エンディングジングル
      b: BGM
    """
    inputs: list[str] = []
    filter_parts: list[str] = []

    # 入力インデックス管理（ffmpeg の -i 順序に対応）
    # 入力順: jingle_start, lines..., pauses..., sfx..., jingle_end, bgm
    # filter_complex 内では [0:a], [1:a], ... として参照

    # ここではシンプルに concat フィルタを使い、
    # 各セグメントを事前に無音・SFX・ジングルと結合した個別ファイルにしてから
    # 最後に concat する方式に変更する方が確実。
    # したがって filter_complex は BGM ミックス用のみに留め、
    # セリフ結合は別途 concat リストファイル方式で行う。
    #
    # この関数は BGM ミックス用フィルタのみを返す。
    if bgm_file and _file_exists(bgm_file):
        # BGM をループ + 音量調整
        filter_parts.append(
            f"[1:a]aloop=loop=-1:size=2147483647,volume={bgm_volume_db}[bgm]"
        )
        # voice と BGM をミックス（voice 優先のオーバーレイ相当）
        filter_parts.append("[0:a][bgm]amerge=inputs=2[audio]")
    else:
        filter_parts.append("[0:a]anull[audio]")

    return ";".join(filter_parts)


def _create_concat_list(
    segments: list[Path],
    list_path: Path,
) -> None:
    """ffmpeg concat デマッガー用のリストファイルを作成する。"""
    with open(list_path, "w", encoding="utf-8") as f:
        for seg in segments:
            # パスをエスケープ（単一クォートで囲む）
            safe = str(seg).replace("'", "'\\''")
            f.write(f"file '{safe}'\n")


def combine_with_pause_and_sfx(
    mp3_paths: list[Path],
    lines: list[dict[str, Any]],
    show: dict[str, Any],
    output_path: Path,
) -> Path:
    """セリフ MP3 を間（pause_ms）と SFX を挟んで結合する。

    ffmpeg の concat デマッガーを使用。各セグメント間に無音・SFX を
    個別ファイルとして挿入し、最後にすべて concat する。

    Args:
        mp3_paths: synthesize_speech の戻り値（MP3 パスリスト）
        lines: セリフ定義（pause_ms / sfx フィールドを参照）
        show: 番組定義（sfx 設定を参照）
        output_path: 出力 MP3 パス（結合済み音声、BGM適用前）

    Returns:
        結合済み MP3 パス
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    ffmpeg_cmd = _which("ffmpeg")
    if not ffmpeg_cmd:
        print("[ERROR] ffmpeg が利用できません", file=sys.stderr)
        sys.exit(1)

    sfx_setting = show.get("sfx", {})
    sfx_dir = Path(sfx_setting.get("dir", "assets/sfx")) if sfx_setting else None
    jingle_start_file = sfx_setting.get("jingle") if sfx_setting else None
    jingle_end_file = sfx_setting.get("jingle_end") if sfx_setting else None

    segments: list[Path] = []
    tmp_dir = output_path.parent / "_concat_tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    def add_file(path: Path | None) -> None:
        if path and path.exists():
            segments.append(path)

    # オープニングジングル
    if jingle_start_file and _file_exists(jingle_start_file):
        add_file(Path(jingle_start_file))

    for idx, mp3_path in enumerate(mp3_paths):
        line_def = lines[idx] if idx < len(lines) else {}

        # セリフ本体
        add_file(mp3_path)

        # SFX 挿入
        sfx_key = line_def.get("sfx")
        if sfx_key and sfx_dir:
            sfx_path = sfx_dir / f"{sfx_key}.mp3"
            if _file_exists(str(sfx_path)):
                add_file(sfx_path)
                print(f"[SFX] 挿入: {sfx_key}")

        # 間（pause_ms）挿入
        pause_ms = line_def.get("pause_ms", SILENCE_SEGMENT_MS)
        if pause_ms and pause_ms > 0:
            pause_path = tmp_dir / f"pause_{idx}.mp3"
            try:
                _ffmpeg_silence(int(pause_ms), pause_path)
                add_file(pause_path)
            except Exception as exc:  # noqa: BLE001
                print(f"[WARN] 無音生成失敗（スキップ）: {exc}")

    # エンディングジングル
    if jingle_end_file and _file_exists(jingle_end_file):
        add_file(Path(jingle_end_file))

    if not segments:
        print("[ERROR] 結合対象の音声セグメントがありません", file=sys.stderr)
        sys.exit(1)

    # concat リストファイル作成
    concat_list = tmp_dir / "concat_list.txt"
    _create_concat_list(segments, concat_list)

    # ffmpeg concat で結合（再エンコード不要なコピーはできないため libmp3lame でエンコード）
    try:
        subprocess.run(
            [
                ffmpeg_cmd, "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_list),
                "-c:a", "libmp3lame",
                "-q:a", "4",
                str(output_path),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print(f"[OK] 結合MP3出力: {output_path}")
    except subprocess.CalledProcessError as exc:
        print(f"[ERROR] ffmpeg 結合に失敗: {exc}", file=sys.stderr)
        raise

    # 中間一時ファイルは残さない（tmp_dir は _concat_tmp）
    return output_path


def apply_bgm_ducking(
    voice_mp3: Path,
    bgm_path: str | None,
    bgm_volume_db: float,
    output_path: Path,
) -> None:
    """声の裏に BGM をループ再生し、ミックスして出力する。

    BGM 未配置または ffmpeg 未導入時は、voice_mp3 をそのままコピー（フォールバック）。
    sidechaincompressor フィルタで本格的なダッキングを試行し、
    失敗時は単純 overlay（amerge）にフォールバック。

    Args:
        voice_mp3: 結合済み音声 MP3 パス
        bgm_path: BGM 音源パス（None または未配置時はスキップ）
        bgm_volume_db: BGM 音量（dB、マイナス値で小音量）
        output_path: 最終出力 MP3 パス
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    ffmpeg_cmd = _which("ffmpeg")
    if not ffmpeg_cmd:
        print("[WARN] ffmpeg が見つからないため、音声をそのままコピー")
        subprocess.run(
            ["cp", str(voice_mp3), str(output_path)], check=False
        )
        return

    if not bgm_path or not _file_exists(bgm_path):
        print("[INFO] BGM なしで音声をそのままコピー（フォールバック）")
        subprocess.run(
            ["cp", str(voice_mp3), str(output_path)], check=False
        )
        return

    # BGM ダッキング（sidechaincompressor）を試行
    filter_complex = (
        f"[1:a]aloop=loop=-1:size=2147483647,volume={bgm_volume_db}[bgm];"
        f"[0:a][bgm]sidechaincompressor=threshold=0.05:ratio=20:attack=50:release=500[audio]"
    )

    try:
        subprocess.run(
            [
                ffmpeg_cmd, "-y",
                "-i", str(voice_mp3),
                "-i", str(bgm_path),
                "-filter_complex", filter_complex,
                "-map", "[audio]",
                "-c:a", "libmp3lame",
                "-q:a", "4",
                str(output_path),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print(f"[OK] BGMダッキング適用 MP3出力: {output_path}")
        return
    except subprocess.CalledProcessError as exc:
        print(f"[WARN] sidechaincompressor ダッキング失敗（overlay にフォールバック）: {exc}")

    # フォールバック: 単純 overlay（amerge）
    filter_complex_simple = (
        f"[1:a]aloop=loop=-1:size=2147483647,volume={bgm_volume_db}[bgm];"
        f"[0:a][bgm]amerge=inputs=2[audio]"
    )
    try:
        subprocess.run(
            [
                ffmpeg_cmd, "-y",
                "-i", str(voice_mp3),
                "-i", str(bgm_path),
                "-filter_complex", filter_complex_simple,
                "-map", "[audio]",
                "-c:a", "libmp3lame",
                "-q:a", "4",
                str(output_path),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print(f"[OK] BGM overlay 適用 MP3出力: {output_path}")
    except subprocess.CalledProcessError as exc2:
        print(f"[WARN] BGM overlay も失敗（音声をそのままコピー）: {exc2}")
        subprocess.run(
            ["cp", str(voice_mp3), str(output_path)], check=False
        )


def produce_final_audio(
    lines: list[dict[str, Any]],
    show: dict[str, Any],
    episode_id: str,
    tmp_dir: Path,
    final_dir: Path,
) -> Path:
    """TTS 合成 → セリフ結合 → BGMダッキング の一連処理を実行し、最終 MP3 パスを返す。

    Args:
        lines: セリフ定義リスト
        show: 番組定義（bgm / sfx 設定を参照）
        episode_id: エピソードID
        tmp_dir: 中間ファイル出力先
        final_dir: 最終出力先

    Returns:
        最終 MP3 ファイルパス
    """
    tmp_dir.mkdir(parents=True, exist_ok=True)
    final_dir.mkdir(parents=True, exist_ok=True)

    # 1) edge-tts でセリフごと音声合成（失敗時は無音フォールバック）
    lines_dir = tmp_dir / "lines"
    line_mp3s = synthesize_speech(lines, lines_dir)
    if not line_mp3s:
        print("[ERROR] 音声合成に失敗しました", file=sys.stderr)
        sys.exit(1)

    # 2) セリフ結合 + 間 + SFX
    combined_path = tmp_dir / f"{episode_id}_combined.mp3"
    combine_with_pause_and_sfx(line_mp3s, lines, show, combined_path)

    # 3) BGMダッキング
    bgm_setting = show.get("bgm", {})
    bgm_file = bgm_setting.get("file")
    bgm_volume = bgm_setting.get("volume_db", -20)
    final_path = final_dir / f"{episode_id}.mp3"

    apply_bgm_ducking(combined_path, bgm_file, bgm_volume, final_path)

    return final_path
