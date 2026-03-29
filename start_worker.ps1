$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (Test-Path "$PSScriptRoot\.venv\Scripts\python.exe") {
  & "$PSScriptRoot\.venv\Scripts\python.exe" "$PSScriptRoot\nova_worker_launch.py" @args
  exit $LASTEXITCODE
}

$py = Get-Command py -ErrorAction SilentlyContinue
if ($py) {
  & py -3 "$PSScriptRoot\nova_worker_launch.py" @args
  exit $LASTEXITCODE
}

$python = Get-Command python -ErrorAction SilentlyContinue
if ($python) {
  & python "$PSScriptRoot\nova_worker_launch.py" @args
  exit $LASTEXITCODE
}

throw "Kein Python-Interpreter gefunden. Bitte Python 3.12 installieren oder eine .venv anlegen."
