/// <reference types="vite/client" />

/**
 * Service Worker 登録ヘルパー
 * Vite の base (./ または /<repo>/) に合わせて sw.js を登録する。
 */

export function registerSW() {
  if (typeof window === "undefined" || !("serviceWorker" in navigator)) {
    return;
  }

  const base = import.meta.env.BASE_URL || "./";
  // URL コンストラクタは "./" や "/<repo>/" のような相対パスを base URL として
  // 受け付けないため、文字列結合で sw.js へのパスを構築する。
  const normalizedBase = base.replace(/\/+$/, "") + "/";
  const swUrl = normalizedBase + "sw.js";

  navigator.serviceWorker
    .register(swUrl)
    .then((registration) => {
      console.log("[SW] 登録成功:", registration.scope);
    })
    .catch((err) => {
      console.error("[SW] 登録失敗:", err);
    });
}
