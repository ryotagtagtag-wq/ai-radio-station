import React from "react";
import { ScriptSegment } from "@/lib/api";

interface TranscriptProps {
  script: ScriptSegment[] | undefined;
}

export function Transcript({ script }: TranscriptProps) {
  if (!script || script.length === 0) {
    return <div className="text-gray-400 text-sm">台本データはありません</div>;
  }

  return (
    <div className="space-y-3">
      {script.map((seg) => (
        <div key={seg.id} className="border-l-2 border-blue-400 pl-3 py-1">
          <div className="text-xs font-semibold text-blue-600 uppercase tracking-wider mb-1">
            {seg.name}
          </div>
          <div className="space-y-1 text-sm text-gray-700">
            {seg.lines.map((line, i) => (
              <div key={i} className="flex gap-2">
                <span className="w-10 text-xs font-bold text-gray-500">{line.speaker}</span>
                <span>{line.text}</span>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
