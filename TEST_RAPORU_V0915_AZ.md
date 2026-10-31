# MATCHLAB AZ v0.9.15 — test hesabatı

- **39/39** avtomatik unittest / Chromium Playwright testi: OK
- Mənbə maketləri: ESPN, OpenLigaDB, TheSportsDB, Wikipedia/Wikidata
- Masaüstü və mobil canlı matç, matç detalları, heyətlər, favoritlər, 7 günlük təqvim: OK
- Taktika qeydləri iki yeni brauzer konteksti arasında saxlanır: OK
- Wikipedia QID uyğunsuzluğunda məqalə infoboksu rədd edilir: OK
- Wikidata gün/ay/il precision fərqləri saxlanır: OK
- SQLite keş xətası profilin açılışını pozmur: OK
- Qismən karyera cəmi yanlış ümumi rəqəm kimi göstərilmir: OK
- Server HTTP API və statik fayllar, public /healthz, şəxsi faylların bağlı olması: OK
- `node --check app.js` və Python bytecode yoxlaması: OK
- `world_football.sqlite` cəmi 506207 qeyd: OK
- Xarici internet API və Render saytının real brauzer təsdiqi: bu mühitdən mümkün olmadı. Özünü doğrulayan xarici data testi keçirilmədi.
