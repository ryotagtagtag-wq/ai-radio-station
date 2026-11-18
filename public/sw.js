const CACHE_NAME = "ai-radio-cache-v1";
const API_CACHE_NAME = "ai-radio-api-cache-v1";

// 常に最新を取得したいリソースパターン
const NETWORK_FIRST_PATTERNS = ["/catalog.json", ".mp3"];

// インストール時：最小限のプリキャッシュ
self.addEventListener("install", (event) => {
  self.skipWaiting();
});

// アクティベーション時：古いキャッシュを削除
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => key !== CACHE_NAME && key !== API_CACHE_NAME)
          .map((key) => caches.delete(key)),
      ),
    ),
  );
  self.clients.claim();
});

// fetch インターセプト
self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);

  // catalog.json と *.mp3 は NetworkFirst で常に最新を取得
  if (
    NETWORK_FIRST_PATTERNS.some((p) => url.pathname.includes(p)) ||
    url.pathname.endsWith("/catalog.json")
  ) {
    event.respondWith(networkFirst(event.request, API_CACHE_NAME));
    return;
  }

  // その他の静的アセットは CacheFirst（ネットワーク不可時はキャッシュから）
  event.respondWith(cacheFirst(event.request, CACHE_NAME));
});

async function networkFirst(request, cacheName) {
  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (err) {
    const cache = await caches.open(cacheName);
    const cached = await cache.match(request);
    if (cached) return cached;
    throw err;
  }
}

async function cacheFirst(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(request);
  if (cached) return cached;

  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (err) {
    return new Response("オフラインです", { status: 503, statusText: "オフライン" });
  }
}
