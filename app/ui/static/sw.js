// Service Worker (E23-2): macht die UI installierbar.
//
// Strategie bewusst schlank: statische Assets cache-first (mit Refresh im
// Hintergrund), alles andere (HTML/API) geht immer ans Netz — die UI ist
// server-gerendert und ohne Server nicht sinnvoll nutzbar. Offline-Queue
// fuer Captures ist E23-3.

const CACHE_NAME = "seiton-static-v1";
const STATIC_PREFIX = "/ui/static/";

self.addEventListener("install", (event) => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))
      )
    ).then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  const isStatic =
    event.request.method === "GET" &&
    url.origin === self.location.origin &&
    url.pathname.startsWith(STATIC_PREFIX);

  if (!isStatic) {
    return; // Netz wie gehabt — nichts cachen (Auth! private Daten!).
  }

  event.respondWith(
    caches.open(CACHE_NAME).then(async (cache) => {
      const cached = await cache.match(event.request);
      const refresh = fetch(event.request)
        .then((response) => {
          if (response.ok) {
            cache.put(event.request, response.clone());
          }
          return response;
        })
        .catch(() => cached);
      return cached || refresh;
    })
  );
});
