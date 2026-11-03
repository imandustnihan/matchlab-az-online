# MATCHLAB AZ — Oracle Cloud Always Free serveri

Bu təlimat mövcud **Python + SQLite** serverini Oracle Compute VM-də işlətmək üçündür. Proqramın Android/Windows versiyalarının mənbə kodunu dəyişmir.

## Şərtlər

- Oracle Cloud Always Free hesabı və kompüterə SSH girişi. Qeydiyyat üçün kart yoxlanması tələb oluna bilər; mövcudluq regiona görə dəyişir.
- **Ubuntu 24.04 və ya 22.04** VM. Always Free uyğun VM forma və resurs məhdudiyyətlərini Oracle Console-da ayrıca yoxla.
- VM-nin **public IPv4** ünvanı və həmin ünvana yönələn domen (və ya sənə məxsus etibarlı DNS adı).
- Oracle VCN security list/NSG-də internetdən TCP **80** və **443** aç, **22/SSH-ni yalnız öz IP-nə** məhdudlaşdır. TCP 10000-i **xaricə açma**.
- Domenin A qeydi VM public IP ünvanını göstərməlidir; Caddy HTTPS sertifikatı bununla işləyəcək.

## Quraşdırma

VM-də (SSH ilə):

```bash
sudo apt-get update
sudo apt-get install -y git
git clone https://github.com/imandustnihan/matchlab-az-online.git
cd matchlab-az-online
sudo bash deploy/oracle/setup.sh api.senin-domenin.az
```

Script: Ubuntu paketləri, Caddy HTTPS reverse proxy, **systemd avtomatik restart**, `matchlab` adlı ayrı xidmət istifadəçisi, 506207 futbol reyestri qeydi üçün SHA-256 və SQLite bütövlüyü yoxlaması, localhost `/healthz` testi.

Yoxla:

```bash
curl -fsS https://api.senin-domenin.az/healthz
sudo systemctl status matchlab --no-pager
sudo journalctl -u matchlab -n 80 --no-pager
```

**Önəmli:** Oracle serverində hesab və VM yaradılmayıbsa, yuxarıdakı skriptlərin GitHub-da olması hələ onlayn yerləşdirmə deyil. Domain HTTPS və real API sorğuları işləməyincə Windows/Android ünvanlarını Oracle-a keçirmə.

## Yeniləmə

```bash
cd ~/matchlab-az-online
git pull --ff-only
sudo bash deploy/oracle/update.sh
```

## Sabitlik və xərc

Oracle Always Free VM Render Free-dəki 15 dəqiqəlik məcburi yuxunu aradan qaldırır, lakin **99.9% uptime zəmanəti yoxdur**. Uzun müddət boş qalan resurslar geri alına bilər. CPU/memory/disk/snapshot monitorinqini qur, həddən artıq resurs istifadəsi və büdcə xəbərdarlıqlarını Console-da aktivləşdir. Always Free xaricinə çıxmamaq üçün instance forması, boot volume, block volume və public IP şərtlərini yoxla.

Rəsmi mənbə: https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier.htm

## İnteqrasiya

HTTPS ünvanı işlək olduqdan sonra tətbiqin backend URL-i aşağıdakı formatda olacaq: `https://api.senin-domenin.az`. Hələlik `https://matchlab-az-online.onrender.com` saxlanılır.
