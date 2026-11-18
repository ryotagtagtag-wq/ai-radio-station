/**
 * catalog.json 取得ヘルパー
 * Vite の base (./ または /<repo>/) に合わせて相対パスを解決する。
 */

export const CATALOG_PATH = "./catalog.json";

export async function fetchCatalog(): Promise<CatalogJson> {
  const res = await fetch(CATALOG_PATH, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`catalog.json の取得に失敗しました: ${res.status}`);
  }
  return res.json();
}

export interface SourceArticle {
  url: string;
  title: string;
  rss_feed: string;
}

export interface ScriptLine {
  speaker: string;
  text: string;
  pause_ms?: number;
  sfx?: string;
  voice_override?: string;
}

export interface ScriptSegment {
  id: string;
  name: string;
  lines: ScriptLine[];
}

export interface Episode {
  episode_id: string;
  title: string;
  audio_url: string;
  published_at: string;
  duration_sec?: number;
  summary?: string;
  script?: ScriptSegment[];
  source_articles?: SourceArticle[];
}

export interface Show {
  show_id: string;
  title: string;
  description?: string;
  feed_url: string;
  episodes: Episode[];
}

export interface CatalogJson {
  updated_at: string;
  base_path: string;
  shows: Show[];
  letters?: Array<{ show_id: string; issue_url: string }>;
}

/**
 * GitHub Issue 作成URLを生成する（番組ラベル付き）。
 * VITE_GITHUB_REPO 環境変数 (例: "owner/repo") が必要。
 * 未設定時は空文字を返す（呼び出し側でボタン無効化を判断）。
 */
export function buildIssueUrl(showId: string, episodeTitle?: string): string {
  const repo = import.meta.env.VITE_GITHUB_REPO;
  if (!repo) {
    return "";
  }
  const title = episodeTitle
    ? `お便り: ${episodeTitle}`
    : "お便り";
  const encodedTitle = encodeURIComponent(title);
  const labels = encodeURIComponent(`letter,${showId}`);
  return `https://github.com/${repo}/new?labels=${labels}&title=${encodedTitle}`;
}

export function getRepoInfo(): { owner: string; name: string } | null {
  const repo = import.meta.env.VITE_GITHUB_REPO;
  if (!repo || !repo.includes("/")) {
    return null;
  }
  const [owner, name] = repo.split("/", 2);
  return { owner, name };
}
