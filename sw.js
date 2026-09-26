const CACHE_VERSION = "charades-pwa-2026-09-26-v8";
const APP_SHELL = [
  "./",
  "./index.html",
  "./styles.css",
  "./cards.js",
  "./app.js",
  "./credits.html",
  "./CREDITS.md",
  "./manifest.webmanifest",
  "./icons/icon-192.png",
  "./icons/icon-512.png",
  "./icons/apple-touch-icon.png"
];

async function cacheAppShellAndCards() {
  const cache = await caches.open(CACHE_VERSION);
  await cache.addAll(APP_SHELL);
  const response = await fetch("./assets/openmoji/manifest.json");
  if (!response.ok) throw new Error("OpenMoji manifest unavailable");
  await cache.put("./assets/openmoji/manifest.json", response.clone());
  const openmojiAssets = await response.json();
  await cache.addAll(openmojiAssets.map((asset) => `./${asset}`));
}

self.addEventListener("install", (event) => {
  event.waitUntil(cacheAppShellAndCards().then(() => self.skipWaiting()));
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((key) => key !== CACHE_VERSION).map((key) => caches.delete(key))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("message", (event) => {
  if (event.data?.type === "SKIP_WAITING") self.skipWaiting();
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;
  const requestUrl = new URL(event.request.url);
  if (requestUrl.origin !== self.location.origin) return;

  if (event.request.mode === "navigate") {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          if (response.ok) caches.open(CACHE_VERSION).then((cache) => cache.put("./index.html", response.clone()));
          return response;
        })
        .catch(() => caches.match("./index.html"))
    );
    return;
  }

  event.respondWith(
    caches.match(event.request).then((cached) => {
      const update = fetch(event.request).then((response) => {
        if (response.ok) caches.open(CACHE_VERSION).then((cache) => cache.put(event.request, response.clone()));
        return response;
      }).catch(() => cached);
      return cached || update;
    })
  );
});
