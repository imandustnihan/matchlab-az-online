# MATCHLAB AZ — Enzonic Python Hosting (kart tələb etməyən alternativ)

Bu paket mövcud MATCHLAB AZ serverinin **Python + SQLite** arxitekturasını dəyişdirmədən Enzonic Python serverində işə salmaq üçündür.

**Status:** GitHub yerləşdirmə faylları hazırdır; Enzonic hesabında server qurulub və HTTPS işləyir demək **deyil**. Render aktiv qalır və Windows/Android proqramlarının server ünvanı hələ dəyişdirilməyib.

## Əvvəlcə düzgün pulsuz məhsulu seç

1. https://www.enzonic.com/python səhifəsində qeydiyyatdan keç.
2. **Python hosting / Python generic** runtime seç. “Deploy Free” funksiyalarının miqyaslanma və yatma qaydaları fərqli ola bilər.
3. Planın **512 MB RAM, 50% CPU, 10 GB SSD, Always On** yazıldığını yoxla. Pulsuz yer region və mövcudluqla məhdudlaşa bilər. Bu, xidmətin öz iddiasıdır, zəmanətli SLA deyil.
4. Yaxın region varsa Frankfurt, Spain və ya Europe-dan uyğununu seç.
5. Repository: `https://github.com/imandustnihan/matchlab-az-online`, branch: `main`.
6. Startup command: `sh deploy/enzonic/start.sh`. Bəzi panellər `python3` əvəzinə `python` tələb edir. Python 3.10+ istifadə et.
7. `PORT` dəyişənini panelin verdiyi HTTP portuna təyin et. Proqram bu portda `0.0.0.0`-da dinləyir; Render-də port avtomatik təyin olunur. Əlavə `MATCHLAB_BIND_HOST` dəyişənini paneldə `127.0.0.1` etmə.
8. Açıq **HTTPS** URL tələb olunur. Panel yalnız `IP:port` verirsə, Windows EXE-yə HTTP ünvanı yazma: reverse proxy, domen və TLS lazımdır. HTTPS olmadan son istifadəçi buraxılışına keçmə.

İşlədikdən sonra URL-ləri yoxla:

```bash
curl -fsS https://SENIN-ENZONIC-HTTPS-URL/healthz
curl -fsS https://SENIN-ENZONIC-HTTPS-URL/api/status
curl -fsS "https://SENIN-ENZONIC-HTTPS-URL/api/live?league=eng.1&date=2026-11-03"
```

- `/healthz` **200** qaytarmalı və `registryTotal=506207` olmalıdır.
- `/api/status` serverin sağlamlığını göstərməlidir.
- Canlı nəticə üçün upstream məlumat mənbələri ayrıca işləməlidir. Boş matç siyahısı avtomatik hostinq problemi demək deyil.
- `/world_football.sqlite` və `/hosting_server.py` xaricdən **404** olmalıdır.
- 30 dəqiqə fəaliyyətsiz qaldıqdan sonra `/healthz` cavabını ölç: provayderin “Always On” iddiasını ayrıca təsdiqlə.

## Məhdudiyyətlər

- 512 MB RAM güclü çoxistifadəçili server üçün kifayət etməyə bilər; SQLite + paralel canlı mənbələr yüklənmə testindən keçirilməlidir.
- Enzonic-in pulsuz və 24/7 imkanları provayderin açıqlamasına əsaslanır; real uptime və gələcək plan şərtlərinə zəmanət verilmir.
- Serverdən xaricə ESPN, Wikipedia və digər mənbələrə sorğular limitlənə bilər.
- Render serverini yalnız yeni HTTPS hostinq, 506207 qeyd və matç API testi təsdiqləndikdən sonra ikinci plana keçir.
- Hesab şifrəsini, tokenlərini, SSH/private key və kart məlumatını ChatGPT-yə göndərmə.

**Rəsmi plan:** https://www.enzonic.com/python
