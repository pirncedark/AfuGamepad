"""Oyun profilleri: JSON dosyaları, hazır şablonlar, otomatik oluşturma."""
import json
import os
import re

MODLAR = ["kapali", "x360", "ds4", "klavye"]
MOD_ADLARI = {"kapali": "Kapalı (kol doğrudan)", "x360": "Sanal Xbox 360", "ds4": "Sanal DualShock 4",
              "klavye": "Klavye + fare"}

GIRISLER = ["A", "B", "X", "Y", "LB", "RB", "LT", "RT", "BACK", "START", "LS", "RS",
            "UP", "DOWN", "LEFT", "RIGHT", "GUIDE"]

SEMA_TETIK_DEGIS = {"ad": "Saldırılar tetikte (RB↔RT, LB↔LT)",
                    "esle": {"RB": "RT", "RT": "RB", "LB": "LT", "LT": "LB"}}
SEMA_NINTENDO = {"ad": "Nintendo düzeni (A↔B, X↔Y)", "esle": {"A": "B", "B": "A", "X": "Y", "Y": "X"}}
SEMA_VARSAYILAN = {"ad": "Varsayılan", "esle": {}}

KLAVYE_WASD = {
    "sol_cubuk": {"yukari": "w", "asagi": "s", "sol": "a", "sag": "d"},
    "sag_cubuk_fare": 1500,
    "tuslar": {"A": "space", "B": "lctrl", "X": "e", "Y": "r", "LB": "q", "RB": "mouse2", "LT": "lshift",
               "RT": "mouse1", "BACK": "tab", "START": "esc", "LS": "lshift", "RS": "mouse3",
               "UP": "1", "DOWN": "2", "LEFT": "3", "RIGHT": "4"},
}


def varsayilan_profil(ad, exe):
    return {
        "ad": ad, "exe": [exe.lower()], "mod": "kapali", "aktif_sema": 0,
        "olu_bolge": {"sol": 0.10, "sag": 0.10}, "tetik_olu_bolge": 0.0,
        "semalar": [SEMA_VARSAYILAN, SEMA_TETIK_DEGIS, SEMA_NINTENDO],
        "klavye": KLAVYE_WASD,
    }


# Popüler oyunlar için hazır profiller. Oyunların hepsi kolu kendisi destekliyor;
# mod "kapali" başlar, kol görünmezse oyun içinden BACK+Y ile mod değiştirilir.
HAZIR = [
    ("Dark Souls: Prepare to Die", "darksouls.exe", "x360"),   # PTDE sadece XInput tanır
    ("Dark Souls Remastered", "darksoulsremastered.exe", "kapali"),
    ("Dark Souls II: Scholar of the First Sin", "darksoulsii.exe", "kapali"),
    ("Dark Souls III", "darksoulsiii.exe", "kapali"),
    ("Elden Ring", "eldenring.exe", "kapali"),
    ("Sekiro: Shadows Die Twice", "sekiro.exe", "kapali"),
    ("Lies of P", "lop-win64-shipping.exe", "kapali"),
    ("Nioh 2", "nioh2.exe", "kapali"),
]


def _dosya_adi(exe):
    return re.sub(r"[^a-z0-9._-]", "_", exe.lower()) + ".json"


class Depo:
    def __init__(self, kok):
        self.klasor = os.path.join(kok, "profiller")
        os.makedirs(self.klasor, exist_ok=True)
        self.profiller = {}  # exe -> profil
        self._hazirlari_yaz()
        self.yukle()

    def _hazirlari_yaz(self):
        for ad, exe, mod in HAZIR:
            yol = os.path.join(self.klasor, _dosya_adi(exe))
            if not os.path.exists(yol):
                p = varsayilan_profil(ad, exe)
                p["mod"] = mod
                self._yaz(yol, p)

    def _yaz(self, yol, p):
        tmp = yol + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(p, f, ensure_ascii=False, indent=2)
        os.replace(tmp, yol)

    def yukle(self):
        self.profiller = {}
        for ad in os.listdir(self.klasor):
            if not ad.endswith(".json"):
                continue
            try:
                with open(os.path.join(self.klasor, ad), encoding="utf-8") as f:
                    p = json.load(f)
            except (OSError, ValueError):
                continue
            for exe in p.get("exe", []):
                self.profiller[exe.lower()] = p

    def bul(self, exe):
        return self.profiller.get(exe.lower())

    def olustur(self, ad, exe):
        p = self.bul(exe)
        if p:
            return p
        p = varsayilan_profil(ad, exe)
        self.kaydet(p)
        return p

    def kaydet(self, p):
        self._yaz(os.path.join(self.klasor, _dosya_adi(p["exe"][0])), p)
        for exe in p["exe"]:
            self.profiller[exe.lower()] = p
