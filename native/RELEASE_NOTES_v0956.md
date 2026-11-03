# MATCHLAB AZ v0.9.56 — Windows + Android

## Yeniliklər
- Windows ana səhifəsində “Bu gün futbol” başlığı qırpılmır: düzəldilmiş ölçülər, daha geniş mətn sahəsi, orijinal yaşıl **M** loqosu
- Tarixi futbol arxivi **bir mövsümü bir dəfə** yükləyir və yerli yaddaşda saxlayır; sonrakı komanda axtarışları hər dəfə serveri gözləmir
- Windows və Android Taktika Studiyasında **Geri al (Undo)** və **Güzgü (Mirror)** əmrləri, mövcud düzülüş, oyunçu adlandırma, hərəkət oxları saxlanılır
- Windows tənzimləmələrində açılış ölçüsü, yığcam matç kartları, matç və tarixi arxiv keşinin təhlükəsiz silinməsi
- Android tənzimləmələrində avtoyeniləmə, yoxlama intervalı, yığcam kartlar və keşin silinməsi
- Windows və Android versiyaları eyni v0.9.56 buraxılışında hazırlanır

## Yükləmələr
- `MATCHLAB_AZ_Setup_0.9.56_x64.exe` — Windows quraşdırıcı
- `MATCHLAB_AZ_Portable_0.9.56_x64.exe` — Windows portable
- `MATCHLAB_AZ_Android_0.9.56.apk` — Android APK, adındakı TEST çıxarıldı
- `SHA256SUMS.txt` — fayl hash yoxlaması

**Android imzalama barədə vacib:** “TEST” sözü fayl adından çıxarılsa da bu APK indiki CI-də `assembleDebug` ilə hazırlanır, **debug imzalı inkişaf paketidir**, Play Store üçün production release deyil. Mövcud APK-dan imza fərqi varsa, yeniləmək mümkün olmaya bilər. Mağaza və stabil avtomatik yeniləmələr üçün ayrıca release imzası/keystore tələb olunur.

## Server etibarlılığı
Enzonic serveri növbədədir, Render HTTPS əsas server olaraq qalır. Yeni `/api/history-bundle` endpoint-i serverdə yerləşdirilənədək sürətli yeni arxiv axını aktiv olmaya bilər. Əvvəlki tarixi mövsüm keşləri məlumat itkisindən qorunur. Mövsümlər yalnız OpenFootball CC0 tərəfindən təqdim olunan arxivdir; canlı nəticələr deyil.

**Məlumat məhdudiyyəti:** avtomatik dəyişiklik yoxlaması yalnız mənbə ilə təsdiqlənmiş, əvvəllər baxılan QID profillərinə tətbiq olunur; 506207 şəxsin hamısının real vaxt yenilənməsi və hər transferin təsdiqi zəmanətli deyil. Macəra deyil, təsdiqlənmiş məlumat göstərilir.

Windows EXE kod imzası yoxdur və SmartScreen xəbərdarlığı ola bilər. Real cihazda UI yoxlaması CI kompilyasiyasından ayrıdır.
