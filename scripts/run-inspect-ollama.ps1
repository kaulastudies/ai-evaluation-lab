param(
  [Parameter(Mandatory=$true)]
  [string]$Model
)

$ErrorActionPreference = "Stop"

$Inspect = ".\.venv\Scripts\inspect.exe"
if (-not (Test-Path $Inspect)) {
  throw "Run .\scripts\install-evalops-tools.ps1 first."
}

try {
  Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -TimeoutSec 5 | Out-Null
} catch {
  throw "Ollama is not reachable at http://localhost:11434. Start Ollama first."
}

& $Inspect eval ".\inspect_evals\local_baseline.py" --model "ollama/$Model" --temperature 0
if ($LASTEXITCODE -ne 0) { throw "Inspect/Ollama evaluation failed." }
