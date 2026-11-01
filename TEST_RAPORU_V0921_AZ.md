# MATCHLAB AZ v0.9.21 — Test raportu

- `python -m py_compile server.py season_stats.py` — uğurlu.
- `node --check app.js` — uğurlu.
- `python -m pytest -q` — **103 passed, 7 subtests passed**.
- Əvvəlki 0.9.20 versiya sətri gözləyən 5 köhnə assert yeni versiyanın status və statik asset keçidlərinə uyğunlaşdırılıb.
- `test_v0921_assists.py` — mənbənin simulyasiya edilmiş cavabı ilə kimlik yoxlaması, yoxdursa 0 göstərməmək, 10 qeydlə məhdudlaşma, API server marşrutu, UI elementləri.
- `test_v0921_browser.py` — real Chromium vasitəsilə 1400px və 390px görünüşlərdə iki futbolçu müqayisəsi, dünya bazasından axtarış, mövsüm statistikası. API cavabları testdə **maket** idi.
- Xarici TheSportsDB bağlantısının real işləməsi **yoxlanmayıb**; istifadəçi açdıqda server xarici mənbəni sorğulayacaq.
- DB dəyişməyib: 506.207 dünya futbol kimliyi əvvəlki kimi saxlanıb.
