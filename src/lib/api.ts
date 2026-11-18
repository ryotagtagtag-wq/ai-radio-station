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
