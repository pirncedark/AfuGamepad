"""Oyun kütüphanelerini tarar ve öndeki pencerenin oyun olup olmadığını anlar."""
import ctypes
import glob
import json
import os
import re
from ctypes import wintypes

import psutil

_user32 = ctypes.WinDLL("user32", use_last_error=True)


def _steam_kok():
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as k:
            return winreg.QueryValueEx(k, "SteamPath")[0].replace("/", "\\")
    except OSError:
        return r"C:\Program Files (x86)\Steam"


def steam_oyunlari():
    """{klasör: oyun adı}"""
    sonuc = {}
    vdf = os.path.join(_steam_kok(), "steamapps", "libraryfolders.vdf")
    try:
        with open(vdf, encoding="utf-8", errors="ignore") as f:
            yollar = [p.replace("\\\\", "\\") for p in re.findall(r'"path"\s+"([^"]+)"', f.read())]
    except OSError:
        return sonuc
    for kutuphane in yollar:
        for acf in glob.glob(os.path.join(kutuphane, "steamapps", "appmanifest_*.acf")):
            try:
                with open(acf, encoding="utf-8", errors="ignore") as f:
                    metin = f.read()
            except OSError:
                continue
            ad = re.search(r'"name"\s+"([^"]+)"', metin)
            klasor = re.search(r'"installdir"\s+"([^"]+)"', metin)
            if ad and klasor:
                sonuc[os.path.join(kutuphane, "steamapps", "common", klasor.group(1)).lower()] = ad.group(1)
    return sonuc


def epic_oyunlari():
    sonuc = {}
    for item in glob.glob(r"C:\ProgramData\Epic\EpicGamesLauncher\Data\Manifests\*.item"):
        try:
            with open(item, encoding="utf-8") as f:
                m = json.load(f)
            sonuc[m["InstallLocation"].lower()] = m.get("DisplayName") or m["AppName"]
        except (OSError, ValueError, KeyError):
            continue
    return sonuc


def tum_kutuphaneler():
    k = {}
    k.update(steam_oyunlari())
    k.update(epic_oyunlari())
    return k


class RECT(ctypes.Structure):
    _fields_ = [("left", wintypes.LONG), ("top", wintypes.LONG), ("right", wintypes.LONG), ("bottom", wintypes.LONG)]


class MONITORINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", RECT), ("rcWork", RECT), ("dwFlags", wintypes.DWORD)]


_SISTEM = {"explorer.exe", "searchhost.exe", "startmenuexperiencehost.exe", "shellexperiencehost.exe",
           "applicationframehost.exe", "textinputhost.exe", "lockapp.exe", "padkopru.exe", "python.exe",
           "pythonw.exe", "steamwebhelper.exe", "steam.exe", "chrome.exe", "msedge.exe", "firefox.exe",
           "code.exe", "windowsterminal.exe", "discord.exe", "obs64.exe", "gamebar.exe", "vlc.exe", "mpc-hc64.exe"}
_OYUN_DISI_YOL = ("\\windows\\", "\\windowsapps\\microsoft.")


def on_pencere():
    """(exe_adı, tam_yol, tam_ekran_mı) ya da None."""
    hwnd = _user32.GetForegroundWindow()
    if not hwnd:
        return None
    pid = wintypes.DWORD()
    _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    try:
        p = psutil.Process(pid.value)
        yol = p.exe()
    except (psutil.Error, OSError):
        return None
    r = RECT()
    _user32.GetWindowRect(hwnd, ctypes.byref(r))
    mon = _user32.MonitorFromWindow(hwnd, 2)
    mi = MONITORINFO(cbSize=ctypes.sizeof(MONITORINFO))
    _user32.GetMonitorInfoW(mon, ctypes.byref(mi))
    m = mi.rcMonitor
    tam = r.left <= m.left and r.top <= m.top and r.right >= m.right and r.bottom >= m.bottom
    return os.path.basename(yol).lower(), yol, tam


def guzel_ad(exe):
    """project_plague-win64-shipping.exe -> Project Plague"""
    ad = os.path.splitext(exe)[0]
    ad = re.sub(r"[-_](win64|win32|x64|dx11|dx12|shipping|vulkan)\b", "", ad, flags=re.I)
    ad = re.sub(r"[-_]+", " ", ad).strip()
    return ad.title() if ad.islower() else ad


def oyun_mu(exe, yol, tam_ekran, kutuphaneler):
    """Oyunsa oyun adını, değilse None döndürür."""
    if exe in _SISTEM:
        return None
    kucuk = yol.lower()
    for klasor, ad in kutuphaneler.items():
        if kucuk.startswith(klasor + "\\"):
            return ad
    if "\\xboxgames\\" in kucuk:
        return guzel_ad(exe)
    if tam_ekran and not any(s in kucuk for s in _OYUN_DISI_YOL):
        return guzel_ad(exe)
    return None
