# MATCHLAB AZ v0.9.14 — test nəticələri

- **27/27** avtomatik Python/Playwright testi uğurlu: mövcud matç/heyət/mobil foto, klub emblemi, Wikipedia QID yoxlaması, stadion/klub profili, mətn və CC BY-SA keçidi.
- **4/4** HTTP yerli server yoxlaması uğurlu: `/api/status`, `/index.html`, `/app.js`, `/styles.css` (HTTP 200).
- `node --check app.js` və `python -m py_compile` yoxlamaları uğurlu.
- Profil dəyişikliyi verilənlər bazası arxivini yenidən yaratmır; baza **506207** qeyd saxlayır.
- **Məhdudiyyət:** real Wikipedia API cavabları bu mühitdə birbaşa sorğulanmayıb; xarici mənbə ilə real işləmə deploy-dan sonra ayrıca yoxlanmalıdır. Browser məlumat yoxlamaları simulyasiya olunmuş nümunələr əsasında aparılıb.
- GitHub və Render bu ZIP-in hazırlanması ilə avtomatik yenilənməyib. Bunun üçün GitHub-a commit və Render deploy tələb olunur.
