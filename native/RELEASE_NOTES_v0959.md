# MATCHLAB AZ v0.9.59 — Native Match Center + REAL Offline Football Index

## Windows EXE + Android APK (no WebView)
- SofaScore-un naviqasiya prinsiplərindən inspirasiya alınmış **orijinal** matç-mərkəzi: Xülasə, Statistika, Heyətlər və Hadisələr bölmələrini ayrıca seç.
- Matçın hər bölməsi real, mənbədə mövcud məlumatı göstərir. xG, heyət, events, animasiyalar və proqnozlar uydurulmur. Verilməyən göstəricilər aydın göstərilir.
- Liqa üzrə qruplaşdırma və **saata görə sıralama** seçimi Android və Windows-da var. Android seçimi yerli yaddaşda saxlanır.
- **506,207 təsdiqli Reep CC0 futbol kimliyi**: build zamanı Git deposunda saxlanmış, SHA256 ilə yoxlanmış 16 hissəli SQLite reyestrdən identifikator/ad/kateqoriya/ölkə offline indeksi yaradılıb.
- Android APK-də gzip arxiv assets içindədir; Windows EXE-də embedded resource olaraq paketlənir. Offline axtarış həqiqi ID-ləri qaytarır, canlı klub/karyera/foto/oyun statistikası deyil.
- İnternet varsa server nəticəsi üstün tutulur, server gecikəndə və ya əlçatmaz olanda yerli reyestrdə axtarış aparılır. Şəbəkəsiz məlumat yenilənməsi iddia edilmir.
- Taktika studiyası, əvvəlki M loqosu, bildiriş sazlamaları və tarix arxivi qorunur.

## Testlər
- Reep arxivi 16 hissənin ölçü və SHA256 yoxlamasından keçir, yekun SQLite SHA256 və 506207 sətir yoxlanır.
- Native Android Java offline identifikasiya JDK17 smoke testləri: diakritiklər, klub/məşqçi/oyunçu filtri, boş nəticə, maksimum nəticə limiti.
- Windows WinForms: match center-in dörd tabı, müstəqil simulyasiya edilmiş təsdiqli API cavabı, offline axtarış və ekran görüntüləri.
- GitHub Actions: Android APK build + emulyator, Windows portable EXE + real Inno Setup install/uninstall.
- Fiziki Redmi Note 13 Pro / Windows 11 sınaqları yenə ayrıca lazımdır.

## Məhdudiyyətlər
- Android debug APK imzalıdır; Windows quraşdırıcısı kod-imzalı deyil.
- Reep CC0 offline data təxminən 506k **kimlik faktı** (ad, ID, kateqoriya, ölkə) saxlayır; bu, 506k dolğun oyuncu profili deyil.
- Render API gecikə bilər, tarixi arxivdə serverin yeni /api/history-bundle endpoint-i hələ aktiv olmaya bilər. Enzonic 7/24 təsdiqlənməyib.
- Profil bio, canlı qol, xG, xəritə, təsdiqlənmiş tam heyətlər üçün müstəqil mənbə və API əhatə dairəsi tələb olunur. Tətbiq saxta məlumat yaratmır.
- Fayl ölçüsü yalnız real offline indeksin hesabına artırılıb; padding/random ballast əlavə olunmayıb.

## Mənbə
- Reep CC0 reyestri: https://www.reep.football/
- Sofascore re-design və filtrlər: https://www.sofascore.com/news/sofascores-new-home-screen-a-smarter-faster-way-to-follow-sports
- Sofascore guide: https://sofascore.helpscoutdocs.com/article/159-how-to-use-matches-list-filters
