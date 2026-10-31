# MATCHLAB AZ v0.9.13 — Şəkillər və loqolar

Bu versiya v0.9.12 üzərində qurulub və bütün əvvəlki canlı matç/taktika/profil funksiyalarını saxlayır.

## Düzəlişlər

- Axtarışda görünən ilk 75 profil üçün təsdiqlənmiş Wikidata QID-si olan fotolar/loqolar ardıcıl partiyalarla yoxlanılır.
- Köhnə xəta: İlk 16 ID üçün sorğu yaradıldıqdan sonra partiyaya daxil olmayan profillər də səhvən 10 dəqiqəlik «şəkil tapılmadı» vəziyyətinə düşürdü. Düzəldildi.
- Yeni səhifədə «Daha 75 nəticə» seçdikdə yeni profil şəkilləri də sorğulanır.
- Ana səhifədəki seçilmiş futbolçuların şəkilləri də partiyalarla yoxlanır.
- Profildə "Şəkli yenidən yoxla" düyməsi əvvəlki uğursuz nəticəni sıfırlayıb təzədən yoxlayır.
- Futbolçu portreti P18, klub gerbi isə yalnız P154 kimi göstərilir. Bir klubun stadion fotosu loqo sayılmır. P154, futbolçu şəkli kimi istifadə edilmir.
- Onlayn Render və yerli server versiya indikatorları yeniləndi; CSS/JS keşlərinin dəyişməsi üçün versiyalı yollar.

## Məhdudiyyətlər

- 506.207 qeyd real ad reyestridir, hazır foto arxivi deyil. Bütün şəxslərin şəklini avtomatik tapmaq mümkün deyil.
- QID olmayan şəxs üçün ad bənzərliyinə əsasən başqa futbolçunun şəklini götürmürük.
- Wikimedia materiallarının müəlliflik, fotoqraf və lisenziya hüquqlarına riayət edin.
- Sofascore/LiveScore məxfi API-lərinə və tətbiq fayllarına müdaxilə edilmir; mövcud rəsmi widget/keçid paneli saxlanır.
- Heç bir API şifrəsi tələb edilmir.

## GitHub + Render

5 yenilənmiş kod faylı: `app.js`, `server.py`, `wikipedia_enrichment.py`, `hosting_server.py`, `index.html`. Bundan əlavə `test_free_v099.py` faylında köhnəlmiş versiya gözləntisi 0.9.13 olaraq yenilənib; yeni `test_v0913_media.py` testi və bu README əlavə edilib.
GitHub-a ZIP-in içindəki ayrı faylları yüklə, ZIP-i özü repo kökünə qoyma. Commit ediləndə Render avtomatik deploy edirsə yeni build başlatmalıdır. Render build: `python prepare_database.py`, start: `python hosting_server.py`.

**Kodların yalnız bir hissəsində nə qədər foto bərpa edildiyi real Wikidata bağlantısı ilə yoxlanıla bilər; testlər xarici serverdən asılı deyil.**
