# Start the "Face Action Control" product (Windows PowerShell)
#
# Usage:
#   .\start.ps1               # default camera (index 0)
#   .\start.ps1 -Camera 1     # specify camera index
#   .\start.ps1 -Test         # run core unit tests (no camera needed)
#
# Missing deps (opencv/mediapipe/numpy/Pillow/PySide6) are auto-installed into src\.venv

param(
    [string]$Camera = "",
    [switch]$Test
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

# 1) Locate a Python interpreter
$pythonExe = $null
if (Test-Path "$Root\.venv\Scripts\python.exe") {
    $pythonExe = "$Root\.venv\Scripts\python.exe"
} elseif (Test-Path "$Root\..\demo\.venv\Scripts\python.exe") {
    $pythonExe = "$Root\..\demo\.venv\Scripts\python.exe"
} else {
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) { $pythonExe = "py" }
    else {
        $p = Get-Command python -ErrorAction SilentlyContinue
        if ($p) { $pythonExe = "python" }
    }
}

if (-not $pythonExe) {
    Write-Host "[start] ERROR: Python 3.9+ not found." -ForegroundColor Red
    exit 1
}

# 2) Check deps; install if missing
$depsOk = $false
if ($pythonExe -eq "py") {
    & py -3.9 -c "import cv2, mediapipe, numpy, PIL, PySide6" 2>$null
    if ($LASTEXITCODE -eq 0) { $depsOk = $true }
} else {
    & $pythonExe -c "import cv2, mediapipe, numpy, PIL, PySide6" 2>$null
    if ($LASTEXITCODE -eq 0) { $depsOk = $true }
}

if (-not $depsOk) {
    if (-not (Test-Path "$Root\.venv\Scripts\python.exe")) {
        Write-Host "[start] Creating venv .venv ..."
        if ($pythonExe -eq "py") { & py -3.9 -m venv "$Root\.venv" }
        else { & $pythonExe -m venv "$Root\.venv" }
        $pythonExe = "$Root\.venv\Scripts\python.exe"
    }
    Write-Host "[start] Installing deps (first run may take a while) ..."
    & $pythonExe -m pip install -r "$Root\requirements.txt"
    if ($LASTEXITCODE -ne 0) { Write-Host "[start] dep install failed" -ForegroundColor Red; exit 1 }
}

# 3) Run
if ($Test) {
    Write-Host "[start] Running unit tests ..."
    & $pythonExe -m unittest discover -s "$Root\tests" -v
    exit $LASTEXITCODE
}

Write-Host "[start] Launching Face Action Control ..."
if ($Camera -ne "") {
    & $pythonExe "$Root\app.py" $Camera
} else {
    & $pythonExe "$Root\app.py"
}
exit $LASTEXITCODE