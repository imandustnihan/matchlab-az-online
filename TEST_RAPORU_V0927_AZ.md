# MATCHLAB AZ v0.9.27 — Bildiriş səsi və tarixçə dəyişiklikləri: sınaq hesabatı

Tarix: 1 noyabr 2026

## Nəticə

- Bütün cari avtomatik testlər: **147 test / 147 uğurlu**, `python -m unittest discover -p 'test_*.py' -v`.
- İstiqamətləndirilmiş HTTP, versiya, məşqçi, bildiriş testləri: 46 / 46 uğurlu.
- Yeddi ayrı Web Audio səs şablonu masaüstü (1350 px) və mobil (390 px) simulyasiya edilmiş brauzerlərdə yoxlanıb. Hər şablonun ritm və tezlik imzası ayrıdır.
- Bildiriş tarixçəsi interfeysdən silinib. Əvvəlki `matchlab_v08_alerts` localStorage açarı tətbiq başlananda təmizlənir. Əvvəlki bildirişlərin təkrar edilməməsi üçün daxili `notifiedKeys` texniki siyahısı qalıb.
- Əvvəlki `coach_tactics.js` HTTP 404 düzəlişi `server.py` faylında qorunub.
- Yerli `hosting_server.py` smoke sınağı: `/healthz` **200**, `/index.html` **200**, `/app.js?v=0927` **200**, `/styles.css?v=0927` **200**, `/coach_tactics.js?v=0927` **200**, `/server.py` **404** (mənbə koduna giriş bloklanıb). Baza ümumi sayı **506207**.
- GitHub/Render deploy bu paketdə **edilməyib**; real onlayn xarici futbol API-ləri və OS səs sistemi bu testlərlə tam təsdiqlənmir.

## Texniki təfərrüat

- Yeni `NOTIFY_SOUND_PATTERNS` 7 kateqoriya üçün `AudioContext` ilə orijinal osilator ardıcıllıqları yaradır.
- `notifyEmit` hadisə kateqoriyasını səs generatoruna ötürür: `goal`, `kickoff`, `final`, `yellow`, `red`, `sub`, `var`.
- Səs nümunələri əl ilə `▶ Dinlə` seçilərək sınana bilir; kateqoriya səssizdirsə də nümunəni dinləmək mümkündür.
- Ümumi səs səviyyəsi 0–100 arasında dəyişir; səslərin hamısını söndürmək mümkündür.
- Masaüstü və telefon dizaynı yeni `.notify-sound-*` sinifləri ilə yoxlanıb.
- Brauzerin autoplay məhdudiyyəti səbəbi ilə ilk səs üçün istifadəçi qarşılıqlı təsiri tələb oluna bilər.
- Sistem bildirişinin əməliyyat sistemi tərəfindən ifa edilən səsi JavaScript ilə tam idarə etmək olmur. Xüsusi səslər saytda işləyən Web Audio əsasında ifa edilir.
- Qol və hadisə avtomatik bildirişləri üçün faktiki canlı məlumat mənbələri və aktiv açıq səhifə tələb olunur.

## İstinadlar

- https://help.livescore.com/hc/en-gb/articles/38914843600786-Can-I-choose-the-notification-alerts-I-receive-in-the-app
- https://play.google.com/store/apps/details?id=com.sofascore.results
- https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API/Best_practices
