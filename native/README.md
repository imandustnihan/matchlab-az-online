# MATCHLAB AZ Native v0.9.30

This version is a **real application UI**, not a browser wrapper.

- **Windows:** WinForms .NET 8, self-contained x64 single-file publish. Uses HttpClient to fetch the existing JSON endpoints. No WebView, no browser.
- **Android:** Java Activity and native Android widgets, HTTPS HttpURLConnection and a custom native Canvas pitch. No WebView, no browser.
- Matches, standings, search, profiles, favorites, match details, tactics and basic status are provided as native screens.
- Native app screens open immediately; live scores, search and standings depend on the hosted server and third-party sources.
- The server and web application are unchanged. This build does not ship the 506,207-identity SQLite database for offline use.
- Native match alerts and OS push notifications are not implemented in this build. No live-coverage guarantees.
- Android APK is debug-signed for local testing. Not Play Store ready.

## Builds
Go to GitHub Actions -> MATCHLAB AZ - Native Windows and Android -> latest successful run -> Artifacts. Unzip each artifact to get the EXE or APK.
