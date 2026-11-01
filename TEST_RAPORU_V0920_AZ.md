# MATCHLAB AZ v0.9.20 — Test hesabatı

- Test mühiti: Python 3.13, pytest, Chromium/Playwright, lokal HTTP server; xarici API sorğuları simulyasiya edilib.
- Test əmri: `python -m pytest -q`
- **Nəticə: 92 passed, 7 subtests passed (23.59s)**.
- JavaScript sintaksisi: `node --check app.js` — uğurlu.
- Python sintaksisi: `py_compile` (`server.py`, `hosting_server.py`, `wikipedia_enrichment.py`, `club_history.py`) — uğurlu.
- Funksional sınaq: Real Madrid tipli Wikipedia kubok cədvəlləri, sadə siyahılar, rəqəmi olmayan kuboklar, ikinci yerlərin filtr edilməsi, köhnə heyətin cari kimi göstərilməməsi, stadionun P115→P18→Commons lisenziyası, şəkil hüququn yoxlanması, mənbəli tarixi əlaqələr, masaüstü/mobil profil və tənzimləmə keçidləri.
- Əvvəlki regressiya: matç mərkəzi, futbolçu profilləri, Mikel Arteta QID birləşməsi, taktika studiyası, HTTP təhlükəsizlik və media-keş sınaqları.
- Verilənlər bazası: əvvəlki 506.207 kimlik qeydi saxlanılıb; SQLite sxemi dəyişdirilməyib.
- Məhdudiyyət: xarici Wikipedia/Wikidata və Commons cavabları internetdən canlı olaraq təsdiqlənməyib; browser ekranlarında sınaq məlumatları istifadə olunub.
