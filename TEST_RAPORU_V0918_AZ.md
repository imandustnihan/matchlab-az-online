# MATCHLAB AZ v0.9.18 — Test hesabatı

- Lokal Python sintaksis və `node --check app.js`: **OK**.
- `python -m unittest discover -p 'test_*.py' -v`: **74/74 OK**.
- Arteta `Mikel Arteta` axtarışı: **1 QID profili**, filtr üzrə 1 nəticə, təkrar adlardan şəxs qarışığı yoxdur.
- Arteta `p:mikel-arteta`, `c:mikel-arteta`, Reep şəxs ID-si: **eyni Q185572 profili**.
- Wikipedia offline fallback: PSG, Rangers, Real Sociedad, Everton, Arsenal və Barcelona B futbolçuluq dövrləri, Manchester City köməkçi məşqçi və Arsenal baş məşqçi dövrləri — mənbə https://en.wikipedia.org/wiki/Mikel_Arteta.
- Naməlum `assists` dəyəri sıfır kimi göstərilmir. Sənədləşmiş `assistsN` göstəricisi parserdə oxunur.
- Taktika `.top` qara düzbucağı: **düzəldildi**. `getComputedStyle(...).backgroundColor` transparent, `backdropFilter=none`.
- Köhnə DEF/MID/ATT rolları redaktorda dəstəklənir; yeni düzülüşlərdə rolu valid seçilən futbolçu verilənlərinə uyğun təyin edir.
- Masaüstü/mobil Playwright: Arteta tək nəticə, birləşmiş profil, meydançada CM mövqeyi, 11 oyunçu, `pageerror` yoxdur.
- Lokal HTTP status və aktiv fayllar: əvvəlki testlər uğurludur; futbol DB mövcuddur, hesab sayı 506.207 olaraq qalır.

Məhdudiyyət: xarici Wikipedia/MediaWiki serverlərinin cari cavabları, canlı matç nəticələri və bütün futbolçuların Wikipedia karyeralarının tamlığı yoxlanmayıb. Bu testlər yerli məlumatlara və HTTP maketlərinə əsaslanır.
