<div align="center">

<img src="assets/icon.svg" alt="MATCHLAB AZ — original M logo" width="96" />

# MATCHLAB AZ
### ⚽ Futbol nəticələri, statistika və taktika studiyası — Windows & Android

**Azərbaycan dilinə fokuslanan native futbol mərkəzi.**

[![Windows + Android Build](https://github.com/imandustnihan/matchlab-az-online/actions/workflows/matchlab_build_native.yml/badge.svg)](https://github.com/imandustnihan/matchlab-az-online/actions/workflows/matchlab_build_native.yml)
[![Latest Release](https://img.shields.io/github/v/release/imandustnihan/matchlab-az-online?label=latest%20release)](https://github.com/imandustnihan/matchlab-az-online/releases/latest)

</div>

---

## 📥 Proqramı yüklə

| Platforma | Paket | Yükləmə |
|---|---|---|
| 🖥️ **Windows 10/11, 64-bit** | Quraşdırıcı: Start menyusu, masaüstü qısayolu, silinmə | [**MATCHLAB AZ Setup EXE**](https://github.com/imandustnihan/matchlab-az-online/releases/latest/download/MATCHLAB_AZ_Setup_0.9.54_x64.exe) |
| 💻 **Windows 10/11, 64-bit** | Portable: quraşdırmadan açılan versiya | [**MATCHLAB AZ Portable EXE**](https://github.com/imandustnihan/matchlab-az-online/releases/latest/download/MATCHLAB_AZ_Portable_0.9.54_x64.exe) |
| 📱 **Android 8+** | **TEST / debug APK** — mobil proqramın mövcud v0.9.52 versiyası | [**MATCHLAB AZ Android TEST APK**](https://github.com/imandustnihan/matchlab-az-online/releases/latest/download/MATCHLAB_AZ_Android_0.9.52_TEST.apk) |

> **Alternativ:** [Bütün buraxılışlar](https://github.com/imandustnihan/matchlab-az-online/releases) · [Ən yeni buraxılış](https://github.com/imandustnihan/matchlab-az-online/releases/latest) · [SHA-256 dəyərləri](https://github.com/imandustnihan/matchlab-az-online/releases/latest/download/SHA256SUMS.txt).
>
> Windows quraşdırıcısı və EXE hələ **rəqəmsal imzalanmayıb**. Windows SmartScreen xəbərdarlığı göstərə bilər. Yükləmənin mənbəsini və SHA-256 dəyərini yoxlayın. Bu versiya **Microsoft Store-da hələ yayımlanmayıb**.

## 🏟️ Windows Premium — v0.9.54

- **Matç mərkəzi:** günə və liqaya görə oyunlar, komanda adları və mənbədə varsa emblemlər; canlı, bütün və seçilmiş oyun filtrləri
- **Turnir cədvəlləri:** seçilən liqalarda mənbənin təqdim etdiyi sıralama; Azərbaycan Premyer Liqası da liqa seçimlərinə daxildir
- **Futbol arxivi:** futbolçu, klub və məşqçi axtarışı; mümkün olduqda foto, bio, karyera məlumatları və Wikipedia/Wikidata keçidləri
- **Taktika Studiyası:** 8 düzülüş, oyunçuları sürükləmə və adlandırma, 7 ehtiyat yeri, hərəkət oxları, tor, **animasiya**, PNG ixracı, avtomatik yerli yaddaş
- **İnterfeys:** orijinal yaşıl M loqosu, qısa açılış animasiyası, tünd masaüstü görünüşü və yığcam matç kartları
- **Sürət:** əvvəllər baxılan oyunlar lokal yaddaşdan göstərilə bilər; köhnə nəticələr açıq şəkildə **CANLI DEYİL** işarələnir
- **Quraşdırma:** offline Setup EXE, masaüstü qısayolu seçimi, Start menyusu və Windows-dan silinmə

**Etibarlılıq qeydi:** Real vaxt reytinqləri, xG, canlı heyət və transfer statistikası hər matç üçün təqdim edilmir. Məlumat boşluqları ehtimal kimi uydurulmur. Server pulsuz Render planında yuxu rejiminə keçə bilər.

## 📱 Android

Android native Java tətbiqi ayrıca saxlanılır. Bu Windows buraxılışında mobil mənbə kodu **dəyişdirilməyib**. APK test üçündür və Play Store buraxılışı hesab olunmur.

## 🧰 İnkişafçılar üçün

| Hissə | Texnologiya |
|---|---|
| Windows | C# · .NET 8 · Windows Forms (WebView yoxdur) |
| Windows quraşdırma | Inno Setup 6 |
| Android | Native Java · Android Gradle Plugin |
| Backend | Python 3 · SQLite · HTTPS |
| Paket avtomatlaşdırma | GitHub Actions → ictimai GitHub Releases |

Windows mənbə: [`native/windows-app/`](native/windows-app/) · Quraşdırıcı: [`native/installer/`](native/installer/) · Build təlimatı: [`native/BUILD_GUIDE_AZ.md`](native/BUILD_GUIDE_AZ.md).

### Yükləmə və quraşdırma problemi
[GitHub Issues-də xəta bildir](https://github.com/imandustnihan/matchlab-az-online/issues/new).

### Microsoft Store
İmzalanmış istehsal paketi, məxfilik sənədi, sabit yayım ünvanı və sertifikasiya mərhələləri tamamlanmalıdır. [Mağaza üçün hazırlıq qeydləri](native/STORE_WINDOWS_RELEASE_AZ.md).

---

<sub>MATCHLAB AZ müstəqil layihədir. Sofascore, FotMob və LiveScore ilə rəsmi əlaqəsi yoxdur. Klub emblem və futbolçu fotolarının hüquqları öz mənbələrinə aiddir.</sub>
