import React from "react";
import { Show } from "@/lib/api";

interface ShowTabsProps {
  shows: Show[];
  activeShowId: string | null;
  onShowSelect: (showId: string) => void;
}

export function ShowTabs({ shows, activeShowId, onShowSelect }: ShowTabsProps) {
  return (
    <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
      {shows.map((show) => (
        <button
          key={show.show_id}
          onClick={() => onShowSelect(show.show_id)}
          className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition ${
            activeShowId === show.show_id
              ? "bg-blue-600 text-white"
              : "bg-gray-100 text-gray-700 hover:bg-gray-200"
          }`}
        >
          {show.title}
        </button>
      ))}
    </div>
  );
}
