# MATCHLAB AZ v0.9.24 — test nəticəsi

- **130/130** unittest uğurlu, 2026-11-01.
- `node --check app.js`: uğurlu.
- Mikel Arteta axtarışı: **1 Q185572** şəxs profili, futbolçu və məşqçi rolları; profilə həm klublar, həm məşqçilik illəri daxildir.
- Pep Guardiola, Carlo Ancelotti, Xabi Alonso və Jürgen Klopp ikili rol sınaqları; Carlo/Davide ayrı qalıb.
- Wikipedia təsdiqlənmiş səhifə kimliyi cədvələ üstün tutulur. Yanlış `wikibase_item` Wikipedia karyerası səhv profilə keçmir.
- Wikidata P54/P580/P582 üzvlüyü və tarixlər: mövcudluğu yoxlanır; olmayan son tarix “aktiv” kimi iddia edilmir.
- Wikipedia məqaləsi olmayan QID-li şəxsdə Wikidata ehtiyatı; QID və komanda adı uyğun gəlməyəndə boş göstərilmə.
- Statistikası olmayan komandalara saxta matç/qol/asist 0 əlavə olunmur.
- Taktika CSS, mobil/masaüstü brauzer, canlı matçlar, klub profilləri və əvvəlki regresiyalar keçib.
- Açıq məhdudiyyət: real Render saytına bu mühitdən birbaşa HTTP yoxlaması uğursuz olub; xarici API-lərin faktiki cavab verməsinə zəmanət yoxdur.
