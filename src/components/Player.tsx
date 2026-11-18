import {
  useEffect,
  useRef,
  useState,
  useCallback,
  ChangeEvent,
} from "react";
import { Episode } from "@/lib/api";

interface PlayerProps {
  episode: Episode | null;
  isActive: boolean;
}

export function Player({ episode, isActive }: PlayerProps) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [speed, setSpeed] = useState(1);

  const positionKey = useRef<string | null>(null);

  // エピソード切り替え時に再生位置キーをリセットし localStorage から復元
  useEffect(() => {
    if (!episode) {
      positionKey.current = null;
      return;
    }
    positionKey.current = `radio-position-${episode.episode_id}`;
    const saved = localStorage.getItem(positionKey.current);
    if (saved && audioRef.current) {
      audioRef.current.currentTime = parseFloat(saved);
      setCurrentTime(parseFloat(saved));
    }
  }, [episode]);

  // 再生位置の localStorage 保存
  const savePosition = useCallback(() => {
    if (!audioRef.current || !positionKey.current) return;
    localStorage.setItem(positionKey.current, String(audioRef.current.currentTime));
  }, [positionKey]);

  // Media Session API（ロック画面・イヤホン制御）
  useEffect(() => {
    if (!("mediaSession" in navigator)) return;

    const mediaSession = navigator.mediaSession;
    mediaSession.metadata = new MediaMetadata({
      title: episode?.title ?? "",
      artist: "AI パーソナルラジオ局",
      album: "ラジオ局",
    });

    mediaSession.setActionHandler("play", () => {
      audioRef.current?.play();
    });
    mediaSession.setActionHandler("pause", () => {
      audioRef.current?.pause();
    });

    return () => {
      mediaSession.setActionHandler("play", null);
      mediaSession.setActionHandler("pause", null);
    };
  }, [episode]);

  // 再生状態の同期
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const handlePlay = () => setIsPlaying(true);
    const handlePause = () => setIsPlaying(false);
    const handleTimeUpdate = () => setCurrentTime(audio.currentTime);
    const handleLoadedMetadata = () => setDuration(audio.duration ?? 0);
    const handleEnded = () => {
      setIsPlaying(false);
      if (positionKey.current) localStorage.removeItem(positionKey.current);
    };

    audio.addEventListener("play", handlePlay);
    audio.addEventListener("pause", handlePause);
    audio.addEventListener("timeupdate", handleTimeUpdate);
    audio.addEventListener("loadedmetadata", handleLoadedMetadata);
    audio.addEventListener("ended", handleEnded);

    return () => {
      audio.removeEventListener("play", handlePlay);
      audio.removeEventListener("pause", handlePause);
      audio.removeEventListener("timeupdate", handleTimeUpdate);
      audio.removeEventListener("loadedmetadata", handleLoadedMetadata);
      audio.removeEventListener("ended", handleEnded);
    };
  }, [episode]);

  const togglePlay = () => {
    if (!audioRef.current) return;
    if (isPlaying) audioRef.current.pause();
    else audioRef.current.play();
  };

  const seek = (delta: number) => {
    if (!audioRef.current) return;
    audioRef.current.currentTime = Math.max(0, audioRef.current.currentTime + delta);
    savePosition();
  };

  if (!episode || !isActive) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-400">
        エピソードを選択してください
      </div>
    );
  }

  const minutes = (s: number) => Math.floor(s / 60);
  const seconds = (s: number) => Math.floor(s % 60)
    .toString()
    .padStart(2, "0");

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-3">
        <button
          onClick={togglePlay}
          className="p-2 bg-blue-600 text-white rounded-full hover:bg-blue-700 disabled:opacity-50"
          disabled={!duration}
        >
          {isPlaying ? "⏸" : "▶"}
        </button>

        <button
          onClick={() => seek(-15)}
          className="p-2 bg-gray-200 rounded-full hover:bg-gray-300 disabled:opacity-50"
          disabled={!duration}
        >
          ⏪ 15秒
        </button>

        <button
          onClick={() => seek(15)}
          className="p-2 bg-gray-200 rounded-full hover:bg-gray-300 disabled:opacity-50"
          disabled={!duration}
        >
          15秒 ⏩
        </button>

        <select
          value={speed}
          onChange={(e: ChangeEvent<HTMLSelectElement>) => {
            const v = parseFloat(e.target.value);
            setSpeed(v);
            if (audioRef.current) audioRef.current.playbackRate = v;
          }}
          className="text-sm bg-gray-100 rounded px-2 py-1"
        >
          <option value="0.75">0.75×</option>
          <option value="1">1×</option>
          <option value="1.25">1.25×</option>
          <option value="1.5">1.5×</option>
        </select>
      </div>

      <div className="relative h-2 bg-gray-200 rounded overflow-hidden group">
        <div
          className="absolute h-full bg-blue-600"
          style={{ width: `${(currentTime / duration) * 100}%` }}
        />
        <input
          type="range"
          min="0"
          max={duration || 1}
          value={currentTime}
          onChange={(e: ChangeEvent<HTMLInputElement>) => {
            const v = parseFloat(e.target.value);
            if (audioRef.current) audioRef.current.currentTime = v;
            setCurrentTime(v);
            savePosition();
          }}
          className="absolute w-full h-full opacity-0 cursor-pointer z-10 accent-blue-600"
        />
      </div>

      <div className="flex justify-between text-sm text-gray-600">
        <span>{minutes(currentTime)}:{seconds(currentTime)}</span>
        <span>{minutes(duration)}:{seconds(duration)}</span>
      </div>

      <audio
        ref={audioRef}
        src={episode.audio_url}
        className="hidden"
        preload="metadata"
      />
    </div>
  );
}
