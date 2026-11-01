# MATCHLAB AZ v0.9.18 — Wikipedia karyeraları, vahid şəxs profili, taktika meydançası

## Nə dəyişdi?

- **Təkrar şəxslər:** `identity_unification.py` futbolçu və məşqçi qeydlərini yalnız **eyni təsdiqlənmiş Wikidata QID** olduqda birləşdirir. Sadəcə ad oxşarlığı istifadə olunmur. Reep bazasında 1.625 QID həm futbolçu, həm məşqçi rolunda rast gəlinir. Bu, 1.625 ədəd UI dublikatının hamısının hər axtarışda göstərilməsi demək deyil; kimlik kəsişməsinin sayıdır.
- **Mikel Arteta:** Köhnə `p:mikel-arteta`, `c:mikel-arteta` qeydləri `Q185572` ilə əlaqələndirilib. Reyestrdəki `rc47c64951da111e` şəxs profilinə yönləndirilir. Futbolçu olduğu illər və məşqçilik fəaliyyəti eyni profildədir. Wikipedia bağlantısı müvəqqəti əlçatmaz olduqda, **Wikipedia məqaləsindən yoxlanmış əsas karyera illəri** `verified_profiles.json` içində ehtiyat kimi saxlanır; oyun/qol/asist sayları uydurulmur.
- **Wikipedia genişləndirilməsi:** On-demand `wiki_title` və təsdiqli Wikipedia dilləri 11-ə artırıldı: en, tr, az, es, de, fr, it, pt, ru, nl, pl. Məqalə identikliyi `pageprops.wikibase_item` ilə yoxlanmadan infobox qəbul edilmir. İngilis futbol bio infobox şablonundan senior liqa karyerası alınır; həmin dildə uyğun şablon yoxdursa, artıq mövcud olan Wikidata klub əlaqələri saxlanır. Bütün dillər tam statistik cədvəl vermir.
- **Asistlər:** Wikipedia məqaləsində mənbəli `assistsN` göstəricisi olduqda görünür. Əks halda `Məlumat yoxdur` yazılır; 0 kimi hesablanmır. Bütün futbolçuların tarixən asist göstəricilərinə pulsuz, yekcins, tam mənbə yoxdur.
- **Taktika meydançası:** Başlıq menyusu üçün istifadə edilən `.top` sinfi cərimə meydançasının `.top` sinfi ilə toqquşurdu və tünd düzbucaqlı yaradırdı. Meydançanın xətləri `pitch-north`/`pitch-south` siniflərinə keçirildi. Formasiya yaradıcısı artıq tanınan GK / müdafiə / orta xətt / hücum rol kodlarından istifadə edir. Arteta kimi sənədləşdirilmiş yarımmüdafiəçi seçilmiş mövqe göstərilməmişsə avtomatik qapıçı mövqeyinə düşmür; əl ilə mövqe seçimi üstün sayılır.

## Dəqiqlik və lisenziyalar

Bu versiya 506.207 real futbol kimliyi qeydini dəyişdirmir. QID bağlantısı olmayan bir çox şəxsin tam karyerası və şəkli yoxdur. Məlumatlar mövcud olduqda Wikipedia və Wikidata-dan **profil açıldıqca** soruşulur; bütün ensiklopediyanın və media arxivinin kopyası deyil. Wikipedia məqaləsi və karyera faktları üçün orijinal məqaləyə keçid verilir, şəkillərin fərdi müəlliflik lisenziyası ayrı yoxlanmalıdır. Wikidata struktur faktları CC0, Wikipedia mətnləri müvafiq CC BY-SA şərtlərindədir. Rəsmi canlı skor məlumatlarının mövcudluğu ayrıca xarici mənbələrdən asılıdır.

Mikel Arteta mənbə: https://en.wikipedia.org/wiki/Mikel_Arteta

## GitHub və Render

1. `MATCHLAB_AZ_v0918_GITHUB_RENDER_PATCH.zip` faylını çıxart.
2. ZIP-in içindəki faylları GitHub `imandustnihan/matchlab-az-online` deposunun kökünə əlavə et; mövcud faylları eyni adla yenilə. **`identity_unification.py` mütləq əlavə edilməlidir**, əks halda server `import` xətası verəcək.
3. `verified_profiles.json`, `styles.css`, `app.js`, `world_db.py`, `server.py`, `wikipedia_enrichment.py` və yeni test fayllarının da yeniləndiyinə bax.
4. Render son commit-i deploy etməlidir. `python prepare_database.py` və `python hosting_server.py` əmrləri dəyişmir.
5. Brauzerdə `Ctrl + F5` ilə yeni JS/CSS-ni aç. `Mikel Arteta` axtarışını və taktika meydançasını yoxla.

HTML + Python server formatı qalır. **APK və EXE bu mərhələdə yaradılmır**; yekun məhsul sınaqlarından sonra ayrıca qərar veriləcək.

## Test

`python -m unittest discover -p 'test_*.py' -v` — yerli 74/74 test uğurlu. Chromium masaüstü və mobil vizual testlərində CSS meydança probleminin düzəldilməsi, 1 Arteta axtarış nəticəsi, futbolçu + məşqçi karyerası, qapıçı rolunun qorunması təsdiqlənib. Real Wikipedia, Wikimedia və matç API-lərinin bütün istifadəçilər üçün cavab verməsi bu testlərlə zəmanət edilmir.
