"""Motor uçtan uca testi: sahte fiziksel kol → motor → gerçek sanal kol → XInput'tan geri okuma."""
import os, queue, sys, tempfile, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from padkopru import xinput, motor as motor_mod, oyunlar
from padkopru.profiller import Depo

gercek = xinput.get_state
SAHTE_SLOT = 3
sahte = {"paket": 1, "g": xinput.GAMEPAD(0, 0, 0, 0, 0, 0, 0)}
def get_state(slot):
    if slot == SAHTE_SLOT:
        return sahte["paket"], sahte["g"]
    if slot in (0, 2):  # testte gerçek fiziksel kolları yok say
        return None
    return gercek(slot)
xinput.get_state = get_state
xinput.set_rumble = lambda *a: None
xinput.vid_pid = lambda s: (0x413D, 0x2104)

def bas(buttons=0, lt=0, rt=0, lx=0):
    sahte["paket"] += 1
    sahte["g"] = xinput.GAMEPAD(buttons, lt, rt, lx, 0, 0, 0)
    time.sleep(0.08)

def sanal_oku(m):
    ui = m.hedef.user_index()
    return gercek(ui)[1]

tmp = tempfile.mkdtemp()
depo = Depo(tmp)
ds3 = depo.bul("DarkSoulsIII.exe")
assert ds3 and ds3["mod"] == "kapali", "hazır profil yok"
ds3["mod"] = "x360"
olay = queue.Queue()
m = motor_mod.Motor(depo, olay)
m.start()
m.oyun_degisti(ds3, ds3["ad"])
time.sleep(1.5)
assert m.hedef is not None and m.hedef.user_index() is not None, "sanal kol takılmadı"
print("sanal yuva:", m.hedef.user_index(), "kaynak:", m.kaynak, "kol:", m.canli["kol"])

bas(xinput.BUTTONS["A"], rt=0, lx=20000)
g = sanal_oku(m); print("varsayılan A + LX:", hex(g.wButtons), g.sThumbLX)
assert g.wButtons & 0x1000 and g.sThumbLX > 0

bas(0, lx=2000)  # ölü bölge içinde
g = sanal_oku(m); assert g.sThumbLX == 0, g.sThumbLX; print("ölü bölge OK")

# kısayol: BACK basılı + RB → sonraki şema (tetik değişimi)
bas(xinput.BUTTONS["BACK"]); bas(xinput.BUTTONS["BACK"] | xinput.BUTTONS["RB"])
g = sanal_oku(m); print("kombo sırasında sanal:", hex(g.wButtons)); assert g.wButtons == 0, "kombo tuşları oyuna sızdı"
bas(0)
print("şema:", m._sema()["ad"]); assert m.profil["aktif_sema"] == 1

bas(xinput.BUTTONS["RB"])
g = sanal_oku(m); print("RB → RT:", hex(g.wButtons), g.bRightTrigger); assert g.bRightTrigger == 255 and not g.wButtons & 0x0200
bas(0, rt=200)
g = sanal_oku(m); print("RT → RB:", hex(g.wButtons)); assert g.wButtons & 0x0200 and g.bRightTrigger == 0
bas(0)

# kaydedildi mi
depo2 = Depo(tmp); assert depo2.bul("darksoulsiii.exe")["aktif_sema"] == 1; print("profil diske kaydedildi")

# BACK+Y → mod değişimi (x360 → ds4)
bas(xinput.BUTTONS["BACK"]); bas(xinput.BUTTONS["BACK"] | xinput.BUTTONS["Y"]); bas(0)
time.sleep(0.5); print("mod:", m.hedef_modu); assert m.hedef_modu == "ds4"

m.oyun_degisti(None, None); time.sleep(0.5); assert m.hedef is None; print("oyun kapandı → sanal kol çıktı")
m.durdur(); m.join(2)
bildirimler = []
while not olay.empty():
    t, v = olay.get()
    if t == "bildirim": bildirimler.append(v)
print("bildirimler:", bildirimler)
k = oyunlar.tum_kutuphaneler(); print("kütüphane klasörü:", len(k), list(k.values())[:5])
print("TÜM TESTLER GEÇTİ")
