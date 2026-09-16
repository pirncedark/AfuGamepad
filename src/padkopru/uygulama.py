"""PadKöprü — tepsi uygulaması, bildirim balonu, ayar penceresi."""
import ctypes
import logging
import os
import queue
import sys
import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk

import psutil
import pystray
from PIL import Image, ImageDraw

from . import oyunlar
from .motor import Motor
from .profiller import MOD_ADLARI, MODLAR, Depo

SURUM = "0.1.0"
KISAYOL_METNI = ("Oyun içi kısayollar (BACK/Select basılı tutarken):\n"
                 "  RB → sonraki şema     LB → önceki şema\n"
                 "  Y  → modu değiştir     START → köprüyü durdur/başlat")


def kok_klasor():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def simge(renk="#3ddc84"):
    im = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((4, 18, 60, 50), 14, fill="#1e1f24")
    d.ellipse((12, 26, 24, 38), fill=renk)
    d.ellipse((42, 24, 50, 32), fill="#e5e7eb")
    d.ellipse((48, 32, 56, 40), fill="#e5e7eb")
    return im


class OyunIzleyici(threading.Thread):
    """Öndeki pencereyi izler; oyunsa profilini bulur/oluşturur ve motora bildirir."""

    def __init__(self, depo, motor):
        super().__init__(daemon=True, name="izleyici")
        self.depo, self.motor = depo, motor
        self.kutuphaneler = {}
        self.aktif = None  # (exe, pid)
        self.son_tarama = 0

    def run(self):
        while True:
            try:
                self._tur()
            except Exception:  # izleyici asla ölmesin
                logging.exception("izleyici")
            time.sleep(1.0)

    def _tur(self):
        if time.time() - self.son_tarama > 600:
            self.kutuphaneler = oyunlar.tum_kutuphaneler()
            self.son_tarama = time.time()
            logging.info("kütüphane: %d oyun klasörü", len(self.kutuphaneler))
        on = oyunlar.on_pencere()
        if on:
            exe, yol, tam = on
            profil = self.depo.bul(exe)
            ad = profil["ad"] if profil else oyunlar.oyun_mu(exe, yol, tam, self.kutuphaneler)
            if ad and (not self.aktif or self.aktif[0] != exe):
                profil = profil or self.depo.olustur(ad, exe)
                pid = next((p.pid for p in psutil.process_iter(["name"]) if (p.info["name"] or "").lower() == exe), None)
                self.aktif = (exe, pid)
                self.motor.oyun_degisti(profil, profil["ad"])
                return
        # oyun penceresi önde değil: oyun kapandıysa bırak (alt-tab'da profili koru)
        if self.aktif and (self.aktif[1] is None or not psutil.pid_exists(self.aktif[1])):
            logging.info("oyun kapandı: %s", self.aktif[0])
            self.aktif = None
            self.motor.oyun_degisti(None, None)


