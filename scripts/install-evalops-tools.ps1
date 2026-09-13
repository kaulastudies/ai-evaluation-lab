$ErrorActionPreference = "Stop"

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
  throw "Python is required."
}

Write-Host "AI Evaluation Lab - isolated tool environments" -ForegroundColor Cyan

# Harbor and Inspect intentionally live in separate virtual environments.
# Their OpenAI SDK dependency requirements can differ.

if (-not (Test-Path ".venv-harbor")) {
  python -m venv .venv-harbor
}
$HarborPy = ".\.venv-harbor\Scripts\python.exe"
& $HarborPy -m pip install --upgrade pip
& $HarborPy -m pip install harbor

if (-not (Test-Path ".venv-inspect")) {
  python -m venv .venv-inspect
}
$InspectPy = ".\.venv-inspect\Scripts\python.exe"
& $InspectPy -m pip install --upgrade pip
& $InspectPy -m pip install "inspect-ai==0.3.263" "openai>=3.1.0"

Write-Host ""
Write-Host "Installed isolated tool environments." -ForegroundColor Green
Write-Host "Harbor : .\.venv-harbor\Scripts\harbor.exe"
Write-Host "Inspect: .\.venv-inspect\Scripts\inspect.exe"
