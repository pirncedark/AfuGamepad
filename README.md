# AfuGamepad (PadKöprü)

**English** | [Türkçe](#padköprü-türkçe)

Portable gamepad bridge for Windows. No installation, changes nothing on your system.
Copy the folder anywhere, run `PadKopru.exe` → it minimizes to the system tray.

## How it works
1. Watches the foreground window. When it sees a program from your Steam/Epic library or one running fullscreen, it counts it as a **game** and creates a profile for it under `profiller\`.
2. Depending on the **mode** in that game's profile, it forwards your controller to the game:

| Mode | What it does | When to use |
|---|---|---|
| Off | Stays out of the way, controller goes straight to the game | When the controller already works (default) |
| Virtual Xbox 360 | Plugs in a virtual pad with a genuine Microsoft Xbox 360 identity | When the game doesn't see the controller at all, or maps buttons wrong |
| Virtual DualShock 4 | Plugs in a virtual PS4 pad | Only for games that recognize PlayStation/DirectInput pads |
| Keyboard + mouse | Turns the controller into key presses (WASD, mouse) | Games with no controller support |

3. The virtual pad is unplugged when the game closes.

## In-game shortcuts
**While holding BACK (Select / View):**
- **RB** → next scheme, **LB** → previous scheme
- **Y** → change mode (Off → Xbox 360 → DS4 → Keyboard)
- **START** → stop/start the bridge

On every change a short overlay appears at the top of the screen, the pad rumbles briefly, and the choice is saved to that game's profile.

## Schemes
Every profile ships with three schemes: **Default**, **Attacks on bumpers (RB↔RT, LB↔LT)**, **Nintendo layout (A↔B, X↔Y)**.
To add a scheme, append to the `semalar` list in the profile JSON:
```json
{"ad": "Jump on RB", "esle": {"A": "RB", "RB": "A"}}
```
Button names: `A B X Y LB RB LT RT BACK START LS RS UP DOWN LEFT RIGHT GUIDE`

Bundled profiles: Dark Souls PTDE (ships in Xbox 360 mode, the game only recognizes XInput), Dark Souls Remastered, Dark Souls II SotFS, Dark Souls III, Elden Ring, Sekiro, Lies of P, Nioh 2.

## Good to know
- **Virtual modes need the ViGEmBus driver.** Without it the virtual modes error out; Off and Keyboard modes still work.
- **Games usually look for a pad at startup.** If you switch to a virtual mode while the game is running, restart the game. Since the profile is saved, the virtual pad will be ready before the game next time.
- **Double input:** in virtual mode your real controller stays visible too (hiding it would require a driver). If the game already sees your controller, you don't need virtual mode. Scheme remapping works most cleanly in games that don't see the real pad.
- With more than one controller plugged in, the **last one you touched** becomes the source.

## Development
```
python -m venv .venv
.venv\Scripts\pip install psutil pystray pillow pyinstaller
.venv\Scripts\python tests\test_motor.py   # end-to-end test with a virtual pad
.\build.ps1                                # portable folder in dist\PadKopru\
```

---

# PadKöprü (Türkçe)

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
