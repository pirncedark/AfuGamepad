"""ViGEmClient.dll üzerinden sanal Xbox 360 / DualShock 4 kolu.

Sürücü (ViGEmBus) kurmaz; sistemde zaten kurulu olanı kullanır.
"""
import os
import sys
from ctypes import CDLL, CFUNCTYPE, Structure, byref, c_short, c_ubyte, c_uint, c_ulong, c_ushort, c_void_p

VIGEM_ERROR_NONE = 0x20000000


class XUSB_REPORT(Structure):
    _fields_ = [("wButtons", c_ushort), ("bLeftTrigger", c_ubyte), ("bRightTrigger", c_ubyte),
                ("sThumbLX", c_short), ("sThumbLY", c_short), ("sThumbRX", c_short), ("sThumbRY", c_short)]


class DS4_REPORT(Structure):
    _fields_ = [("bThumbLX", c_ubyte), ("bThumbLY", c_ubyte), ("bThumbRX", c_ubyte), ("bThumbRY", c_ubyte),
                ("wButtons", c_ushort), ("bSpecial", c_ubyte), ("bTriggerL", c_ubyte), ("bTriggerR", c_ubyte)]


# void cb(client, target, UCHAR large, UCHAR small, UCHAR led, LPVOID user)
X360_NOTIFY = CFUNCTYPE(None, c_void_p, c_void_p, c_ubyte, c_ubyte, c_ubyte, c_void_p)


def _dll_path():
    base = getattr(sys, "_MEIPASS", None) or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base, "vendor", "ViGEmClient.dll")


class VigemError(RuntimeError):
    pass


class Bus:
    def __init__(self):
        d = CDLL(_dll_path())
        for name, args, res in [
            ("vigem_alloc", (), c_void_p), ("vigem_connect", (c_void_p,), c_uint),
            ("vigem_disconnect", (c_void_p,), None), ("vigem_free", (c_void_p,), None),
            ("vigem_target_x360_alloc", (), c_void_p), ("vigem_target_ds4_alloc", (), c_void_p),
            ("vigem_target_add", (c_void_p, c_void_p), c_uint), ("vigem_target_remove", (c_void_p, c_void_p), c_uint),
            ("vigem_target_free", (c_void_p,), None),
            ("vigem_target_x360_update", (c_void_p, c_void_p, XUSB_REPORT), c_uint),
            ("vigem_target_ds4_update", (c_void_p, c_void_p, DS4_REPORT), c_uint),
            ("vigem_target_x360_get_user_index", (c_void_p, c_void_p, c_void_p), c_uint),
            ("vigem_target_x360_register_notification", (c_void_p, c_void_p, c_void_p, c_void_p), c_uint),
            ("vigem_target_x360_unregister_notification", (c_void_p,), None),
        ]:
            f = getattr(d, name)
            f.argtypes, f.restype = args, res
        self.d = d
        self.client = d.vigem_alloc()
        err = d.vigem_connect(self.client)
        if err != VIGEM_ERROR_NONE:
            d.vigem_free(self.client)
            raise VigemError(f"ViGEmBus'a bağlanılamadı (kod {err:#x}). Sürücü kurulu değil olabilir.")

    def close(self):
        self.d.vigem_disconnect(self.client)
        self.d.vigem_free(self.client)


class VirtualX360:
    kind = "x360"

    def __init__(self, bus, on_rumble=None):
        self.bus, self.d = bus, bus.d
        self.target = self.d.vigem_target_x360_alloc()
        err = self.d.vigem_target_add(bus.client, self.target)
        if err != VIGEM_ERROR_NONE:
            self.d.vigem_target_free(self.target)
            raise VigemError(f"Sanal Xbox kolu takılamadı (kod {err:#x})")
        self._cb = None
        if on_rumble:
            self._cb = X360_NOTIFY(lambda c, t, large, small, led, u: on_rumble(large, small))
            self.d.vigem_target_x360_register_notification(bus.client, self.target, self._cb, None)

    def user_index(self):
        idx = c_ulong(0xFFFFFFFF)
        if self.d.vigem_target_x360_get_user_index(self.bus.client, self.target, byref(idx)) != VIGEM_ERROR_NONE:
            return None
        return idx.value

    def send(self, buttons, lt, rt, lx, ly, rx, ry):
        self.d.vigem_target_x360_update(self.bus.client, self.target, XUSB_REPORT(buttons, lt, rt, lx, ly, rx, ry))

    def close(self):
        if self._cb:
            self.d.vigem_target_x360_unregister_notification(self.target)
        self.d.vigem_target_remove(self.bus.client, self.target)
        self.d.vigem_target_free(self.target)


# XInput bit -> DS4 bit
_DS4_MAP = {0x1000: 1 << 5, 0x2000: 1 << 6, 0x4000: 1 << 4, 0x8000: 1 << 7,  # A→✕ B→○ X→□ Y→△
            0x0100: 1 << 8, 0x0200: 1 << 9, 0x0020: 1 << 12, 0x0010: 1 << 13,
            0x0040: 1 << 14, 0x0080: 1 << 15}
# (up, down, left, right) -> hat
_HAT = {(1, 0, 0, 0): 0, (1, 0, 0, 1): 1, (0, 0, 0, 1): 2, (0, 1, 0, 1): 3,
        (0, 1, 0, 0): 4, (0, 1, 1, 0): 5, (0, 0, 1, 0): 6, (1, 0, 1, 0): 7}


class VirtualDS4:
    kind = "ds4"

    def __init__(self, bus, on_rumble=None):
        self.bus, self.d = bus, bus.d
        self.target = self.d.vigem_target_ds4_alloc()
        err = self.d.vigem_target_add(bus.client, self.target)
        if err != VIGEM_ERROR_NONE:
            self.d.vigem_target_free(self.target)
            raise VigemError(f"Sanal DualShock 4 takılamadı (kod {err:#x})")

    def user_index(self):
        return None

    def send(self, buttons, lt, rt, lx, ly, rx, ry):
        w = 0
        for xb, db in _DS4_MAP.items():
            if buttons & xb:
                w |= db
        if lt > 30:
            w |= 1 << 10
        if rt > 30:
            w |= 1 << 11
        key = (int(bool(buttons & 1)), int(bool(buttons & 2)), int(bool(buttons & 4)), int(bool(buttons & 8)))
        w |= _HAT.get(key, 8)
        axis = lambda v, inv: max(0, min(255, (((-v if inv else v) + 32768) >> 8)))
        rep = DS4_REPORT(axis(lx, False), axis(ly, True), axis(rx, False), axis(ry, True),
                         w, 1 if buttons & 0x0400 else 0, lt, rt)
        self.d.vigem_target_ds4_update(self.bus.client, self.target, rep)

    def close(self):
        self.d.vigem_target_remove(self.bus.client, self.target)
        self.d.vigem_target_free(self.target)