class Uygulama:
    def __init__(self):
        self.kok = kok_klasor()
        logging.basicConfig(filename=os.path.join(self.kok, "padkopru.log"), level=logging.INFO,
                            format="%(asctime)s %(name)s %(message)s", encoding="utf-8")
        self.depo = Depo(self.kok)
        self.olaylar = queue.Queue()
        self.motor = Motor(self.depo, self.olaylar)
        self.izleyici = OyunIzleyici(self.depo, self.motor)

        self.root = tk.Tk()
        self.root.withdraw()
        self.root.title(f"PadKöprü {SURUM}")
        self.root.protocol("WM_DELETE_WINDOW", self.root.withdraw)
        self._toast = None
        self._arayuz()

        self.tepsi = pystray.Icon("PadKopru", simge(), "PadKöprü", menu=pystray.Menu(
            pystray.MenuItem("Göster", lambda: self.root.after(0, self.goster), default=True),
            pystray.MenuItem("Köprüyü durdur", lambda: self.motor.komut("duraklat", not self.motor.duraklat),
                             checked=lambda i: self.motor.duraklat),
            pystray.MenuItem("Profiller klasörü", lambda: os.startfile(self.depo.klasor)),
            pystray.MenuItem("Çıkış", lambda: self.root.after(0, self.cikis)),
        ))

    # ---------- pencere ----------
    def _arayuz(self):
        r = self.root
        r.geometry("540x620")
        r.minsize(480, 580)
        stil = ttk.Style()
        stil.configure("Baslik.TLabel", font=("Segoe UI Semibold", 11))
        cer = ttk.Frame(r, padding=12)
        cer.pack(fill="both", expand=True)

        ttk.Label(cer, text="Şu an", style="Baslik.TLabel").pack(anchor="w")
        self.lbl_durum = ttk.Label(cer, text="", justify="left", font=("Segoe UI", 10))
        self.lbl_durum.pack(anchor="w", pady=(2, 8))
        self.lbl_tuslar = ttk.Label(cer, text="", foreground="#2563eb", font=("Consolas", 10))
        self.lbl_tuslar.pack(anchor="w", pady=(0, 10))

        ttk.Label(cer, text="Profiller", style="Baslik.TLabel").pack(anchor="w")
        self.liste = ttk.Treeview(cer, columns=("mod", "sema"), height=8, selectmode="browse")
        self.liste.heading("#0", text="Oyun")
        self.liste.heading("mod", text="Mod")
        self.liste.heading("sema", text="Şema")
        self.liste.column("#0", width=200)
        self.liste.column("mod", width=130)
        self.liste.column("sema", width=150)
        self.liste.pack(fill="both", expand=True, pady=4)
        self.liste.bind("<<TreeviewSelect>>", lambda e: self._secimi_goster())

        duz = ttk.Frame(cer)
        duz.pack(fill="x", pady=6)
        ttk.Label(duz, text="Mod").grid(row=0, column=0, sticky="w")
        self.cb_mod = ttk.Combobox(duz, state="readonly", values=[MOD_ADLARI[m] for m in MODLAR], width=22)
        self.cb_mod.grid(row=0, column=1, padx=6, sticky="w")
        self.cb_mod.bind("<<ComboboxSelected>>", lambda e: self._duzenle())
        ttk.Label(duz, text="Şema").grid(row=1, column=0, sticky="w", pady=4)
        self.cb_sema = ttk.Combobox(duz, state="readonly", width=34)
        self.cb_sema.grid(row=1, column=1, padx=6, sticky="w")
        self.cb_sema.bind("<<ComboboxSelected>>", lambda e: self._duzenle())
        ttk.Label(duz, text="Çubuk ölü bölge %").grid(row=2, column=0, sticky="w")
        self.sp_olu = ttk.Spinbox(duz, from_=0, to=40, width=5, command=self._duzenle)
        self.sp_olu.grid(row=2, column=1, padx=6, sticky="w")

        alt = ttk.Frame(cer)
        alt.pack(fill="x", pady=(8, 0))
        ttk.Button(alt, text="Profiller klasörü", command=lambda: os.startfile(self.depo.klasor)).pack(side="left")
        ttk.Button(alt, text="Yeniden yükle", command=self._yeniden_yukle).pack(side="left", padx=6)
        ttk.Label(cer, text=KISAYOL_METNI, foreground="#6b7280", justify="left").pack(anchor="w", pady=(10, 0))

    def _profil_listesi(self):
        tekil = {}
        for p in self.depo.profiller.values():
            tekil[p["exe"][0]] = p
        return sorted(tekil.values(), key=lambda p: p["ad"].lower())

    def _listeyi_yenile(self):
        secili = self.liste.selection()
        self.liste.delete(*self.liste.get_children())
        for p in self._profil_listesi():
            sema = p["semalar"][p.get("aktif_sema", 0) % len(p["semalar"])]["ad"]
            self.liste.insert("", "end", iid=p["exe"][0], text=p["ad"], values=(MOD_ADLARI[p["mod"]], sema))
        if secili and self.liste.exists(secili[0]):
            self.liste.selection_set(secili[0])

    def _secili(self):
        s = self.liste.selection()
        return self.depo.bul(s[0]) if s else None

    def _secimi_goster(self):
        p = self._secili()
        if not p:
            return
        self._guncelleniyor = True
        self.cb_mod.set(MOD_ADLARI[p["mod"]])
        self.cb_sema["values"] = [s["ad"] for s in p["semalar"]]
        self.cb_sema.current(p.get("aktif_sema", 0) % len(p["semalar"]))
        self.sp_olu.set(int(round(p.get("olu_bolge", {}).get("sol", 0.1) * 100)))
        self._guncelleniyor = False

    def _duzenle(self):
        p = self._secili()
        if not p or getattr(self, "_guncelleniyor", False):
            return
        p["mod"] = MODLAR[[MOD_ADLARI[m] for m in MODLAR].index(self.cb_mod.get())]
        p["aktif_sema"] = max(0, self.cb_sema.current())
        try:
            olu = max(0, min(40, int(self.sp_olu.get()))) / 100
            p["olu_bolge"] = {"sol": olu, "sag": olu}
        except ValueError:
            pass
        self.depo.kaydet(p)
        self.motor.komut("profil_guncel")
        self._listeyi_yenile()

    def _yeniden_yukle(self):
        self.depo.yukle()
        aktif = self.izleyici.aktif
        if aktif:
            p = self.depo.bul(aktif[0])
            self.motor.oyun_degisti(p, p["ad"] if p else None)
        self._listeyi_yenile()

    def goster(self):
        self._listeyi_yenile()
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    # ---------- bildirim balonu ----------
    def toast(self, metin):
        if self._toast:
            self._toast.destroy()
        t = tk.Toplevel(self.root)
        t.overrideredirect(True)
        t.attributes("-topmost", True)
        t.attributes("-alpha", 0.92)
        t.configure(bg="#111318")
        tk.Label(t, text=metin, bg="#111318", fg="#f3f4f6", font=("Segoe UI Semibold", 12),
                 padx=18, pady=10).pack()
        t.update_idletasks()
        g = t.winfo_width()
        x = (t.winfo_screenwidth() - g) // 2
        t.geometry(f"+{x}+{int(t.winfo_screenheight() * 0.08)}")
        # tıklamaları oyuna geçir (WS_EX_TRANSPARENT | WS_EX_LAYERED), odak çalma
        hwnd = ctypes.windll.user32.GetParent(t.winfo_id())
        stil = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
        ctypes.windll.user32.SetWindowLongW(hwnd, -20, stil | 0x20 | 0x80000 | 0x08000000)
        self._toast = t
        t.after(2200, lambda: (t.destroy(), setattr(self, "_toast", None) if self._toast is t else None))

    # ---------- döngü ----------
    def _olaylari_isle(self):
        try:
            while True:
                tur, veri = self.olaylar.get_nowait()
                if tur == "bildirim":
                    self.toast(veri)
                    self.tepsi.title = f"PadKöprü — {veri}"[:127]
                elif tur == "durum" and self.root.state() == "normal":
                    self._listeyi_yenile()
        except queue.Empty:
            pass
        m = self.motor
        c = m.canli
        oyun = m.oyun_adi or "— (oyun algılanmadı)"
        mod = MOD_ADLARI[m.hedef_modu] + (" · DURAKLATILDI" if m.duraklat else "")
        self.lbl_durum.config(text=(
            f"Oyun: {oyun}\nMod: {mod}\n"
            f"Kol: {c['kol'] or 'bağlı değil'}" + (f" (XInput yuva {c['slot']})" if c['slot'] is not None else "") +
            (f"\nSanal kol yuvası: {c['sanal_slot']}" if c["sanal_slot"] is not None else "")))
        self.lbl_tuslar.config(text="Basılı: " + (" ".join(c["tuslar"]) or "-"))
        self.root.after(50, self._olaylari_isle)

    def cikis(self):
        self.motor.durdur()
        self.motor.join(timeout=2)
        self.tepsi.stop()
        self.root.destroy()

    def calistir(self):
        self.motor.start()
        self.izleyici.start()
        self.tepsi.run_detached()
        self.root.after(50, self._olaylari_isle)
        self.root.after(300, lambda: self.toast("PadKöprü çalışıyor — tepside"))
        self.root.mainloop()


def tek_ornek():
    ctypes.windll.kernel32.CreateMutexW(None, False, "Local\\PadKopruTekOrnek")
    return ctypes.windll.kernel32.GetLastError() != 183  # ERROR_ALREADY_EXISTS


def main():
    if not tek_ornek():
        ctypes.windll.user32.MessageBoxW(None, "PadKöprü zaten çalışıyor (saat yanındaki simgeye bak).", "PadKöprü", 0x40)
        return
    try:
        Uygulama().calistir()
    except Exception as e:
        logging.exception("çöktü")
        messagebox.showerror("PadKöprü", f"Beklenmeyen hata:\n{e}")


if __name__ == "__main__":
    main()
