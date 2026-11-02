# MATCHLAB AZ Android v0.9.44 — installed app

The APK is a normal Android application, not a browser shortcut. The signed APK is installed through Android's package installer. On successful installation Android registers it in App Drawer and Settings > Apps, with app label MATCHLAB AZ and the generated adaptive icon. Android handles uninstall.

The app opens the same bundled HTML/CSS/JavaScript football interface used in the PWA/Windows EXE. Live API calls still require network access and an available Render backend.

Use the native three-dot top-right menu to: request a home-screen shortcut (Android launcher/user approval required), refresh the interface, open Android App Info for permissions/uninstall, or see app version. Some launchers automatically place installed apps on the home screen; the manual shortcut is optional.

## Signature and updating
The GitHub Actions artifact is a **debug-signed** APK, not a store-ready Google Play release. The standard debug signing key can differ across CI runs. Android requires matching application ID and signing identity to update an installed APK. If you see APP_NOT_INSTALLED or UPDATE_INCOMPATIBLE, do NOT blindly uninstall if you have important favourites/settings; first back up the locally stored data. A stable production signing key must be created securely, stored in GitHub Actions secrets (not in a public repository) and used to sign future APKs. If the user wants seamless future upgrades, configure release signing first.

CI smoke tests install, launch and screenshot the app on an Android 15 emulator, inspect APK label/activity/icon, and verify all HTML assets are packed. Home-screen pin acceptance depends on the launcher and the user; emulator smoke cannot guarantee it works on a Redmi/HyperOS device.
