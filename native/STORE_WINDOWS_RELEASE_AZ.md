# MATCHLAB AZ — Windows quraşdırılması və Microsoft Store hazırlığı

## Yükləmə paketləri

- `MATCHLAB_AZ_Windows_x64_v0953`: birbaşa işləyən, amma quraşdırıcısı olmayan portable EXE
- `MATCHLAB_AZ_Setup_v0953`: normal **offline quraşdırıcı**. Başlat menyusu keçidi, seçimlə masaüstü qısayolu və Windows Settings > Installed apps bölməsindən silinmə dəstəyi var
- Quraşdırıcı yalnız bu proqramı yerləşdirir, əlavə proqram və internetdən komponent yükləmir

Quraşdırıcı `native/installer/MATCHLAB_AZ.iss` faylı ilə Inno Setup 6 istifadə edilərək hazırlanır. GitHub Actions avtomatik olaraq Windows EXE-dən bu setup faylını yaradır.

### Lokal build

1. .NET 8 SDK, Python + Pillow, Inno Setup 6 quraşdır.
2. Repo kökündə:
   ```powershell
   python -m pip install pillow
   python native/branding/generate_icons.py
   dotnet publish native/windows-app/MATCHLABAZ.csproj -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true -p:IncludeNativeLibrariesForSelfExtract=true -o native/windows-app/out
   & "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe" "native/installer/MATCHLAB_AZ.iss"
   ```
3. Hazır setup: `native/windows-app/installer-out/MATCHLAB_AZ_Setup_0.9.53_x64.exe`

### Microsoft Store üçün bu setup hələ göndərilməyə hazır deyil

Microsoft Store Win32 EXE/MSI quraşdırıcısını qəbul edə bilər, **amma** həmin installer və daxilindəki bütün PE faylları etibarlı CA tərəfindən verilmiş sertifikatla rəqəmsal imzalanmalıdır. Ayrıca:
- Yükləmə linki **birbaşa HTTPS** olmalı və konkret versiyaya sabitlənməlidir; sadəcə GitHub Actions artifakt səhifəsi Store təqdimatı üçün uyğun sabit URL deyil
- Tam **offline**, əlavə proqram qurmayan quraşdırıcı tələb olunur
- Store quraşdırması **səssiz rejimdə** mümkün olmalıdır (Inno Setup: `/VERYSILENT /SUPPRESSMSGBOXES /NORESTART`)
- Store adı və marka materialları Partner Center-də saxlanmalıdır
- Ekran görüntüləri, məxfilik sənədi, real cihaz testləri, əlçatanlıq və sertifikasiya yoxlamaları tamamlanmalıdır

**Alternativ:** MSIX ilə Microsoft Store sonrakı mərhələdə Microsoft tərəfindən imzalanır və yeniləmələri idarə edir. MSIX hazırlanması üçün Partner Center şəxsiyyəti, Publisher məlumatları və paket identifikatorları bilinməlidir; bunlar hazırda repoda yoxdur. Ona görə saxta Publisher və imza əlavə edilməyib.

Mənbələr:
- https://learn.microsoft.com/en-us/windows/apps/publish/publish-your-app/msi/app-package-requirements
- https://learn.microsoft.com/en-us/windows/apps/distribute-through-store/how-to-distribute-your-win32-app-through-microsoft-store
- https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/choose-distribution-path

### Funksiya və keyfiyyət məhdudiyyətləri

Açılış animasiyası real serverin hazır olduğunu iddia etmir. Futbol statistikaları açıq API-lərdən gəlir və gecikə bilər. Quraşdırıcının build-inin uğurlu olması Windows 11-də manual klik testi və Microsoft Store sertifikasiyası demək deyil.
