"""Köprü motoru: fiziksel kolu okur, profili uygular, sanal kola / klavyeye yazar."""
import ctypes
import logging
import math
import queue
import threading
import time

from . import klavye, xinput
from .profiller import MOD_ADLARI, MODLAR
from .vigem import Bus, VigemError, VirtualDS4, VirtualX360

log = logging.getLogger("motor")

B = xinput.BUTTONS
TETIK_DIJITAL = 30  # tetik bu değerin üstündeyse "basılı" sayılır
KISAYOL_TUSU = B["BACK"]
KISAYOLLAR = {B["RB"]: "sema+", B["LB"]: "sema-", B["Y"]: "mod+", B["START"]: "durdur"}

BILINEN_KOLLAR = {(0x413D, 0x2104): "BigBig Won Blitz 2 TMR", (0x37D7, 0x2401): "Flydigi Vader 5 Pro",
                  (0x045E, 0x028E): "Xbox 360 uyumlu", (0x045E, 0x02FF): "Xbox One", (0x045E, 0x0B12): "Xbox Series"}


def kol_adi(vp):
    if not vp:
        return "?"
    return BILINEN_KOLLAR.get(vp, f"{vp[0]:04X}:{vp[1]:04X}")


def _olu_bolge(x, y, bolge):
    """Dairesel ölü bölge + yeniden ölçekleme. Girdi/çıktı -32768..32767."""
    nx, ny = x / 32767.0, y / 32767.0
    m = math.hypot(nx, ny)
    if m <= bolge:
        return 0, 0
    olcek = min(1.0, (m - bolge) / (1.0 - bolge)) / m
    c = lambda v: max(-32768, min(32767, int(v * olcek * 32767)))
    return c(nx), c(ny)


