// Service worker mínimo: cacheia apenas o "app shell" (HTML/JS/CSS/ícones
// estáticos). Explicitamente NÃO cacheia nada sob /api/* — nem STT, nem TTS,
// nem conversa/correção — para não servir áudio ou respostas obsoletas.

const CACHE_NAME = "lingua-shell-v1";
const SHELL_ASSETS = ["/", "/index.html", "/manifest.json", "/icons/icon.svg"];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(CACHE_NAME)
      .then((cache) => cache.addAll(SHELL_ASSETS))
      .then(() => self.skipWaiting()),
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((chaves) =>
        Promise.all(chaves.filter((chave) => chave !== CACHE_NAME).map((chave) => caches.delete(chave))),
      )
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);

  // Nunca interceptar/cachear chamadas de API (STT, TTS, conversa, etc.).
  if (url.pathname.startsWith("/api/")) {
    return;
  }

  // Apenas GETs do mesmo domínio entram no cache de shell.
  if (event.request.method !== "GET" || url.origin !== self.location.origin) {
    return;
  }

  event.respondWith(
    caches.match(event.request).then((cacheado) => {
      if (cacheado) return cacheado;
      return fetch(event.request)
        .then((resposta) => {
          if (resposta.ok && (resposta.type === "basic" || resposta.type === "default")) {
            const clone = resposta.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
          }
          return resposta;
        })
        .catch(() => caches.match("/index.html"));
    }),
  );
});
