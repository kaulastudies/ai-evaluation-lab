$ErrorActionPreference = "Stop"

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
  throw "Python is required."
}

if (-not (Test-Path ".venv")) {
  python -m venv .venv
}

$Py = ".\\.venv\\Scripts\\python.exe"
& $Py -m pip install --upgrade pip
& $Py -m pip install harbor inspect-ai

Write-Host ""
Write-Host "Installed Harbor and Inspect AI into .venv." -ForegroundColor Green
Write-Host "Activate with: .\\.venv\\Scripts\\Activate.ps1"
