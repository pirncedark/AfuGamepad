# PadKöprü — Gamepad Sorunları Çalışması

Tarih: 2026-09-16
Amaç: Hangi kol takılı olursa olsun, her oyun kolu **her gün aynı şekilde** görsün.
x360ce'nin yerini alacak, oyuna DLL koymadan sistem genelinde çalışacak, oyunları otomatik tanıyacak.

---

## 1. Tespit (bu bilgisayarda ölçüldü)

### Belirti
- Test sitesinde kol çalışıyor, Home tuşu Xbox Game Bar'ı açıyor → **kol ve Windows sağlam.**
- Aynı kol bir gün bir oyunda çalışıyor, ertesi gün başka oyunda (veya aynı oyunda) algılanmıyor.

### Ölçüm sonuçları
| Bulgu | Değer | Anlamı |
|---|---|---|
| Kayıtlı ama takılı olmayan (hayalet) kol kaydı | **~60 adet** | Her taktığında Windows yeni kayıt açmış |
| Görülen farklı kollar | 413D:2104, 37D7:2401, 045E:028E (Flydigi Vader 3 dahil), 057E:2009 (Switch Pro), 2563:0575/0526 (ShanWan), 04B4:2412, 054C (PS4/PS5)… | Birden çok kol, çoğu "sahte Xbox 360" kimliğiyle |
| Aynı kolun XInput sırası | IG_00, IG_01, IG_02, IG_03, IG_04, IG_06 | Kol her bağlanışta **farklı yuvaya** düşüyor |
| Sabah 413D kolu | XInput **yuva 1**'de, yuva 0 boş | Sadece "1. oyuncu"yu okuyan oyun kolu görmez |
| Şu an 37D7 kolu | DirectInput'ta hem joy0 hem joy2 | Eski joystick numaraları birikmiş |
| DirectInput joystick numaraları (kayıt defteri) | Joystick1..6 farklı kollara atanmış | Eski oyunlar "Joystick 1"i arıyor, orada başka/olmayan kol var |
| vJoy | Hata durumunda | Bozuk sanal cihaz, temizlenmeli |
| ViGEmBus | Kurulu, çalışıyor | Sanal kol altyapısı hazır |
| HidHide | Yok | Kurulacak |

