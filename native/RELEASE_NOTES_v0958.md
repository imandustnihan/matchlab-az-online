# MATCHLAB AZ v0.9.58 — Native ev/səfər forma analitikası

## Windows EXE + Android APK
- OpenFootball mənbəsində nəticəsi təsdiqlənmiş tarixi oyunlardan ev və səfər Qələbə/Heç-heçə/Məğlubiyyət göstəriciləri ayrıca hesablanır.
- Qol fərqi (+/−) və qələbə faizi əlavə edilib; faizin məxrəci yalnız qeydə alınmış oyunlardır, 0 oyunda 0% göstərilir.
- Ev/səfər hesab istiqaməti düzgün çevrilir: qonaq komandanın vurduğu qol awayScore əsasında hesablanır.
- Axtarış bir neçə fərqli klub adına uyğun gələndə qarışıq forma statistikası göstərilmir; dəqiq klub adı istənilir.
- Tarixi məlumatlar canlı kimi təqdim edilmir, köhnə serverin səhifələnmiş cavabı BU SƏHİFƏ (TAM DEYİL) olaraq qalır.
- Android kartında göstəricilər çoxsətirli, Windows tarix arxivi kartında əlavə iki statistik sətirdir.
- Quraşdırıcı, EXE, Android APK və CI artifact versiyaları 0.9.58-ə uyğunlaşdırılıb.

## Test rejimi və məhdudiyyətlər
- Java 17 ilə APK-dəki eyni riyazi məntiq lokal olaraq test edilib. Windows üçün ayrıca WinForms GUI smoke testlərinə yeni hesablamalar əlavə edilib.
- GitHub Actions Windows build, real Setup quraşdırma/silmə və Android emulyator yoxlamaları tamamlandıqda nəticələr ayrıca dəyərləndirilir.
- Android çıxışı assembleDebug ilə debug imzalıdır; Play Store release deyil.
- Windows quraşdırıcısı kod imzalı deyil, Microsoft SmartScreen xəbərdarlığı mümkündür.
- Real Windows 11 və Redmi Note 13 Pro cihazlarında sınaqlar hələ ayrıca lazımdır.
- Enzonic-in işləyən HTTPS endpoint-i doğrulanmayıb; mövcud Render backend saxlanılıb. 7/24 zəmanət verilmir.

## Mənbələr
- OpenFootball football.json CC0: https://github.com/openfootball/football.json — tarixi nəticələr, real-time deyil.
- Android Views accessibility: https://developer.android.com/guide/topics/ui/accessibility/views/apps-views — 48dp tövsiyəsi, hələ tam UI auditindən keçməyib.
- .NET Windows Forms DPI guidance: https://learn.microsoft.com/en-us/dotnet/desktop/winforms/automatic-scaling-in-windows-forms
