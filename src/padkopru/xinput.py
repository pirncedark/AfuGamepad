"""XInput okuma/yazma (ctypes, ek bağımlılık yok)."""
from ctypes import Structure, WinDLL, byref, c_short, c_ubyte, c_uint, c_ushort

ERROR_SUCCESS = 0

# Tuş bitleri (XINPUT_GAMEPAD_*)
BUTTONS = {
    "UP": 0x0001, "DOWN": 0x0002, "LEFT": 0x0004, "RIGHT": 0x0008,
    "START": 0x0010, "BACK": 0x0020, "LS": 0x0040, "RS": 0x0080,
    "LB": 0x0100, "RB": 0x0200, "GUIDE": 0x0400,
    "A": 0x1000, "B": 0x2000, "X": 0x4000, "Y": 0x8000,
}


class GAMEPAD(Structure):
    _fields_ = [("wButtons", c_ushort), ("bLeftTrigger", c_ubyte), ("bRightTrigger", c_ubyte),
                ("sThumbLX", c_short), ("sThumbLY", c_short), ("sThumbRX", c_short), ("sThumbRY", c_short)]


class STATE(Structure):
    _fields_ = [("dwPacketNumber", c_uint), ("Gamepad", GAMEPAD)]


class VIBRATION(Structure):
    _fields_ = [("wLeftMotorSpeed", c_ushort), ("wRightMotorSpeed", c_ushort)]


class CAPABILITIES(Structure):
    _fields_ = [("Type", c_ubyte), ("SubType", c_ubyte), ("Flags", c_ushort),
                ("Gamepad", GAMEPAD), ("Vibration", VIBRATION)]


class CAPABILITIES_EX(Structure):
    _fields_ = [("Capabilities", CAPABILITIES), ("VendorId", c_ushort), ("ProductId", c_ushort),
                ("ProductVersion", c_ushort), ("unk1", c_ushort), ("unk2", c_uint)]


_dll = WinDLL("xinput1_4.dll")
_get_state = _dll.XInputGetState
_set_state = _dll.XInputSetState
try:
    _get_state_ex = _dll[100]  # Guide tuşunu da döndüren gizli fonksiyon
except (AttributeError, OSError):
    _get_state_ex = _get_state
try:
    _get_caps_ex = _dll[108]
except (AttributeError, OSError):
    _get_caps_ex = None


def get_state(slot):
    """(packet, GAMEPAD) veya bağlı değilse None."""
    st = STATE()
    if _get_state_ex(slot, byref(st)) != ERROR_SUCCESS:
        return None
    return st.dwPacketNumber, st.Gamepad


def set_rumble(slot, left, right):
    """left/right: 0-255"""
    _set_state(slot, byref(VIBRATION(left * 257, right * 257)))


def vid_pid(slot):
    if _get_caps_ex is None:
        return None
    caps = CAPABILITIES_EX()
    if _get_caps_ex(1, slot, 0, byref(caps)) != ERROR_SUCCESS:
        return None
    return caps.VendorId, caps.ProductId


def connected_slots():
    return [s for s in range(4) if get_state(s) is not None]
