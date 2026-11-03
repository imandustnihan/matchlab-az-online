# MATCHLAB AZ v0.9.57 — Native historical team form and connection diagnostics

## Windows EXE + Android Java APK
- Tarix arxivində komanda axtarışı nəticələrindən **Qələbə / Heç-heçə / Məğlubiyyət**, vurulan-buraxılan qollar və son 5 matç forması (Q/H/M) hesablana bilir.
- **Yalnız real, mənbədə nəticəsi qeyd olunmuş oyunlar** hesablanır: boş hesablar, qeyri-müəyyən uyğunluqlar və başqa klubların oyunları toplanmır.
- Tam mövsüm xülasəsi yalnız `complete=true` və `bundle=true` arxiv cavabına əsaslanır. Köhnə Render serverinin səhifələnmiş endpoint-i **BU SƏHİFƏ (TAM DEYİL)** kimi göstərilir.
- Tarix arxivi üçün yerli saxlanmış paketlər və köhnə serverlə uyğunluq rejimi qorunub.
- Windows server statusunda, Android-də isə **Server vəziyyətini yoxla** düyməsində real HTTPS cavab müddəti (ms) göstərilir.
- Hər iki platformanın versiyası `0.9.57` oldu; Windows Setup, portable EXE və Android APK müstəqil build olunur.
- Yeni C# WinForms smoke yoxlamaları və Android üçün SDK tələb etməyən JDK 17 müqavilə testləri əlavə edilib.

## Test və yayım hədləri
- Bu buraxılış üçün build və GitHub Actions smoke nəticəsi branch-də ayrıca yoxlanmalıdır.
- Android `assembleDebug` APK **debug imzalıdır**, Play Store release və əvvəlki fərqli imzalı APK-lardan yerində update zəmanəti deyil.
- Windows quraşdırıcısı kod-imzalı deyil. Microsoft SmartScreen xəbərdarlığı yarana bilər.
- Android/Windows **fiziki cihaz testləri** ayrıca qalır; emulyator testi fiziki cihaz təsdiqi deyil.
- Enzonic-də aktiv HTTPS endpoint təsdiqlənənədək tətbiqlər mövcud Render API-dən istifadə edir. 7/24 fasiləsiz işləmə bu dəyişikliklə təsdiqlənmir.
- Tarixi matçlar canlı nəticələr deyil; hər bir oyun və oyunçu statistikası yalnız mənbədə varsa göstərilməlidir. Bu yenilik canlı xəbərdarlıqların app bağlıykən gəlməsini təmin etmir.

## Mənbələr və sərhədlər
- OpenFootball football.json (CC0): https://github.com/openfootball/football.json — tarixi fixture və nəticələr; real-time live hesab axını deyil.
- football-data.org: https://www.football-data.org/pricing — pulsuz planda məhdud yarışlar, gecikməli nəticələr və limitlər; pulsuz tam canlılıq/heyət eventləri kimi təqdim olunmamalıdır.
- Android notification permission: https://developer.android.com/develop/ui/views/notifications/notification-permission — həqiqi bildiriş servisi əlavə olunarsa Android 13+ icazə və arxa-plan icrası ayrıca layihələndirilməlidir.
