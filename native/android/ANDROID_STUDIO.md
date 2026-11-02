# MATCHLAB AZ v0.9.47 — WebView-siz Android Studio tətbiqi

Bu versiya **Java native Android** ekranları ilə qurulub. HTML və WebView yoxdur.
SofaScore və LiveScore-dan yalnız istifadəçi təcrübəsi prinsipləri öyrənilib; onların kodu və qorunan dizaynları istifadə edilməyib.

## Görünüş və funksiyalar
- Daha kompakt başlıq, alt naviqasiya və orijinal vektor ikonlar
- Mənbə ilə təsdiqlənən klub loqoları üçün təhlükəsiz HTTPS şəkil yüklənməsi, əks halda neytral hərf
- Matçların liqa üzrə qruplaşdırılması, hesab, mənbə və canlı/köhnə statusu
- Turnir cədvəlinin kompakt və geniş görünüşləri
- Oyun, qələbə, heç-heçə, məğlubiyyət, qol fərqi, xallar, mənbədə olduqda vurulan/buraxılan qollar və son oyun forması
- Matç mərkəzi: mənbədə mövcud real statistika, heyət, hadisələr
- Dünya reyestri axtarışı, profillər, seçilmişlər və yerli taktika meydançası

## Android Studio
1. GitHub Actions > MATCHLAB AZ v0.9.47 native Android Studio project and APK işini aç
2. Source ZIP-i yüklə və çıxart
3. Android Studio > File > Open > MATCHLAB_AZ_Android_Studio_Native
4. Gradle Sync, sonra Build > Build APK(s)
5. APK yolu: app/build/outputs/apk/debug/app-debug.apk

JDK 17, Gradle 8.9, AGP 8.7.3, Android SDK 35.
Release imza və uzunmüddətli yeniləmə üçün sabit, gizli keystore lazımdır.

## Dürüst məhdudiyyətlər
API əlçatan deyilsə canlı nəticələr və tam statistikalar göstərilmir.
Bəzi mənbələrdə qollar, künclər, kartlar və heyətlər mövcud olmaya bilər.
Geniş taktika redaktoru və native bildiriş sistemi hələ tamamlanmayıb.
Native debug build-in real Redmi/HyperOS telefonunda sınağı ayrıca aparılmalıdır.