class Motor(threading.Thread):
    def __init__(self, depo, olay_kuyrugu):
        super().__init__(daemon=True, name="motor")
        self.depo = depo
        self.olaylar = olay_kuyrugu  # UI'ya giden (tur, veri)
        self.komutlar = queue.Queue()
        self.profil = None
        self.oyun_adi = None
        self.duraklat = False
        self.bus = None
        self.hedef = None  # VirtualX360 / VirtualDS4
        self.hedef_modu = "kapali"
        self.kaynak = None
        self._son_paket = {}
        self._kombo = False
        self._onceki_tus = 0
        self._basili_klavye = set()
        self._titresim = (0, 0)
        self._gonderilen_titresim = (0, 0)
        self._titresim_bitis = 0.0
        self._fare_artik = [0.0, 0.0]
        self._son_tur = time.perf_counter()
        self.canli = {"tuslar": [], "slot": None, "kol": None, "sanal_slot": None}
        self._calis = True

    # ---- dışarıdan çağrılır (thread-safe: kuyruk üzerinden) ----
    def oyun_degisti(self, profil, oyun_adi):
        self.komutlar.put(("oyun", (profil, oyun_adi)))

    def komut(self, ad, deger=None):
        self.komutlar.put((ad, deger))

    def durdur(self):
        self._calis = False

    # ---- iç ----
    def _bildir(self, metin):
        log.info(metin)
        self.olaylar.put(("bildirim", metin))

    def _istenen_mod(self):
        if self.duraklat or not self.profil:
            return "kapali"
        return self.profil.get("mod", "kapali")

    def _hedefi_ayarla(self):
        mod = self._istenen_mod()
        if mod == self.hedef_modu:
            return
        self._hedefi_kapat()
        if mod in ("x360", "ds4"):
            try:
                if self.bus is None:
                    self.bus = Bus()
                sinif = VirtualX360 if mod == "x360" else VirtualDS4
                self.hedef = sinif(self.bus, on_rumble=self._rumble)
            except (VigemError, OSError) as e:
                self._bildir(f"Sanal kol takılamadı: {e}")
                mod = "kapali"
        self.hedef_modu = mod
        self.olaylar.put(("durum", None))

    def _hedefi_kapat(self):
        for k in list(self._basili_klavye):
            klavye.key(k, False)
        self._basili_klavye.clear()
        if self.hedef:
            try:
                self.hedef.close()
            except OSError:
                pass
            self.hedef = None
        self.hedef_modu = "kapali"

    def _rumble(self, buyuk, kucuk):
        self._titresim = (buyuk, kucuk)

    def _komutlari_isle(self):
        while True:
            try:
                ad, deger = self.komutlar.get_nowait()
            except queue.Empty:
                return
            if ad == "oyun":
                self.profil, self.oyun_adi = deger
                if self.profil:
                    self._bildir(f"🎮 {self.oyun_adi} — {MOD_ADLARI[self.profil['mod']]} · {self._sema()['ad']}")
            elif ad == "mod" and self.profil:
                self.profil["mod"] = deger
                self.depo.kaydet(self.profil)
            elif ad == "sema" and self.profil:
                self.profil["aktif_sema"] = deger % len(self.profil["semalar"])
                self.depo.kaydet(self.profil)
            elif ad == "profil_guncel":
                pass  # profil nesnesi yerinde değişti; sadece hedefi yeniden değerlendir
            elif ad == "duraklat":
                self.duraklat = bool(deger)
            self.olaylar.put(("durum", None))

    def _sema(self):
        s = self.profil["semalar"]
        return s[self.profil.get("aktif_sema", 0) % len(s)]

    def _kisayol(self, eylem):
        if eylem == "durdur":
            self.duraklat = not self.duraklat
            self._bildir("⏸ Köprü durduruldu" if self.duraklat else "▶ Köprü açık")
        elif not self.profil:
            self._bildir("Aktif oyun yok — kısayol oyun içinde çalışır")
        elif eylem in ("sema+", "sema-"):
            n = len(self.profil["semalar"])
            self.profil["aktif_sema"] = (self.profil.get("aktif_sema", 0) + (1 if eylem == "sema+" else -1)) % n
            self.depo.kaydet(self.profil)
            self._bildir(f"Şema: {self._sema()['ad']}")
        elif eylem == "mod+":
            i = MODLAR.index(self.profil.get("mod", "kapali"))
            self.profil["mod"] = MODLAR[(i + 1) % len(MODLAR)]
            self.depo.kaydet(self.profil)
            ek = " (oyun kolu görmezse oyunu yeniden başlat)" if self.profil["mod"] in ("x360", "ds4") else ""
            self._bildir(f"Mod: {MOD_ADLARI[self.profil['mod']]}{ek}")
        self.olaylar.put(("durum", None))

    def _kaynak_sec(self):
        """Fiziksel kolları bul; en son dokunulanı kaynak yap (birden çok kol desteği)."""
        sanal = self.hedef.user_index() if isinstance(self.hedef, VirtualX360) else None
        self.canli["sanal_slot"] = sanal
        if isinstance(self.hedef, VirtualX360) and sanal is None:
            return  # sanal kolun yuvası henüz belli değil; kendini kaynak sanmasın
        en_iyi = None
        for s in range(4):
            if s == sanal:
                continue
            st = xinput.get_state(s)
            if st is None:
                self._son_paket.pop(s, None)
                continue
            paket, g = st
            kullaniliyor = g.wButtons or g.bLeftTrigger > TETIK_DIJITAL or g.bRightTrigger > TETIK_DIJITAL or \
                max(abs(g.sThumbLX), abs(g.sThumbLY), abs(g.sThumbRX), abs(g.sThumbRY)) > 12000
            if s != self.kaynak and s in self._son_paket and self._son_paket[s] != paket and kullaniliyor:
                en_iyi = s  # başka bir kola dokunuldu → ona geç
            self._son_paket[s] = paket
            if self.kaynak is None and en_iyi is None:
                en_iyi = s
        if en_iyi is not None and en_iyi != self.kaynak:
            if self.kaynak is not None:
                xinput.set_rumble(self.kaynak, 0, 0)
            self.kaynak = en_iyi
            self.canli["kol"] = kol_adi(xinput.vid_pid(en_iyi))
            self._bildir(f"Kol: {self.canli['kol']} (yuva {en_iyi})")
        if self.kaynak is not None and self.kaynak not in self._son_paket:
            self._bildir(f"Kol ayrıldı: {self.canli['kol']}")
            self.kaynak = None
            self.canli["kol"] = None
        self.canli["slot"] = self.kaynak

    def run(self):
        ctypes.WinDLL("winmm").timeBeginPeriod(1)
        son_tarama = 0.0
        try:
            while self._calis:
                self._komutlari_isle()
                self._hedefi_ayarla()
                simdi = time.perf_counter()
                if simdi - son_tarama > 0.25:
                    self._kaynak_sec()
                    son_tarama = simdi
                self._tur()
                time.sleep(0.001)
        finally:
            self._hedefi_kapat()
            if self.bus:
                self.bus.close()
            ctypes.WinDLL("winmm").timeEndPeriod(1)

    def _tur(self):
        st = xinput.get_state(self.kaynak) if self.kaynak is not None else None
        if st is None:
            if self.hedef:
                self.hedef.send(0, 0, 0, 0, 0, 0, 0)
            return
        paket, g = st
        if self._son_paket.get(self.kaynak) != paket:
            self._son_paket[self.kaynak] = paket
        tuslar = g.wButtons

        # --- kısayollar: BACK basılıyken RB/LB/Y/START ---
        yeni = tuslar & ~self._onceki_tus
        self._onceki_tus = tuslar
        if tuslar & KISAYOL_TUSU:
            for bit, eylem in KISAYOLLAR.items():
                if yeni & bit:
                    self._kombo = True
                    self._kisayol(eylem)
                    xinput.set_rumble(self.kaynak, 0, 120)
                    self._titresim_bitis = time.perf_counter() + 0.12
        elif self._kombo:
            self._kombo = False
        if self._titresim_bitis:
            if time.perf_counter() > self._titresim_bitis:
                self._titresim_bitis = 0
                self._gonderilen_titresim = None
        elif self._titresim != self._gonderilen_titresim:
            self._gonderilen_titresim = self._titresim
            xinput.set_rumble(self.kaynak, *self._titresim)

        self.canli["tuslar"] = [ad for ad, bit in B.items() if tuslar & bit] + \
            (["LT"] if g.bLeftTrigger > TETIK_DIJITAL else []) + (["RT"] if g.bRightTrigger > TETIK_DIJITAL else [])

        if not self.hedef and self.hedef_modu != "klavye":
            return
        if self._kombo:
            tuslar &= ~(KISAYOL_TUSU | sum(KISAYOLLAR))

        p = self.profil
        ob = p.get("olu_bolge", {})
        lx, ly = _olu_bolge(g.sThumbLX, g.sThumbLY, ob.get("sol", 0.1))
        rx, ry = _olu_bolge(g.sThumbRX, g.sThumbRY, ob.get("sag", 0.1))
        tob = int(p.get("tetik_olu_bolge", 0) * 255)
        lt = g.bLeftTrigger if g.bLeftTrigger > tob else 0
        rt = g.bRightTrigger if g.bRightTrigger > tob else 0

        # --- şema (yeniden eşleme) ---
        esle = self._sema().get("esle", {})
        if esle:
            giris = {ad: 255 if tuslar & bit else 0 for ad, bit in B.items()}
            giris["LT"], giris["RT"] = lt, rt
            cikis = dict.fromkeys(giris, 0)
            for ad, deger in giris.items():
                hedef = esle.get(ad, ad)
                if hedef in cikis:
                    cikis[hedef] = max(cikis[hedef], deger)
            tuslar = 0
            for ad, bit in B.items():
                if cikis[ad] > TETIK_DIJITAL:
                    tuslar |= bit
            lt, rt = cikis["LT"], cikis["RT"]

        if self.hedef:
            self.hedef.send(tuslar, lt, rt, lx, ly, rx, ry)
        elif self.hedef_modu == "klavye":
            self._klavye(p.get("klavye", {}), tuslar, lt, rt, lx, ly, rx, ry)

    def _klavye(self, ayar, tuslar, lt, rt, lx, ly, rx, ry):
        istenen = set()
        for ad, tus in ayar.get("tuslar", {}).items():
            if ad in B and tuslar & B[ad]:
                istenen.add(tus)
            elif ad == "LT" and lt > TETIK_DIJITAL or ad == "RT" and rt > TETIK_DIJITAL:
                istenen.add(tus)
        sc = ayar.get("sol_cubuk", {})
        esik = 16000
        for kosul, yon in ((ly > esik, "yukari"), (ly < -esik, "asagi"), (lx < -esik, "sol"), (lx > esik, "sag")):
            if kosul and yon in sc:
                istenen.add(sc[yon])
        for k in istenen - self._basili_klavye:
            klavye.key(k, True)
        for k in self._basili_klavye - istenen:
            klavye.key(k, False)
        self._basili_klavye = istenen
        hiz = ayar.get("sag_cubuk_fare", 0)  # tam itişte piksel/saniye
        simdi = time.perf_counter()
        dt, self._son_tur = min(0.05, simdi - self._son_tur), simdi
        if hiz:
            fx, fy = rx / 32767.0, ry / 32767.0
            self._fare_artik[0] += math.copysign(fx * fx, fx) * hiz * dt
            self._fare_artik[1] -= math.copysign(fy * fy, fy) * hiz * dt
            dx, dy = int(self._fare_artik[0]), int(self._fare_artik[1])
            self._fare_artik[0] -= dx
            self._fare_artik[1] -= dy
            klavye.mouse_move(dx, dy)
