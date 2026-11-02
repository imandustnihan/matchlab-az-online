# MATCHLAB AZ 0.9.48 — Android and Windows Native
The Android APK and Windows EXE use independent native components; neither uses WebView.

### Main improvement
- Automatic competition-grouped matches, date controls, live/all/favorites
- Azerbaijani Premier League support using TheSportsDB league id 4693 when the new backend branch is deployed
- More leagues, but the API can be incomplete; no invented scores
- Improved search examples, categories and results
- Native tactical editor with drag-to-move, player labels and persistent saved plans
- Windows Inno Setup installer creates desktop and Start shortcuts, supports uninstall

GitHub Actions:
- Android: `.github/workflows/android_studio_export.yml`
- Windows: `.github/workflows/native_windows_v0948.yml`

All code changes remain on `feat/unified-live-leagues-tactics-v0948`. The deployment of the Python server is independent and requires deliberate update. Real end-to-end scores for Azerbaijan are not confirmed until new backend deploy.
