# AfuGamepad (PadKöprü) — Durum

Son güncelleme: 2026-09-16 · Sürüm 0.1.0

## Kural
**Sisteme dokunma.** Sürücü kurma/kaldırma, kayıt defteri temizliği yok. Her şey portable programın içinde kalacak.

## Bitti
- XInput okuma (ctypes, Guide tuşu + VID/PID dahil)
- ViGEmClient.dll ile sanal Xbox 360 / DualShock 4 (sistemde kurulu ViGEmBus'u kullanır), oyundan gelen titreşimi gerçek kola iletme
- Klavye + fare modu (SendInput, tarama kodu)
- Oyun algılama: öndeki pencere + Steam/Epic kütüphanesi + tam ekran → profili otomatik açma
- JSON profiller + şemalar (tuş değişimi), hazır Souls profilleri
- Oyun içi kısayollar: BACK + RB/LB/Y/START, ekranda bildirim + titreşim
- Birden çok kol: en son dokunulan kol kaynak olur
- Tepsi simgesi + ayar penceresi, tek örnek kilidi, `padkopru.log`
- `tests/test_motor.py` uçtan uca test (geçiyor), `build.ps1` → `dist\PadKopru\` portable

## Test bekleyen (gerçek oyunda)
- [ ] Blitz 2 TMR ile kolu görmeyen oyunda "Sanal Xbox 360" modu
- [ ] Dark Souls serisinde şema değişimi
- [ ] Klavye modu (gerçek SendInput hiç denenmedi)
- [ ] Kol değiştirme (Blitz 2 ↔ Vader 5 Pro) oyun açıkken
- [ ] Tam ekran (exclusive) oyunda bildirim balonunun görünmesi

## Bilinen sınırlar / sonraki fikirler
- Sanal modda gerçek kol da görünür (gizlemek sürücü ister) → çift giriş olabilir
- Sadece XInput kollar okunuyor; DirectInput/HID kol desteği (SDL veya winmm) sonra eklenecek
- Oyuna özel klavye düzenleri (Souls vb.) yok
- Ayar penceresinden şema düzenleme yok (şimdilik JSON)

## Sistem tespitleri (değiştirilmedi)
- Kollar: BigBig Won Blitz 2 TMR `413D:2104` (sorunlu), Flydigi Vader 5 Pro `37D7:2401`
- HIDClass'ta 2× HidGuardian UpperFilter kalıntısı, 3× ViGEmBus 1.17.333, `steamxbox` alt filtresi, GeniTech sanal kol, bozuk vJoy
- Ayrıntı: `docs/PLAN.md`
