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
  const swUrl = new URL("sw.js", base).href;

  navigator.serviceWorker
    .register(swUrl, { scope: base })
    .then((registration) => {
      console.log("[SW] 登録成功:", registration.scope);
    })
    .catch((err) => {
      console.error("[SW] 登録失敗:", err);
    });
}
