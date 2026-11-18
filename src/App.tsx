import { useState, useMemo, useEffect } from "react";
import { useCatalog } from "@/hooks/useCatalog";
import { ShowTabs } from "@/components/ShowTabs";
import { EpisodeList } from "@/components/EpisodeList";
import { Player } from "@/components/Player";
import { Transcript } from "@/components/Transcript";
import { Articles } from "@/components/Articles";
import { LetterButton } from "@/components/LetterButton";
import { Show, Episode } from "@/lib/api";

export default function App() {
  const { catalog, loading, error } = useCatalog();

  const [activeShowId, setActiveShowId] = useState<string | null>(null);
  const [activeEpisodeId, setActiveEpisodeId] = useState<string | null>(null);

  const shows: Show[] = useMemo(() => (catalog ? catalog.shows : []), [catalog]);

  // デフォルトで最初の番組を選択
  useEffect(() => {
    if (shows.length > 0 && !activeShowId) {
      setActiveShowId(shows[0].show_id);
    }
  }, [shows, activeShowId]);

  const activeShow: Show | undefined = useMemo(
    () => shows.find((s) => s.show_id === activeShowId),
    [shows, activeShowId],
  );

  const activeEpisode: Episode | undefined = useMemo(() => {
    if (!activeShow || !activeEpisodeId) return undefined;
    return activeShow.episodes.find((e) => e.episode_id === activeEpisodeId);
  }, [activeShow, activeEpisodeId]);

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center text-gray-500">
        ラジオ局を読み込み中…
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-screen items-center justify-center p-4 text-center text-red-500">
        {error}
      </div>
    );
  }

  if (!activeShow) {
    return (
      <div className="flex h-screen items-center justify-center text-gray-500">
        番組が見つかりません
      </div>
  )}

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900">
      <header className="bg-blue-600 text-white px-6 py-4 shadow-sm">
        <h1 className="text-xl font-bold flex items-center gap-2">
          📻 AI パーソナルラジオ局
        </h1>
        <p className="text-sm text-blue-100 mt-1">
          GitHub Actions で自動生成・GitHub Pages で配信
        </p>
      </header>

      <div className="flex flex-col md:flex-row h-[calc(100vh-72px)] overflow-hidden">
        {/* 左側：番組選択・エピソード一覧 */}
        <aside className="w-full md:w-80 bg-white border-r border-gray-200 overflow-y-auto p-4">
          <div className="mb-6">
            <h2 className="text-sm font-semibold text-gray-700 mb-3 uppercase tracking-wider">
              番組
            </h2>
            <ShowTabs
              shows={shows}
              activeShowId={activeShowId ?? ""}
              onShowSelect={setActiveShowId}
            />
          </div>

          {activeShow && (
            <div>
              <h2 className="text-sm font-semibold text-gray-700 mb-3 uppercase tracking-wider">
                エピソード
              </h2>
              <EpisodeList
                show={activeShow}
                activeEpisodeId={activeEpisodeId}
                onEpisodeSelect={setActiveEpisodeId}
              />
            </div>
          )}
        </aside>

        {/* 右側：プレイヤー・台本・記事・お便り */}
        <main className="flex-1 overflow-y-auto p-6">
          {activeEpisode && (
            <div className="max-w-2xl mx-auto space-y-8">
              <div>
                <h2 className="text-2xl font-bold mb-2">{activeEpisode.title}</h2>
                <p className="text-gray-600">{activeEpisode.summary}</p>
              </div>

              <div className="bg-white rounded-xl shadow p-6 border border-gray-100">
                <h3 className="text-sm font-semibold text-gray-700 mb-4 uppercase tracking-wider">
                  プレイヤー
                </h3>
                <Player
                  episode={{
                    ...activeEpisode,
                    // 相対パスを現在のページURLに対して解決（GitHub Pages サブパス対応）
                    audio_url: new URL(
                      activeEpisode.audio_url,
                      window.location.href,
                    ).href,
                  }}
                  isActive
                />
              </div>

              <div className="bg-white rounded-xl shadow p-6 border border-gray-100">
                <Transcript script={activeEpisode.script} />
              </div>

              <div className="bg-white rounded-xl shadow p-6 border border-gray-100">
                <Articles articles={activeEpisode.source_articles} />
                <div className="mt-6">
                  <LetterButton
                    showId={activeShow.show_id}
                    letters={catalog?.letters ?? []}
                  />
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
