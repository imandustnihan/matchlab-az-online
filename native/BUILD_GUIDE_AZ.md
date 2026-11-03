# MATCHLAB AZ — Android Studio və Windows build (v0.9.57)

## 1. Android APK — əvvəlcə bunu hazırla

1. Android Studio-da **Open** seç və repodakı `native/android` qovluğunu aç.
2. Android SDK **Platform 35**, Build Tools **35.0.0** və JDK **17** quraşdırıldığını yoxla.
3. Layihə Gradle **8.9** və Android Gradle Plugin konfiqurasiyasından istifadə edir. Repo hazırda `gradlew` / `gradle-wrapper.jar` saxlamır. Android Studio avtomatik Gradle konfiqurasiyasını qurmasa, **Gradle 8.9** quraşdırıb lokal Gradle ilə build et; mövcud olmayan wrapper-a istinad etmə.
4. **Build → Build APK(s)** seç, yaxud terminalda `gradle :app:assembleDebug` işə sal.
5. Fayl: `native/android/app/build/outputs/apk/debug/app-debug.apk`.
6. Debug APK test üçündür; Play Store və istehsal yayımı üçün ayrıca **imzalanmış release** APK/AAB yaradılmalıdır.

## 2. Windows EXE — APK-dan sonra

1. Windows-da .NET **8 SDK** quraşdır.
2. `native/branding/generate_icons.py` Windows üçün ikona hazırlayır və **Pillow** tələb edir: `python -m pip install pillow`, sonra `python native/branding/generate_icons.py`.
3. Repo kökündən:
   ```powershell
   dotnet publish native/windows-app/MATCHLABAZ.csproj -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true -p:IncludeNativeLibrariesForSelfExtract=true -o native/windows-app/out
   ```
4. Hazır proqram: `native/windows-app/out/MATCHLAB_AZ.exe`.

## GitHub Actions

`.github/workflows/matchlab_build_native.yml` Android APK-nı **əvvəl**, Windows EXE-ni isə Android uğurla bitdikdən **sonra** yaradır. Build artefaktlarının adları `MATCHLAB_AZ_Android_v0957` və `MATCHLAB_AZ_Windows_x64_v0957`-dir.

## Hazır funksiyalar və məhdudiyyətlər

- Android: native Java ekranları, canlı matç API-si, profil, liqa cədvəli, taktika oxları və ehtiyatlar, lokal bildiriş/səs ayarları.
- Windows: native WinForms ekranları, API nəticələri, taktika lövhəsində 11 oyunçu sürükləmə və ad/nömrə dəyişmə, oxlar, 8 formasiya, 7 ehtiyat, saxlanma/sıfırlama/mətn paylaşımı, hadisəyə görə səs seçimləri.
- **Yoxdur:** avtomatik push bildirişləri, təsdiqlənmiş xG/transfer məlumatlarının qlobal təminatı, Windows vibrasiya inteqrasiyası, Android–Windows arasında avtomatik taktika sinxronizasiyası.
- **Vacib:** APK/EXE buildinin uğuru telefonda və kompüterdə bütün davranışların test olunduğu demək deyil.
