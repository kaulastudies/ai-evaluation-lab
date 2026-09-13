param(
  [Parameter(Mandatory=$true)]
  [string]$Model
)

$ErrorActionPreference = "Stop"

$Inspect = ".\.venv-inspect\Scripts\inspect.exe"
if (-not (Test-Path $Inspect)) {
  throw "Inspect environment missing. Run .\scripts\install-evalops-tools.ps1 first."
}

try {
  $tags = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -TimeoutSec 5
} catch {
  throw "Ollama is not reachable at http://localhost:11434. Start Ollama first."
}

$modelNames = @($tags.models | ForEach-Object { $_.name })
if ($Model -notin $modelNames) {
  throw "Ollama model '$Model' is not installed. Installed: $($modelNames -join ', ')"
}

& $Inspect eval ".\inspect_evals\local_baseline.py" --model "ollama/$Model" --temperature 0
if ($LASTEXITCODE -ne 0) {
  throw "Inspect/Ollama evaluation failed."
}
