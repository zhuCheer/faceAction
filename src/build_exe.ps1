# Package "Face Action Control" into a distributable Windows EXE (PyInstaller).
#
# Usage:
#   .\build_exe.ps1            # single-file exe -> ..\release\FaceAction.exe
#   .\build_exe.ps1 -Dir       # onedir folder  -> ..\release\FaceAction\
#
# Notes:
#   - First run auto-creates .venv and installs deps + PyInstaller (mediapipe is large).
#   - Single-file exe extracts to a temp dir on launch (slower start);
#     onedir starts faster and is less likely to trigger antivirus false positives.
#   - The packaged app reads config from <exe_dir>\config\settings.json (falls back to
#     the bundled defaults if missing), so you can ship an editable config beside the exe.

param(
    [switch]$Dir      # use --onedir output instead of --onefile
)

# Note: do NOT set $ErrorActionPreference = "Stop" here. In Windows PowerShell 5.1
# a native command's stderr (e.g. a Python traceback) is turned into a terminating
# NativeCommandError, which would abort the dependency check before it can install.
$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$AppName = "FaceAction"
$DistDir = "$Root\..\release"
$VenvPy  = "$Root\.venv\Scripts\python.exe"

# 1) Locate Python (prefer the .venv created by start.ps1, else py launcher)
$pythonExe = $null
if (Test-Path $VenvPy) {
    $pythonExe = $VenvPy
} else {
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) { $pythonExe = "py" } else {
        $p = Get-Command python -ErrorAction SilentlyContinue
        if ($p) { $pythonExe = "python" }
    }
}
if (-not $pythonExe) {
    Write-Host "[build] ERROR: Python 3.9+ not found." -ForegroundColor Red
    exit 1
}

# 2) Ensure .venv + deps (including PyInstaller) are ready
function Test-Deps {
    # find_spec only probes installed packages and never raises, so no stderr traceback.
    $check = "import importlib.util,sys; missing=[m for m in ['cv2','mediapipe','numpy','PIL','PySide6','PyInstaller'] if importlib.util.find_spec(m) is None]; sys.exit(1 if missing else 0)"
    if ($pythonExe -eq "py") {
        & py -3.9 -c $check 2>$null; return ($LASTEXITCODE -eq 0)
    }
    & $pythonExe -c $check 2>$null; return ($LASTEXITCODE -eq 0)
}

if (-not (Test-Deps)) {
    if (-not (Test-Path $VenvPy)) {
        Write-Host "[build] Creating venv .venv ..."
        if ($pythonExe -eq "py") { & py -3.9 -m venv "$Root\.venv" }
        else { & $pythonExe -m venv "$Root\.venv" }
        $pythonExe = $VenvPy
    }
    Write-Host "[build] Installing deps (first run may take a while) ..."
    & $pythonExe -m pip install -r "$Root\requirements.txt" pyinstaller
    if ($LASTEXITCODE -ne 0) { Write-Host "[build] dep install failed" -ForegroundColor Red; exit 1 }
}

# 3) Assemble PyInstaller args and build
#    mediapipe model/resource files need collect-all; config ships as a data file.
$modeArgs = if ($Dir) { @("--onedir") } else { @("--onefile") }
$addData  = "config\settings.json;config"

$args = @(
    "--noconfirm",
    "--clean",
    "--windowed",                 # GUI app, no console window
    "--name", $AppName,
    "--distpath", $DistDir,
    "--workpath", "$Root\build",
    "--specpath", "$Root",
    "--collect-all", "mediapipe",
    "--add-data", $addData
) + $modeArgs + @("app.py")

Write-Host "[build] Running PyInstaller ..."
& $pythonExe -m PyInstaller @args
if ($LASTEXITCODE -ne 0) { Write-Host "[build] PyInstaller failed" -ForegroundColor Red; exit 1 }

if ($Dir) {
    Write-Host "[build] Done -> $DistDir\$AppName\" -ForegroundColor Green
} else {
    Write-Host "[build] Done -> $DistDir\$AppName.exe" -ForegroundColor Green
}
exit 0