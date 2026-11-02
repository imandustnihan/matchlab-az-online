# CLAUDE — MATCHLAB AZ: full context and work request

I am transferring MATCHLAB AZ to you. Read `README_FIRST_AZ.md` and all relevant source files in this ZIP first. The official GitHub repository is `https://github.com/imandustnihan/matchlab-az-online`; do NOT assume that local v0.9.50 changes are already pushed there. Compare code before editing.

## What I want delivered
Build a professional native Windows and native Android football-analysis application that feels as polished and complete as the provided HTML/PWA source, but does **not** use an embedded browser/WebView on either platform. Improve functionality and design without copying SofaScore/Flashscore/LiveScore intellectual property.

Windows starting point: `01_WINDOWS_NATIVE_GO_v0950_SOURCE/main.go` (Go direct Win32, standalone x64 EXE). Companion installer source `02_WINDOWS_SETUP_v0950_SOURCE/main.go`. Maintain splash + full-screen start and add reliable F11/Esc. Use user screenshots as evidence of problems. Fix connection state, hangs, freezes, standings lag, clipped text and blank areas. On Render Free, server cold starts cannot be entirely fixed client-side; implement non-blocking warmup, precise status, backoff and retries. Never fabricate match data.

Android starting point: `05_ANDROID_NATIVE_JAVA_v0946/` native Java only, splash animation and immersive fullscreen, navigation/insets fixed, actual stable APK. Older HTML PWA `03_HTML_PWA_v0942/` is a DESIGN + FEATURE reference, not a target runtime.

Server starting point: inspect actual GitHub current backend. This handoff contains a version 0.9.27 Python backend snapshot without large SQLite. Test `/healthz`, `/api/status`, `/api/live`, `/api/standings`, `/api/search` and explain upstream source coverage and licensing. Do not change production service or paid Render plan without my approval.

Store distribution: Microsoft Store MSIX packaging with actual Partner Center identity, valid logos and app manifests. SmartScreen warning of unsigned standalone EXE must not be bypassed; provide signing / reputation process, don't claim it is removed. Use `07_STORE_MSIX_KIT_V0949_LEGACY/` only as a preliminary template, not production Store package.

Installation: I want a directly downloadable Windows Setup.exe with Desktop/Start shortcuts, Installed Apps entry and uninstall; no CMD, SDK, ZIP extraction or manual compilation. Android: directly downloadable APK; validate on emulator and explain real-device test limitations.

Deliver in stages with concrete changed files and proof of tests: (1) connectivity and responsiveness; (2) smooth standings and full GUI UX; (3) data/API; (4) tactics/lineups/profiles; (5) Windows setup, Android APK and Microsoft Store readiness. Preserve existing features, data and favorites. Work on a new GitHub branch, never merge to main without permission.

The user has had repeated failed or unusable files and expects real tested deliverables, not assertions. Distinguish source build vs compiled EXE, format validation vs Windows execution, simulator smoke vs physical device QA, and MSIX packaging vs Microsoft Store certification. If a tool cannot do a task, report the block and offer real downloadable artifacts or reproducible build instructions.