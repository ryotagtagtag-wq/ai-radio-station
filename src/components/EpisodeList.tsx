import React from "react";
import { Episode, Show } from "@/lib/api";

interface EpisodeListProps {
  show: Show | null;
  activeEpisodeId: string | null;
  onEpisodeSelect: (episodeId: string) => void;
}

export function EpisodeList({
  show,
  activeEpisodeId,
  onEpisodeSelect,
}: EpisodeListProps) {
  if (!show) return null;

  const episodes = [...show.episodes].reverse(); // 最新が上

  return (
    <div className="space-y-2">
      {episodes.map((ep) => (
        <button
          key={ep.episode_id}
          onClick={() => onEpisodeSelect(ep.episode_id)}
          className={`w-full flex justify-between items-start p-3 rounded-lg border transition ${
            activeEpisodeId === ep.episode_id
              ? "bg-blue-50 border-blue-200"
              : "bg-white border-gray-200 hover:bg-gray-50"
          }`}
        >
          <div>
            <div className="font-semibold text-gray-900">{ep.title}</div>
            <div className="text-xs text-gray-500">
              {new Date(ep.published_at).toLocaleString("ja-JP")}{" "}
              {ep.duration_sec ? `・${Math.floor(ep.duration_sec / 60)}分` : ""}
            </div>
          </div>
          <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
            再生
          </span>
        </button>
      ))}
    </div>
  );
}
