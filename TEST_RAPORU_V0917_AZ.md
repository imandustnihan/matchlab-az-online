# MATCHLAB AZ v0.9.17 — Test hesabatı

- **Avtomatik testlər:** 61/61 uğurlu (1 noyabr 2026).
- **Sintaksis:** Python modul compile və `node --check app.js` uğurlu.
- **Desktop + mobil:** mövcud axtarış, canlı matçlar, taktika redaktoru və profil görünüşü avtomatik yoxlanıb.
- **Media Expansion:** 8 dildə wiki sitelink/QID yoxlaması; 20-lik batch; pulsuz lisenziya; səhv kimlik, yanlış foto hostu, stadion/forma şəkli kimi yalancı loqonun rəddi, şəbəkə xətasında yanlış negative cache yazılmaması; disk media keşi; mənbə metadata cavabı.
- **Taktika:** seçilmiş futbolçunun profildən meydançaya əlavə edilməsi və real foto URL-sinin yadda saxlanması/ixrac üçün qorunması brauzerdə test edilib.
- **Baza:** 506.207 qeyd; 437.525 oyunçu / 43.031 klub / 24.120 məşqçi / 1.531 yarış. Media QID bağlantısı: oyunçu 143.832, klub 5.004, məşqçi 10.065.

### Testlə təsdiqlənməyən sahə
Bu mühitdən Wikimedia və canlı Render URL-sinə xarici HTTP/DNS bağlantısı yoxdur. Buna görə internet üzərindən faktiki yüklənən *əlavə şəkillərin sayını* təsdiq etmək mümkün olmayıb. `61/61` nəticəsi bütün futbolçu foto və klub loqolarının artıq mövcud olması demək deyil.
