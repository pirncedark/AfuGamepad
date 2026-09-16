# PadKöprü portable derleme: dist\PadKopru\ klasörü USB'ye kopyalanıp her yerde çalışır
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
& .\.venv\Scripts\python -c "from PIL import Image; import sys; sys.path.insert(0,'src'); from padkopru.uygulama import simge; simge().save('simge.ico', sizes=[(16,16),(32,32),(48,48),(64,64)])"
& .\.venv\Scripts\pyinstaller --noconfirm --clean --windowed --name PadKopru --icon simge.ico `
    --add-binary "vendor\ViGEmClient.dll;vendor" --paths src --hidden-import pystray._win32 PadKopru.pyw
Copy-Item README.md dist\PadKopru\ -ErrorAction SilentlyContinue
Write-Host "Hazır: dist\PadKopru\PadKopru.exe"
