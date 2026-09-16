"""Kol → klavye/fare (SendInput, tarama kodu ile — DirectInput oyunları da görür)."""
from ctypes import POINTER, Structure, Union, WinDLL, byref, c_long, c_ulong, c_ushort, sizeof
from ctypes.wintypes import DWORD, WORD

_user32 = WinDLL("user32")

SCAN = {
    **{c: v for c, v in zip("1234567890", range(0x02, 0x0C))},
    **{c: v for c, v in zip("qwertyuiop", range(0x10, 0x1A))},
    **{c: v for c, v in zip("asdfghjkl", range(0x1E, 0x27))},
    **{c: v for c, v in zip("zxcvbnm", range(0x2C, 0x33))},
    "esc": 0x01, "tab": 0x0F, "enter": 0x1C, "space": 0x39, "lshift": 0x2A, "rshift": 0x36,
    "lctrl": 0x1D, "lalt": 0x38, "backspace": 0x0E, "capslock": 0x3A,
    "f1": 0x3B, "f2": 0x3C, "f3": 0x3D, "f4": 0x3E, "f5": 0x3F, "f6": 0x40,
    "f7": 0x41, "f8": 0x42, "f9": 0x43, "f10": 0x44, "f11": 0x57, "f12": 0x58,
    # genişletilmiş tuşlar (E0 önekli)
    "up": 0xE048, "down": 0xE050, "left": 0xE04B, "right": 0xE04D,
}
MOUSE = {"mouse1": (0x0002, 0x0004), "mouse2": (0x0008, 0x0010), "mouse3": (0x0020, 0x0040)}


class KEYBDINPUT(Structure):
    _fields_ = [("wVk", WORD), ("wScan", WORD), ("dwFlags", DWORD), ("time", DWORD), ("dwExtraInfo", POINTER(c_ulong))]


class MOUSEINPUT(Structure):
    _fields_ = [("dx", c_long), ("dy", c_long), ("mouseData", DWORD), ("dwFlags", DWORD),
                ("time", DWORD), ("dwExtraInfo", POINTER(c_ulong))]


class _U(Union):
    _fields_ = [("ki", KEYBDINPUT), ("mi", MOUSEINPUT), ("pad", c_ushort * 16)]


class INPUT(Structure):
    _fields_ = [("type", DWORD), ("u", _U)]


def _send(inp):
    _user32.SendInput(1, byref(inp), sizeof(INPUT))


def key(name, down):
    name = name.lower()
    if name in MOUSE:
        inp = INPUT(type=0)
        inp.u.mi = MOUSEINPUT(0, 0, 0, MOUSE[name][0 if down else 1], 0, None)
        return _send(inp)
    code = SCAN.get(name)
    if code is None:
        return
    flags = 0x0008 | (0 if down else 0x0002)  # SCANCODE | KEYUP
    if code > 0xFF:
        flags |= 0x0001  # EXTENDEDKEY
        code &= 0xFF
    inp = INPUT(type=1)
    inp.u.ki = KEYBDINPUT(0, code, flags, 0, None)
    _send(inp)


def mouse_move(dx, dy):
    if dx or dy:
        inp = INPUT(type=0)
        inp.u.mi = MOUSEINPUT(int(dx), int(dy), 0, 0x0001, 0, None)
        _send(inp)
