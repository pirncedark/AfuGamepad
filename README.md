# PadKöprü

Portable gamepad köprüsü. Kurulum yok, sistemde hiçbir ayar değiştirmez.
Klasörü istediğin yere kopyala, `PadKopru.exe`'yi aç → saat yanındaki tepsiye küçülür.

## Nasıl çalışır
1. Öndeki pencereyi izler. Steam/Epic kütüphanesindeki ya da tam ekran açılan bir program görünce **oyun** sayar ve `profiller\` altına profilini kendisi açar.
2. Oyunun profilindeki **moda** göre kolu oyuna iletir:

| Mod | Ne yapar | Ne zaman |
|---|---|---|
| Kapalı | Karışmaz, kol oyuna doğrudan gider | Kol zaten çalışıyorsa (varsayılan) |
| Sanal Xbox 360 | Gerçek Microsoft Xbox 360 kimliğiyle sanal kol takar | Oyun kolu hiç görmüyorsa ya da tuşları karışık eşliyorsa |
| Sanal DualShock 4 | Sanal PS4 kolu takar | Sadece PlayStation/DirectInput kolu tanıyan oyunlar |
| Klavye + fare | Kolu tuş basışına çevirir (WASD, fare) | Kol desteği olmayan oyunlar |

3. Oyun kapanınca sanal kol çıkarılır.

## Oyun içi kısayollar
**BACK (Select / View) basılı tutarken:**
- **RB** → sonraki şema, **LB** → önceki şema
- **Y** → modu değiştir (Kapalı → Xbox 360 → DS4 → Klavye)
- **START** → köprüyü durdur/başlat

Her değişimde ekranın üstünde kısa bir yazı çıkar, kol hafifçe titrer, seçim o oyunun profiline kaydedilir.

## Şemalar
Her profilde hazır üç şema var: **Varsayılan**, **Saldırılar tetikte (RB↔RT, LB↔LT)**, **Nintendo düzeni (A↔B, X↔Y)**.
Yeni şema eklemek için profil JSON'undaki `semalar` listesine ekle:
```json
{"ad": "Zıplama RB'de", "esle": {"A": "RB", "RB": "A"}}
```
Tuş adları: `A B X Y LB RB LT RT BACK START LS RS UP DOWN LEFT RIGHT GUIDE`

Hazır profiller: Dark Souls PTDE (Xbox 360 modunda gelir, oyun sadece XInput tanır), Dark Souls Remastered, Dark Souls II SotFS, Dark Souls III, Elden Ring, Sekiro, Lies of P, Nioh 2.

## Bilinmesi gerekenler
- **Sanal mod için ViGEmBus sürücüsü gerekir.** Bu bilgisayarda kurulu. Başka bilgisayarda yoksa sanal modlar hata verir, Kapalı ve Klavye modları yine çalışır.
- **Oyun kolu genelde açılışta arar.** Sanal moda oyun açıkken geçtiysen oyunu yeniden başlat. Profil kaydedildiği için bir sonraki açılışta sanal kol oyundan önce hazır olur.
- **Çift giriş:** Sanal modda gerçek kol da görünmeye devam eder (onu gizlemek sürücü ister). Oyun kolu zaten görüyorsa sanal moda gerek yok. Şema değişimi en temiz şekilde, gerçek kolu görmeyen oyunlarda çalışır.
- Birden fazla kol takılıysa **en son dokunduğun kol** kaynak olur.

## Geliştirme
```
python -m venv .venv
.venv\Scripts\pip install psutil pystray pillow pyinstaller
.venv\Scripts\python tests\test_motor.py   # sanal kolla uçtan uca test
.\build.ps1                                # dist\PadKopru\ portable klasörü
```
