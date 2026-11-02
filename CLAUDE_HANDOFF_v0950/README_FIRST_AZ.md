# MATCHLAB AZ — Claude üçün tam təhvil / full developer handoff

**Handoff tarixi:** 2 noyabr 2026. **Ən yeni proqram:** Windows v0.9.50 (Go/Win32). **Ən yeni Android native mənbə:** v0.9.46 (Java). **Sayt/PWA mənbəsi:** v0.9.42, backend snapshot v0.9.27. Bu versiyalar **bir-birinə inteqrasiya edilmiş tək releas deyil**.

## Əsas linklər
- GitHub: https://github.com/imandustnihan/matchlab-az-online
- Son ayrı inkişaf branch: https://github.com/imandustnihan/matchlab-az-online/tree/fix/windows-desktop-installer-v0943
- HTML/PWA branch: https://github.com/imandustnihan/matchlab-az-online/tree/fix/pwa-installable-html-v0942
- Əvvəlki Android/Windows branch: https://github.com/imandustnihan/matchlab-az-online/tree/fix/html-packed-exe-apk-20261102
- İlk native əsas branch: fix/windows-fast-start-and-pitch-20261101 (PR #1 https://github.com/imandustnihan/matchlab-az-online/pull/1)
- Backend: https://matchlab-az-online.onrender.com
- User confirmed: GitHub main branch should NOT be merged without approval. Develop in a new branch.

## Paketin içindəkilər / Which version to start from
1. `01_WINDOWS_NATIVE_GO_v0950_SOURCE/` — **LATEST Windows desktop implementation**, Go + direct Win32/GDI. No WebView, no HTML, no .NET SDK; `main.go`, `go.mod`, `offline-catalog.json`, `icon.ico` and compiled EXE. Original latest build, not changed or recompiled in this handoff.
2. `02_WINDOWS_SETUP_v0950_SOURCE/` — latest Go installer source (`main.go`, `go.mod`), compiled Setup.exe; installers create per-user application, Windows shortcut and uninstall registration. Installer MAY show SmartScreen: unsigned.
3. `03_HTML_PWA_v0942/` — latest local HTML/CSS/JS design and PWA. Use it as a **visual and feature reference**, not as a WebView for the user's native desktop requirement.
4. `04_ORIGINAL_BACKEND_AND_TESTS_v0927/` — server/API Python sources, utilities, docs/tests extracted from older 0.9.27 bundle. **Excludes** the 136 MB SQLite identity database; repository may have newer source. Always inspect GitHub HEAD first.
5. `05_ANDROID_NATIVE_JAVA_v0946/` — **native Java Android**, opening splash / fullscreen / UI and tactical pitch, no HTML WebView. Source-only, not fully device-tested.
6. `06_WINDOWS_CSHARP_V0947_LEGACY/` — Windows Forms prototype; **known v0.9.47 build failure** C# CS1010 etc. Do NOT assume it's valid or replace v0.9.50 with it. Use only design/history if helpful.
7. `07_STORE_MSIX_KIT_V0949_LEGACY/` — MSIX packaging scripts and logos. This is **not** a certified/signed Store submission; manifest identity is not verified against Partner Center.
8. `08_SCREENSHOTS/` — screenshots of failures and older HTML designs.
9. `CLAUDE_TASK_PROMPT.md` — detailed plan to give Claude.
10. `FILE_SHA256.txt` — SHA-256 per packaged file for checking transfer integrity.

## User requirements (high priority)
- Windows: true native standalone desktop application, WITHOUT opening HTML/WebView/browser; polished rich design like the HTML site, but original. Starts fullscreen automatically with logo splash. F11 toggles, Esc exits fullscreen.
- Android: true native Android Java, no WebView. Startup animation and automatic immersive fullscreen; navigation/buttons must not overlap Android system bars. Deploy APK after verifying emulator AND actual phone compatibility.
- UX: professional football home with live/results, leagues, standings, search, profiles, clubs, coach info, lineups, event timelines, realistic tactics. Loading/error/empty states must be distinguishable. NO mock scores/rosters/statistics.
- Performance: standings scroll smooth with 100+ rows; don't block UI thread with network; avoid excessive GDI painting, leaks, unnecessary full refresh; user has observed “not responding” on Windows and severe standings lag.
- Connectivity: Render backend on FREE plan has cold starts; don't claim to eliminate this using client-side timeouts. Show progress/retries without freezing, cache only appropriately timestamped nonlive/static data. Paid always-on hosting or explicitly authorized hosting changes needed for truly fast cold starts.
- Installation: single Windows Setup.exe, user should not manually run .cmd, .NET SDK, Go or unzip source. Desktop and Start shortcuts, Installed Apps registration, clean uninstaller, branded icon. Show version and update behavior clearly.
- Microsoft Store: plan MSIX with proper Partner Center identity, certificate and actual certification. Do not promise unsigned EXE avoids SmartScreen or advise disabling Windows Security. Microsoft Store developer registration may be free, but require verification and compliance.
- Sources: Check license/terms of ESPN, TheSportsDB, Wikipedia, Wikimedia, football-data.org and any other football feed. Never copy proprietary third-party apps' assets or access unlicensed APIs.
- Protect existing data, favorite settings, keys and source files; no deletion/merge to main without user's consent. Prove tests honestly.

## Bugs reported by user
- “Server yoxlanılır”, “Yenidən qoşulma gözlənilir” stays too long, reconnect unreliable; very slow to become active.
- Windows “not responding” dialogue (see `08_SCREENSHOTS/Windows_not_responding.png`).
- Standings stutters/freezes when mouse wheel or touchpad scroll moves up/down. v0.9.49 source attempted clipped visible-row rendering and double buffering; not confirmed on user's PC.
- Early native Windows v0.9.46/v0.9.47 looked worse than HTML website; oversized empty spaces, clipped sidebar branding; owner rejected it.
- Several C# versions failed to compile: duplicate `Card` definition (CS0102), line break in string literal `Program.cs` at lines 343-344 (CS1010/CS1003).
- Earlier APK navbar overlapped system UI; previous attempts fixed inset measurement, but not all phones verified.
- Multiple sandbox download links from ChatGPT showed Turkish “Bu işlem tamamlanamadı”. Provide download source in a reliable, verifiable place (GitHub Releases or Actions artifact) instead of renaming links repeatedly.
- Unsigned EXE triggers Microsoft Defender SmartScreen. Legitimate fix is trusted publisher signing/reputation or appropriate Store package, NOT bypass.

## Technical claims and validation
- Latest Go v0.9.50 EXE and Setup files exist and have Windows x64 PE headers. Their real GUI behavior, shortcut installation, MSIX validation, malware screening, performance and Render connectivity have NOT been tested here on user's Windows PC.
- Android v0.9.42 older HTML/WebView APK was built and emulator smoke-tested; this is NOT the requested true-native Android version.
- Android v0.9.46 native source had static checks only, not complete signed Android APK/device acceptance testing.
- Windows v0.9.43 HTML/WebView installer passed GitHub CI on Windows, but user explicitly rejects HTML wrapper architecture, so **do not take it as final architecture**.
- v0.9.49/v0.9.50 Go use native Windows rendering. `01_WINDOWS_NATIVE_GO_v0950_SOURCE/main.go` is authoritative for latest functionality.
- The original large SQLite identity data is NOT a live statistics dataset; the historical claim of 506,207 records is an identity count, not 506,207 full stats profiles.

## Start here / immediate engineering approach
1. Open `CLAUDE_TASK_PROMPT.md` and inspect v0.9.50 Go source, installer and backend separately. Check network timeout/retry handling, thread ownership, event loop, draw loop and `WM_MOUSEWHEEL` before changing anything.
2. Verify backend health/status and Render deployment using official tools and logs; measure cold and warm latency. If Render free tier is asleep, advise the user of objective limitation rather than masking it.
3. Reproduce freezes in Windows VM with instrumentation. Add repeatable benchmarks for 20, 100, 500 standing rows and repeated page changes (GDI leak test), improve painting and input responsiveness.
4. Produce ONE verifiable code-signed/reputation strategy for Store. Build an unsigned MSIX for submission only after obtaining exact identity values from Partner Center; avoid fake signature or false assurances.
5. Create a tested native Android APK from v0.9.46 source, adding useful app UX while ensuring system bars/accessibility compatibility.
6. Publish tested Windows EXE/installer and APK to GitHub Releases or CI artifacts; link exact built output. Do not merge main without explicit approval.

## Important version provenance
- GitHub branches named v0.9.42/0.9.43 contain HTML embedded WebView variants, NOT the later Go Win32 native v0.9.50 from this package.
- This ZIP preserves multiple attempts for comparison. Choose the current working base deliberately, not by filename alone.