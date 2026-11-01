/* MATCHLAB AZ installable PWA shell. No football/live/API data is cached. */
'use strict';
const CACHE_NAME = 'matchlab-az-shell-v0942';
const SHELL = [
  '/', '/index.html', '/styles.css', '/app.js',
  '/catalog.js', '/featured_media.js', '/coach_tactics.js',
  '/shell.css', '/shell.js', '/install.js', '/manifest.webmanifest',
  '/assets/icon.svg', '/assets/pwa-192.png', '/assets/pwa-512.png',
  '/assets/pwa-512-maskable.png'
];
self.addEventListener('install', event => {
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE_NAME);
    await cache.addAll(SHELL.map(path => new Request(path, { cache: 'reload' })));
    await self.skipWaiting();
  })());
});
self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    const names = await caches.keys();
    await Promise.all(names.filter(name => name.startsWith('matchlab-az-shell-') && name !== CACHE_NAME).map(name => caches.delete(name)));
    await self.clients.claim();
  })());
});
self.addEventListener('fetch', event => {
  const request = event.request;
  if (request.method !== 'GET') return;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;
  // Always ask the backend for live results, scores, profiles and standings.
  // Never present cached football data as current.
  if (url.pathname.startsWith('/api/')) return;
  if (request.mode === 'navigate') {
    event.respondWith((async () => {
      try { return await fetch(request); }
      catch {
        const cache = await caches.open(CACHE_NAME);
        return (await cache.match('/index.html')) ||
          new Response('Offline — MATCHLAB AZ interfeysi mövcud deyil.', { status: 503, headers: {'Content-Type':'text/plain; charset=utf-8'} });
      }
    })());
    return;
  }
  if (!SHELL.includes(url.pathname)) return;
  event.respondWith((async () => {
    const cache = await caches.open(CACHE_NAME);
    return (await cache.match(url.pathname)) || fetch(request);
  })());
});
