# MATCHLAB AZ v0.9.12 — Canlı matç mərkəzi

Bu versiya Sofascore və LiveScore-un canlı matç səhifələrində rast gəlinən ümumi istifadə rahatlığını MATCHLAB AZ-a uyğun **müstəqil dizaynda** təqdim edir. Onların loqo/dizaynını piksel-piksel kopyalamır və Sofascore/LiveScore məlumatlarını icazəsiz API/scraping vasitəsilə toplamır.

## Daxildir
- 7 günlük interaktiv matç təqvimi, əvvəlki/sonrakı həftə və tarix seçimi
- Bütün liqalar, canlı, bitmiş, gələcək, favorit filtrləri
- Sevimli liqaların brauzerdə saxlanması; liqa qrupları və sürətli seçmə
- İki sətirli komanda/hesab dizaynı, oyun statusu, saat və matç favoriti
- Matç profillərində ümumi məlumat, təsdiqlənmiş heyətlər, statistika, hadisələr və rəsmi mənbə keçidləri üçün ayrıca tablar
- Sofascore widgeti və rəsmi Sofascore/LiveScore matç linki paneli (v0.9.11-dən qorunub)
- Əvvəlki 506.207 futbolçu/klub/məşqçi kimlik qeydi və taktika studio modulu dəyişdirilməyib

## Mənbə məhdudiyyətləri
Mövcud pulsuz ESPN (qeyri-rəsmi), OpenLigaDB və TheSportsDB adaptərləri saxlanıb. Mənbələr uğursuz olarsa uydurma nəticə və ya heyət yaradılmır. Mənbə saatı real-vaxt təminatı deyil. Sofascore rəsmi widget məlumatlarını yalnız onun embed kodu mövcud olduqda göstərir.

## Quraşdırma
Tam yerli ZIP-i çıxart, `BASLAT_WINDOWS.bat` aç. Python 3.10+ lazımdır. HTTP ünvanı: http://127.0.0.1:8765

GitHub/Render üçün `main` üzərinə kod yazılmayıb, çünki yayımlama üçün ayrıca təsdiq tələb olunur. HTML + yerli server saxlanılıb, APK/EXE yaradılmayıb.