### Kollar
| Kimlik | Kol | Not |
|---|---|---|
| 413D:2104 | **BigBig Won Blitz 2 TMR** (Windows'a "Xbox 360 Controller" diye tanıtıyor) | Sorunlu kol. XInput / Sony / Switch modları, kablo veya 2.4G alıcı. Yazılımı: BigBig Won / Mojiang Assistant |
| 37D7:2401 | Flydigi Vader 5 Pro | Flydigi Space Station servisi arka planda çalışıyor |

### ⚠ Sürücü çakışmaları (en büyük şüpheli)
| Bulgu | Neden sorun |
|---|---|
| **HidGuardian, HIDClass'a 2 kez "UpperFilter" olarak kayıtlı.** Servisi durmuş, sürümleri 1.9 / 1.14 (2017-2018) | Eski DS4Windows'tan kalma "kol gizleyici". Bütün HID cihazlarının önünde duruyor, kolu oyundan saklayabiliyor. Nefarius'un kendisi kaldırılmasını söylüyor (yerine HidHide çıktı) |
| **ViGEmBus 3 kopya** (ROOT\SYSTEM\0001, 0004, 0008), üçü de eski **1.17.333** | Aynı sanal kol veri yolundan 3 tane var. Sanal kol yuvaları karışıyor. Yeni sürüm 1.21.442 depoda duruyor ama kullanılmıyor |
| **Steam `steamxbox` alt filtresi** HIDClass ve XnaComposite'e takılı | "Xbox Extended Feature Support" sürücüsü. Taklit Xbox kollarında (Blitz 2 de öyle) oyunların kolu görmemesiyle biliniyor |
| GeniTech Virtual Gamepad, Feizhi (Flydigi) sanal klavye/fare, vJoy (bozuk) | Bunlar da sanal kol ya da giriş cihazı ekliyor. Yuva 0'ı kapıp sonra bırakabiliyorlar. Sabah Blitz 2'nin yuva 1'e düşmesinin olası sebebi |
| Steam çalışıyor (Steam Input) + Flydigi Space Station + JoyToKey kurulu | Aynı kolu 2-3 yazılım aynı anda yakalamaya çalışıyor |

### Kök nedenler
0. **Katmanlı sürücü çöplüğü:** HidGuardian kalıntısı, 3 ViGEmBus kopyası, steamxbox filtresi ve üretici servisleri aynı kolun önüne diziliyor. Hangisinin önce yüklendiğine göre kol "bugün var, yarın yok" oluyor.
1. **Yuva kayması:** Oyunlar kolu 4 XInput yuvasından okur. Birçoğu sadece yuva 0'a bakar. Kol, uyku veya yeniden bağlanma sonrası yuva 1-2-3'e düşünce oyun "kol yok" der.
2. **Oyun kolu yalnız açılışta arar:** Kablosuz alıcı uyuyup geri bağlanınca veya kol oyun açıldıktan sonra takılınca bazı oyunlar yakalayamaz.
3. **Kimliği bilinmeyen kollar:** 413D/37D7 gibi kimlikler SDL, Unity Rewired ve Unreal gibi motorların kol veritabanında yok. XInput dışı yoldan okuyan oyun bunları tanımaz ya da tuşları karışık eşler.
4. **Çift görünme:** Aynı kol hem XInput hem DirectInput olarak görünüyor. Oyun ikisini de okuyunca çift giriş oluyor ya da yanlış cihazı seçiyor.
5. **Hayalet kayıtlar ve eski joystick numaraları:** DirectInput sırası bozulmuş.
6. **Game Bar'ın çalışması yanıltıcı:** Game Bar kolu `Windows.Gaming.Input` üzerinden okur. Oyunlar ise XInput, DirectInput, SDL veya RawInput kullanır. Biri çalışırken diğeri çalışmayabilir.

---

## 2. Çözüm fikri: "tek sabit sanal kol"

```
 [Gerçek kollar: 413D, 37D7, Vader3, Pro...]
            │  (HidHide ile oyunlardan GİZLİ)
            ▼
   PadKöprü servisi (sadece o görür)
     - SDL2 ile okur (binlerce kol tanıdık)
     - tanımadığı kol için 30 sn eşleme sihirbazı
     - oyuna göre profil uygular
            │
            ▼
   ViGEmBus → SANAL Xbox 360 kolu (yuva 0, açılıştan itibaren hep takılı)
            │
            ▼
        [Oyunlar]  → her zaman aynı, standart, tek kolu görür
```

**Neden işe yarar:**
- Sanal kol **bilgisayar açılınca oluşur ve hiç çıkmaz.** Gerçek kol uyusa, değişse ya da başka porta takılsa bile oyun bunu fark etmez (sıcak değişim).
- Hep **yuva 0**'da durur → yuva kayması biter.
- Oyun sadece **gerçek Xbox 360 kimliğini** görür → bilinmeyen kimlik sorunu biter.
- Gerçek kollar gizli olduğu için → çift giriş biter.

---

## 3. Bileşenler

| # | Parça | Teknoloji | Görev |
|---|---|---|---|
| 1 | **Temizlik aracı** | PowerShell + `pnputil /remove-device` | Hayalet kol kayıtlarını, eski DirectInput joystick numaralarını ve bozuk vJoy'u temizler (önce yedek alır) |
| 2 | **Sürücüler** | ViGEmBus (var) + HidHide 1.5.x | Sanal kol + gerçek kolu gizleme |
| 3 | **Köprü servisi** | Python 3.11 + `pysdl2` (SDL2 kol veritabanı) + `vgamepad` (ViGEm) | Gerçek kolu okur, sanal kola yazar, 1 ms döngü, kol değişimini anında yakalar |
| 4 | **Oyun izleyici** | `psutil` işlem izleme + Steam/Epic/Xbox kütüphane taraması | Oyun açılınca profilini uygular |
| 5 | **Profiller** | `profiller/<oyun>.json` | Ölü bölge, tetik eşiği, tuş değişimi, "bu oyunda köprü kapalı" (kolu yerel destekleyen oyunlar için), X360 veya DS4 modu |
| 6 | **Tepsi arayüzü** | `pystray` | Aç/kapat, aktif oyun, aktif kol, sihirbaz |
| 7 | **Teşhis ekranı** | küçük yerel web sayfası | "Oyun neyi görüyor?": XInput yuvaları, DirectInput listesi, SDL listesi, HidHide durumu yan yana |
| 8 | **Otomatik başlatma** | Görev Zamanlayıcı (oturum açılışında, yönetici) | Servis oyunlardan önce ayağa kalksın |

### Oyunların otomatik alınması
- Steam: `libraryfolders.vdf` + `appmanifest_*.acf` → exe klasörleri
- Epic: `C:\ProgramData\Epic\EpicGamesLauncher\Data\Manifests\*.item`
- Xbox/Game Pass: `Get-AppxPackage` + `XboxGames` klasörü
- Bilinmeyen exe: tam ekran açılan ve GPU kullanan işlem → "Bu bir oyun mu?" bildirimi → bir tıkla listeye
- Yeni oyun ilk açıldığında varsayılan profil (standart Xbox 360) otomatik uygulanır.

---

## 4. Aşamalar

| Aşama | İş | Test / kabul ölçütü |
|---|---|---|
| **A0 — Temizlik** | 1) Sistem geri yükleme noktası + sürücü/kayıt yedeği 2) HidGuardian filtresini ve sürücüsünü kaldırma (Nefarius Legacinator veya elle) 3) Fazla ViGEmBus kopyalarını silme, tek ViGEmBus 1.21.442 bırakma 4) Steam "Xbox Extended Feature Support"u kapatma 5) vJoy ve GeniTech kaldırma (kullanılmıyorsa) 6) Hayalet kol kayıtları + joystick numaraları temizliği 7) Blitz 2: XInput modu (yeşil LED) + firmware kontrolü | Yeniden başlatma sonrası Blitz 2 yuva 0'da; sorunlu oyunlarda 3 gün boyunca algılanıyor |
| **A1 — Köprü çekirdeği** | HidHide kurulumu + SDL okuma → ViGEm sanal kol | Tek kol ile sorunlu oyun kolu görüyor; test sitesinde sadece 1 kol görünüyor |
| **A2 — Sıcak değişim** | Kol çıkar/tak, 413D ↔ 37D7 değiştir, uyku sonrası uyanma | Oyun açıkken kol değişiyor, oyun kesintisiz devam ediyor |
| **A3 — Oyun tanıma + profiller** | Kütüphane taraması, işlem izleyici, JSON profiller | Oyun açılınca doğru profil 1 sn içinde aktif |
| **A4 — Arayüz + teşhis + otomatik başlatma** | Tepsi, teşhis sayfası, eşleme sihirbazı | Yeniden başlatmadan sonra hiçbir şey yapmadan çalışıyor |
| **A5 — Çoklu oyuncu (opsiyonel)** | 2-4 gerçek kol → 2-4 sabit sanal kol, kol başına sabit oyuncu numarası | Her kol her gün aynı oyuncu numarası |

---

## 5. Riskler
- **ViGEmBus arşivlendi (2023)** ama Win 11'de çalışıyor. DS4Windows, DSX gibi araçlar hâlâ kullanıyor. Halefi çıkarsa tek dosya değişir.
- **Anti-cheat'li oyunlar** (ör. bazı online oyunlar) sanal kolu genelde kabul eder. HidHide ile gizleme sorun yaratırsa o oyunun profilinde köprü kapatılır.
- **Steam Input** açık olduğunda Steam kolu kendisi de sanallaştırır → çakışma olur. Steam oyunlarında profil "Steam Input kapalı" önerisi verecek.
- Temizlik aracı cihaz kaydı sildiği için önce `pnputil /enum-devices` yedeği alınacak.
