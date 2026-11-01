# MATCHLAB AZ native builds

Actions -> MATCHLAB AZ - Windows EXE and Android APK -> Run workflow.
The Windows EXE embeds index.html, JavaScript, CSS, catalog and tactics module. Live APIs are proxied to the existing Render backend; no fictitious data are created. Windows 10/11 x64 requires Edge or Chrome.
The Android debug APK targets Android 8.0+ (API 26+) and loads the HTTPS hosted service. Debug signing is suitable for testing, not a store release. This is not a standalone offline football database.
Find downloadable EXE and APK in the successful workflow run's Artifacts section. This folder is additive; existing main web hosting remains unchanged.
