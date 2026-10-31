# MATCHLAB AZ — v0.9.5, onlayn HTML + Python server

Bu paket **Render-ə yerləşdirilməyə hazırdır**, amma internetə hələ dərc edilməyib.

## Nə var?
- HTML, CSS, JS interfeysi; real Reep 2026-10-25.1 futbol kimlik bazası (506 207 qeyd).
- `world_football.sqlite.gz.part001`–`004` arxiv hissələrindən avtomatik qurulan, dəyişdirilməz əsas axtarış indeksi.
- Futbolçu, klub, məşqçi axtarışı və mövcud Wikidata əlaqələri.
- ESPN (qeyri-rəsmi), OpenLigaDB, TheSportsDB sorğularında ehtiyat mənbə məntiqi, lakin **canlı nəticələr təmin edilmir**.
- Şəkillər yalnız mənbə və lisenziya imkan verdikdə yüklənir; hər profilin fotosu yoxdur.
- Publik versiyada verilənlər bazası yükləmə və idarəetmə əməliyyatları bloklanıb.

## Onlayn necə dərc edilir?
1. Render hesabını qoş və bu layihənin `render.yaml` faylı olan qovluğunu GitHub repozitoriyasına yüklə. **`world_football.sqlite` faylını yükləmə** — `.gitignore` ilə xaricdir. `world_football.sqlite.gz.part001`–`004` fayllarını isə yüklə; hər biri GitHub brauzer limitindən kiçikdir.
2. Render-də **New → Blueprint** seç, GitHub repozitoriyasına qoş və `render.yaml` planına bax.
3. Xidmət üçün `free` planını təsdiqlə. Render yerləşdirdikdən sonra `https://<verilən-host>.onrender.com/` kimi **gerçək** link yaradacaq; öncədən link uydurmaq olmaz.
4. `/healthz`, `/api/status`, `/api/search?q=Ronaldo`, axtarış və taktika ekranlarını yoxla.

İnternetsiz paketdən test: `python prepare_database.py` və `PORT=8765 python hosting_server.py` (terminal tələb edir; son istifadəçi bu addımları etməyəcək).

## Məhdudiyyətlər
- Render Free **15 dəqiqə istifadəsizlikdən sonra yatma** rejiminə keçir və yenidən açılış gecikə bilər.
- Pulsuz veb servisdə disk müvəqqətidir; əsas 506 207-lik baza hər deploy-da yenidən paketdən bərpa edilir, amma sonradan yığılan Wikipedia keş və skor snapshot-ları restartda itə bilər.
- Futbol məlumat mənbələri açarsız olsa da bəziləri bloklana bilər; Canlı Matçlar heç vaxt uydurma nəticə göstərməməlidir.
- İctimai açıq host test məqsədlidir. Əsl real-vaxt push, bütün şəkillər və tam tarixi statistika üçün müqaviləli provider və dayanıqlı DB tələb olunur.
- Şəxsi API açarları, parollar bu ZIP-ə daxil edilməyib.

## Məlumatların hüquqi statusu
Reep/Wikidata CC0 haqqında qeydlər və fotoların müəllif hüquqları üçün `SOURCES_AND_LIMITS.md` və `PHOTO_CREDITS.md` fayllarına bax.

## GitHub brauzerində yükləmək (CMD yoxdur)
1. GitHub-da yeni **private** repo yarat (`matchlab-az`).
2. ZIP-i tam aç. Qovluğun içindəki faylları GitHub-da **Add file → Upload files** ilə repoya qoy. Dörd `world_football.sqlite.gz.part...` parçasının **hər birini** yüklə, lakin `world_football.sqlite`-i yükləmə.
3. Render → **New → Blueprint** və ya **New → Web Service** seç; GitHub hesabını və repoyu bağla.
4. `render.yaml` avtomatik olaraq serveri və verilənlər bazasını quraşdırır.
5. `https://...onrender.com/` linki yalnız **Render deploy uğurla başa çatdıqdan sonra** mövcud olacaq.

Qeyd: Bu addımlar hesab sahibinin nəzarətindədir. Quraşdırılmış Render əlavəsi bu söhbətdə server yaratma əmri göstərmirsə, dərc etmə üçün ChatGPT **Work** rejimində həmin əlavədən istifadə et.
