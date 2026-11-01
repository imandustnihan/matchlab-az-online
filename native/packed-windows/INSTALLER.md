# MATCHLAB AZ v0.9.43 — Windows Desktop Installer

## Installation
The installer sets up the full local HTML desktop window, branded shortcuts, and a normal uninstall option. It creates a Start menu shortcut, an optional (preselected) Desktop shortcut, and a Windows Settings > Apps > Installed Apps entry.

- Per-user destination: %LOCALAPPDATA%\Programs\MATCHLAB AZ
- No administrator access required.
- Uninstall from Settings > Apps > Installed Apps or the generated uninstaller.
- The main app is a WebView2 desktop window containing HTML/CSS/JavaScript files, not a browser tab. Windows Edge WebView2 Runtime must be available.
- Live football data requires the configured HTTPS Render server.

## SmartScreen
The installer is not digitally signed. Windows Defender SmartScreen may show Windows protected your PC. It cannot be legitimately removed by changing filename, packaging, or disabling system security. To reduce warning frequency, a trusted publisher code-signing identity and reputation are required; Microsoft Store publication is another option. Even newly signed files can trigger SmartScreen.

For a SmartScreen-free alternative that does not involve downloading an unsigned EXE, open the existing HTTPS website in Microsoft Edge and use the menu: ... > More tools > Apps > Install this site as an app. Edge creates installed-app entries and shortcuts. Full PWA offline features require deployment of the PWA branch to the website.

## Verification
The CI workflow builds the self-contained Windows EXE, launches its HTML screen, creates this installer using Inno Setup, installs silently in a clean Windows runner session, verifies installed-app registration and both shortcuts, tests embedded HTML assets, and uninstalls.

Windows installer build is unsigned and not a Microsoft Store package.
