(() => {
  'use strict';
  // The real PWA is installed from the HTTPS website. The already packaged
  // Windows/Android hosts do not need browser install prompts or SW registration.
  if (location.hostname === 'matchlab.local') return;
  if (location.protocol !== 'https:' && !['localhost','127.0.0.1'].includes(location.hostname)) return;
  const installButton = document.getElementById('pwa-install');
  if (!installButton) return;
  let pendingPrompt = null;
  const installed = () => window.matchMedia('(display-mode: standalone)').matches
    || Boolean(window.navigator.standalone);
  function hide() { installButton.hidden = true; pendingPrompt = null; }
  if (installed()) hide();
  window.addEventListener('beforeinstallprompt', e => {
    if (installed()) return;
    e.preventDefault(); pendingPrompt = e; installButton.hidden = false;
  });
  installButton.addEventListener('click', async () => {
    if (!pendingPrompt) return;
    const prompt = pendingPrompt;
    pendingPrompt = null;
    installButton.hidden = true;
    try { await prompt.prompt(); await prompt.userChoice; }
    catch { /* Browser may reject or cancel without damaging the app. */ }
  });
  window.addEventListener('appinstalled', hide);
  if ('serviceWorker' in navigator)
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/service-worker.js', {scope:'/'})
        .catch(error => console.warn('MATCHLAB AZ offline-shell registration failed:',error));
    }, {once:true});
})();
