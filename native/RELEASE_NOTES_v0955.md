# MATCHLAB AZ v0.9.55 — Windows & Android Native Premium

## İctimai yükləmələr
- Windows Setup: `MATCHLAB_AZ_Setup_0.9.55_x64.exe`
- Windows Portable: `MATCHLAB_AZ_Portable_0.9.55_x64.exe`
- Android TEST: `MATCHLAB_AZ_Android_0.9.55_TEST.apk`
- SHA256SUMS.txt: bütövlük yoxlaması.

## Əsas yeniliklər
- **Köhnə/orijinal yaşıl M futbol loqosu** Android ekran başlığında da göstərilir; Windows ikon, splash və quraşdırıcıda saxlanılır.
- **Windows maksimum pəncərə** ilə açılır (çərçivəli, bağlama/minimize düymələri qalır).
- **İdarəetmə/səs studiyası**: Windows üçün orijinal sintez olunmuş kateqoriya melodiyaları, səs səviyyəsi, interval, sevimli oyun seçimi.
- **Android səs idarəetməsi**: səs gücü sürüşdürməsi, proqram açıqkən yoxlanılan real qol/final dəyişikliklərində audio uyarı, vibrasiya menyusu və icazəsi silinib.
- **Futbol tarixi**: `/api/history` və `/api/history-leagues` ilə OpenFootball CC0 2010–2026 mövsüm seçimi və müəyyən liqalar; Windows və Android üzərindən liqa, mövsüm və klub axtarışı, səhifələmə.
- Mövcud taktika studiyası, futbolçu/klub arxivi, matç mərkəzi və mənbəli heyətlər qorunur.
- Tarixi məlumatlar **canlı deyil**. Uydurulmuş skor, xG, transfer və statistika yoxdur.

## Məhdudiyyətlər
- Qol səsi yalnız proqram açıq ikən təkrarlanan uğurlu server yoxlamalarında **iki eyni matçın hesab fərqi** görüldükdə verilir; hər hadisəyə sistem push-u verilmir.
- Daha az səslərdən yalnız istifadəçi sınağı mövcuddur: penalti/kart/assist hadisəsi üçün serverdə etibarlı müqayisə mühərriki hələ yoxdur.
- 24/7 canlı məlumat və server mövcudluğu təminatı yoxdur; Enzonic hələ işə salınmayıb, Render HTTPS qalır.
- OpenFootball tarixi arxivi bəzi liqa/mövsümlərdə yoxdur və upstream güncəl olmayan qeydləri ola bilər.
- Futbolçu kimlik bazası 506207 qeyddir; bu **506207 tam idman statistikasına** bərabər deyil.
- Android TEST APK mağaza üçün imzalanmış release deyil. Windows EXE Authenticode sertifikatı ilə imzalanmayıb və Microsoft Store üçün sertifikatlaşdırılmayıb.

Mənbə lisenziyası: [OpenFootball football.json](https://github.com/openfootball/football.json) (CC0), Wikidata CC0, media üçün fərdi Wikimedia Commons lisenziyaları. ESPN qeyri-rəsmi mənbədir; istifadəyə dair məhdudiyyətləri yoxlayın.
