# MATCHLAB AZ v0.9.42 — actual HTML app packaged for Windows and Android

These two applications contain **index.html, styles.css, app.js, catalog.js, featured_media.js, coach_tactics.js, icon.svg, shell.css and shell.js** from the repository. They do not open an external browser to show the main interface.

- **Windows:** .NET 8 WinForms + Microsoft Edge WebView2; all HTML assets embedded inside the single-file EXE as .NET resources. A virtual HTTPS origin `https://matchlab.local` is served by the application, and only `/api/...` routes are forwarded to the existing Render backend over HTTPS. Requires WebView2 Runtime on Windows.
- **Android:** Android Java WebView; bundled HTML and scripts in APK assets via Gradle copy. HTTPS virtual origin served from APK. All `/api/...` routes are proxied to the fixed backend; no public CORS or insecure file:// access. Android system bar insets are applied to the root view.
- Full web experience: search, club/player profiles, matches, league tables, comparisons, tactics and preferences. Server-dependent football data still requires an available backend.
- The public Render backend deployment is not changed or automatically updated by this build; its access, uptime and data coverage are independent limits.
- APK is debug-signed; desktop has no code-signing certificate. Do not claim either is store-ready.
- The 506,207-identity database is on the server and is **not embedded** in these two binaries. App size does not indicate available offline data.
- Windows resource test: `MATCHLAB_AZ.exe --self-test` (exit 0 if all bundled web resources are present).
- See GitHub Actions workflow for build output, asset verification and emulator smoke tests.

The full HTML website can also be installed as a standalone PWA using `manifest.webmanifest` and `service-worker.js`. Only the static application shell is cached; API content is never cached or presented as live when offline. On Android, the APK packs the same production HTML and PWA static resources; its WebView does not register another service worker. The Render service must be deployed from this branch or merged after review before PWA install is available at the public website.

## Windows installer v0.9.43
See `native/packed-windows/INSTALLER.md` for installed-app integration, shortcuts, uninstall and SmartScreen limitations.
