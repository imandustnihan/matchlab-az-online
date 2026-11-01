# MATCHLAB AZ v0.9.25 — test hesabatı

- Baza: v0.9.24, GitHub commit `8dd970eef6b27fbeb0762e3ad3a51e6c6a66c5db`.
- `node --check app.js`: keçdi.
- `python -m py_compile wikipedia_enrichment.py hosting_server.py`: keçdi.
- `python -m unittest discover -p 'test_*.py' -q`: **135 test, OK**.
- v0.9.25 keçid bərpası: **5/5 test**, həm desktop, həm mobil Chromium smoke-test.
- Köhnə v0.9.14 klub profilinə aid Wikipedia lisenziyası və dil keçidləri: keçdi.
- Mövcud Arteta, Guardiola, Wikipedia career və futbolçu-məşqçi vahid şəxs testləri: keçdi.
- Taktika studiyası, canlı matçlar, profil statistikası, klub loqosu və assist regresiya testləri: keçdi.
- Baza faylları: dəyişdirilməyib. Testin yaratdığı `wikipedia_profiles.sqlite` keş faylı yayımlama paketinə daxil edilməyib.
- Render canlı Wikimedia HTTP inteqrasiyası: **bu mühitdən yoxlanılmayıb** (xarici DNS mövcud deyil).
- Xırda qalan məsələ: SQLite bağlantıları barədə test mühitində `ResourceWarning` bildirişləri var.
