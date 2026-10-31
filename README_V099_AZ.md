# MATCHLAB AZ v0.9.9 — pulsuz hibrid yeniləmə

**Məqsəd:** 506 207 futbol qeydi offline qalmaqla, təsdiqlənmiş matç heyətini və statistikanı internet olduqda göstərmək. **Bütün API-lər pulsuzdur; ödənişli məlumat mənbəyi yoxdur.**

## Nə əlavə edildi?

- `/api/match-detail` — sabit, mənbəsi göstərilən format: `events`, `statistics`, `lineup.home`, `lineup.away`.
- ESPN qeyri-rəsmi matç xülasəsi: mənbədə varsa real `formation`, `starter`, `formationPlace`, ehtiyat oyunçu və qol hadisələri. Üçüncü tərəf API olduğu üçün əlçatanlığı zəmanətli deyil.
- TheSportsDB v1 pulsuz API: `lookuplineup`, `lookupeventstats`, `lookuptimeline`. Mənbə tez-tez yalnız ilk beş qeyd qaytardığına görə **tam heyət kimi göstərilmir**.
- OpenLigaDB: matçın dəqiq ID-si ilə vurulmuş qollar, mümkün olduqda qolgətirən adı və dəqiqə.
- Matçın meydan təsviri, mənbədə təsdiqlənmiş formasiya, heyət siyahısı, hadisə axını, statistika cədvəli. Əgər mənbə 11 oyunçu təqdim etmirsə, uydurma rəqəmlər qoyulmur. Tam 11-liyi taktika redaktoruna köçürmə funksiyası əlavə edildi.
- TheSportsDB statusları `1H`, `HT`, `2H`, `FT`, `AET`, `PEN` düzgün canlı/bitmiş kimi təhlil edilir. Tarix UTC olaraq göstərilir.
- Windows EXE-nin daxilində böyük futbol arxivi var; Render-dən asılı olmadan açılır. Android build mənbəyi eyni məlumat formatını dəstəkləyir, lakin **APK real SDK-da və telefonda hələ təsdiqlənməyib**.

## Faylların istifadəsi

1. **Windows:** `MATCHLAB_AZ_WINDOWS_Free_v099.exe` faylını kompüterə köçür və iki dəfə kliklə. İlk işə salma zamanı Windows-un imzalanmamış proqram xəbərdarlığı ola bilər. Proqram yalnız `127.0.0.1` üzərində yerli HTTP server açır; internet olmayanda futbol arxivi qalır.
2. **Onlayn sayt:** `MATCHLAB_AZ_FREE_WEB_v099_PATCH.zip` arxivinin içindəki 6 faylı GitHub layihəsinin kökünə yerləşdir. Dəyişikliklərdən sonra Render yeni commit üçün deploy başladarsa onu yoxla; yoxdursa manuel deploy lazımdır. **Bu addım olmadan onlayn sayt dəyişmir.**
3. **Android APK:** `MATCHLAB_AZ_FREE_HYBRID_v099_KAYNAK.zip` kodunu GitHub layihəsinə yerləşdir. `.github/workflows/build_matchlab.yml` GitHub Actions workflow-u Android APK debug və Windows EXE artifact-lərini yaratmaq üçün nəzərdə tutulub. Öz telefonunda quraşdırma və real canlı məlumatın yoxlaması ayrıca lazımdır.
4. **Futbol bazası:** `world_football.sqlite.gz.part001`–`part016` artıq GitHub-da varsa, onları təkrar yükləmə. APK build zamanı məhz həmin parçaları birləşdirəcək.

## Dəqiqlik və hüquqlar

- Futbol şəxsiyyət indeksi Reep CC0 arxividir; adı olan hər qeyd üçün foto və karyera statistikası təmin olunmur.
- Wikipedia mətnindən istifadə müəllif hüquqlarına və CC BY-SA-nın şərtlərinə tabedir. Wikimedia Commons-dakı hər foto ayrıca lisenziyalıdır. Hazırkı sistem Wikidata identifikatoruna əsasən şəkil axtarır, amma bütün şəkilləri offline yükləmir.
- TheSportsDB v1 pulsuz istifadəsi limitlidir (sənədlərində dəqiqəlik 30 sorğu yazılır), canlı skor xidməti premium məhsuldur. Ekranda yenilənmə hər 25 saniyəyə yoxlansa da, **real mənbədə hər 25 saniyəyə dəyişiklik olacağına zəmanət yoxdur**.
- ESPN API qeyri-rəsmi istifadəyə açıq endpoint-dir; istehsalat istifadəsi və davamlılığı zəmanətli deyil.
- Render Free yuxuya gedə bilər; EXE və offline APK üçün bu maneə yoxdur, canlı məlumat isə internet tələb edir.

## Test sərhədləri

`python test_free_v099.py`, `python test_browser_v099.py`, `cd windows_go && go test ./...` və Java API-stub compile yoxlamaları keçib. Brauzer testləri **mock məlumat** ilə aparılıb, həqiqi cari oyun və Android SDK quraşdırılması sınağı deyil. Windows EXE GNU/Linux mühitində çapraz-kompilyasiya edilib, real Windows 11 istifadəçi cihazında açılışı test edilməyib.

API sənədləri: https://www.thesportsdb.com/documentation ; https://api.openligadb.de ; https://www.mediawiki.org/wiki/Wikimedia_APIs/Content_reuse
