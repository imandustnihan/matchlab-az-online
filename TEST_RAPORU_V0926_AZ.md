# MATCHLAB AZ v0.9.26 — test hesabatı

- Tarix: 2026-11-01
- Kod: HTML / JS / CSS + Python server
- **Yerli avtomatik testlər: 145/145 keçdi, 0 xəta**
- Əvvəlki 135 regresiya testi saxlanılıb. Yeni testlər: 9 Python mənbə/təhlükəsizlik/sxem testi və 1 geniş Playwright desktop+mobil ssenarisi.

## Təsdiqlənən yoxlamalar

1. 12 əsas + 56 əlavə kod; 68 kod unikal; `/api/leagues` cavabı; `all` sorğusu 12 mənbədən artıq yükləmir.
2. ESPN cədvəlində həqiqi vurulan/buraxılan qol, top fərqi, qrup və mənbəli son forma sahələri; yoxdursa `None`; pulsuz ehtiyat cədvəlində naməlum qollar sıfır deyil.
3. `strAssist` mənbədə varsa matç hadisəsində göstərilir, yoxdursa yaradılmır.
4. Altı mənbəli tarixi məşqçi şablonu və mənbə linkləri; düzgün 10 meydan oyunçulu formasiya sayları.
5. Desktop və mobil Chromium: məşqçi şablonunu 3-2-4-1-ə tətbiq et; 11 rəqib markerini göstər; künc/cərimə zərbəsi; iki səhnə saxla/oynat/dayandır; JSON ixrac et.
6. Desktop və mobil Chromium: 68-li liqa seçimi; mənbəli qrup cədvəli, qollar, forma; cavabsız liqa üçün şəffaf boş vəziyyət.
7. Desktop və mobil Chromium: ayarlar; səs səviyyəsi; bildiriş sınağı parametri gizlicə aktivləşdirmir; hesab 0:0 → 1:0 olanda bir xəbərdarlıq, təkrar sorğuda ikinci xəbərdarlıq yoxdur.
8. `node --check app.js`, `python -m py_compile *.py` uğurludur.

## Testin əhatə etmədikləri

Pulsuz xarici API-lərdən **real internetdə** bütün 68 yarış üçün turnir cədvəlini və bütün futbolçuların assistlərini təsdiqləmək mümkün deyil. Səhifə bağlı olanda push bildirişləri də daxil deyil. Real Android/Windows EXE testləri keçirilməyib, çünki bu paket yalnız HTML+server üçündür.
