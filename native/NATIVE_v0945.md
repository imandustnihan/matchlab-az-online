# MATCHLAB AZ v0.9.45 — Native Android and Windows

This branch provides two native user interfaces: Android Java Activity and Windows .NET 8 WinForms. **No WebView2, WebView, HTML, PWA or browser app.** The existing Python Render backend is used only as an HTTPS JSON API for public football data.

- Windows starts **maximized** (not exclusive fullscreen, so Windows taskbar and window controls remain accessible), shows a short WinForms launch animation, has native page navigation and installs with Inno Setup as a real Windows app.
- Android shows a short launch overlay with an animated progress bar, has a native branded toolbar with an app menu, native bottom tabs, native search, results, standings, favourites and tactic pitch.
- The native interfaces currently offer fewer features than the earlier web interface. They are independent applications, not the full web UI copied to native controls. Missing stats are not fabricated.
- Both application version indicators are **0.9.45**, although the remote backend continues with its own separate version number.
- GitHub Windows job checks actual navigation, splash, maximized state, installer and uninstall. Android job checks APK content and native screen on an Android 15 emulator.
- The Android APK is debug-signed; upgrades from differently signed packages can fail. Back up saved favourites before removing an old install. A permanent release signing key is needed for seamless upgrades.
- The Windows installer is unsigned; SmartScreen may warn. Do not turn off system protection to work around it.
