# MATCHLAB AZ v0.9.5 — Onlayn hazırlıq və sınaq hesabatı

Tarix: 31 oktyabr 2026.

## Yoxlananlar

- Paket ZIP-dən ayrıca müvəqqəti qovluğa çıxarıldı; içində əvvəlcədən açılmış `.sqlite` faylı yoxdur.
- Sıxılmış verilənlər bazası **4 hissədən** avtomatik birləşdirildi, hər hissənin SHA-256 dəyəri və yekun SQLite hash-i yoxlandı.
- `PRAGMA quick_check = ok`, **506 207** reyestr qeydi təsdiqləndi.
- Lokal işə salınmış ictimai server adapteri HTTP yoxlamalarından keçdi:
  - `200`: `/healthz`, `/api/status`, Ronaldo, Messi, Qarabağ axtarışları, ölkələr siyahısı, `/`, `/app.js`, `/styles.css`;
  - `403`: idarəetmə endpointləri və bütün POST sorğuları;
  - `404`: birbaşa Python kodunu və SQLite bazasını götürmə sorğuları.
- `render.yaml` üzərində Python runtime, build, start, port və sağlamlıq yoxlaması sazlandı.

## Tamamlanmamış doğrulamalar

- **Render-də real dərc olunma** bu söhbətdə aparılmayıb; buna görə ictimai domen və deploy ID yoxdur.
- Xarici ESPN, OpenLigaDB, TheSportsDB və Wikimedia internet cavabları bu mühitdə tam canlı təsdiqlənməyib.
- Chromium-un yerli `localhost` girişi təhlükəsizlik qaydası ilə bloklandığı üçün vizual real-brauzer testi yekun olaraq təsdiqlənməyib.
- Qol bildirişlərinin fon rejimində işləməsi və bütün futbolçu şəkillərinin təmin olunması bu buraxılışın təsdiqlənmiş funksiyaları deyil.

## Render Free qeydi

Pulsuz servis 15 dəqiqə fəaliyyətsizlikdən sonra yuxu rejiminə keçir, sıxılmış əsas reyestr isə hər yeni build zamanı bərpa edilir. İstifadəçi tərəfindən sonradan yaradılmış lokal keşlər yenidən deploy zamanı itə bilər.
