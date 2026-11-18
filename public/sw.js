// Service Worker for AI Radio Station PWA
// Phase 0: Basic cache for offline playback

const CACHE_NAME = 'ai-radio-v1';
const ASSETS = [
  './index.html',
  './manifest.json',
  './css/style.css',
  './js/app.js',
  './js/player.js',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS))
  );
});

self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => {
      if (response) {
        return response;
      }
      return fetch(event.request);
    })
  );
});
