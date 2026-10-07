/* Lets the app be installed and open without internet.
   The page is always fetched fresh when online (so updates show right away);
   the saved copy is used only when offline. */
var CACHE = 'mytriathlon-v3'; // change this number every time you publish an update
var BASE = self.registration.scope; // e.g. https://ronen1m.github.io/MyTriathlon/
var PAGE = BASE + 'index.html';
var FILES = [BASE, PAGE, BASE + 'manifest.json', BASE + 'icons/icon-192.png'];

self.addEventListener('install', function (e) {
  e.waitUntil(caches.open(CACHE).then(function (c) {
    return Promise.all(FILES.map(function (u) {
      return fetch(new Request(u, {cache: 'reload'})).then(function (r) { if (r.ok) return c.put(u, r); }).catch(function () {});
    }));
  }));
  self.skipWaiting();
});

self.addEventListener('activate', function (e) {
  e.waitUntil(caches.keys().then(function (keys) {
    return Promise.all(keys.filter(function (k) { return k !== CACHE; }).map(function (k) { return caches.delete(k); }));
  }));
  self.clients.claim();
});

self.addEventListener('fetch', function (e) {
  var req = e.request;
  if (req.method !== 'GET') return;
  var u = req.url.split('?')[0];
  var isPage = req.mode === 'navigate' || u === BASE || u === PAGE;
  if (isPage) {
    e.respondWith(fetch(req, {cache: 'no-cache'}).then(function (res) {
      var copy = res.clone();
      caches.open(CACHE).then(function (c) { c.put(PAGE, copy); });
      return res;
    }).catch(function () {
      return caches.match(PAGE).then(function (r) { return r || caches.match(BASE); });
    }));
    return;
  }
  e.respondWith(caches.match(req).then(function (r) {
    return r || fetch(req).then(function (res) {
      if (res.ok) { var copy = res.clone(); caches.open(CACHE).then(function (c) { c.put(req, copy); }); }
      return res;
    });
  }));
});
