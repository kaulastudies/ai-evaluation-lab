$ErrorActionPreference = "Stop"

function Show-Tool([string]$Name) {
  $cmd = Get-Command $Name -ErrorAction SilentlyContinue
  if ($cmd) {
    Write-Host "[OK] $Name -> $($cmd.Source)" -ForegroundColor Green
    return $true
  }
  Write-Host "[MISSING] $Name" -ForegroundColor Yellow
  return $false
}

Write-Host "AI Evaluation Lab - local preflight" -ForegroundColor Cyan

$null = Show-Tool "python"
$dockerOk = Show-Tool "docker"
$ollamaOk = Show-Tool "ollama"
$null = Show-Tool "harbor"
$null = Show-Tool "inspect"

if ($dockerOk) {
  docker info 1>$null 2>$null
  if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Docker daemon is running" -ForegroundColor Green
  } else {
    Write-Host "[BLOCKED] Docker is installed but not running" -ForegroundColor Red
  }
}

if ($ollamaOk) {
  try {
    $tags = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -TimeoutSec 5
    Write-Host "[OK] Ollama API is reachable" -ForegroundColor Green
    if ($tags.models.Count -gt 0) {
      Write-Host "Installed Ollama models:"
      $tags.models | ForEach-Object { Write-Host "  - $($_.name)" }
    } else {
      Write-Host "No Ollama models are currently installed." -ForegroundColor Yellow
    }
  } catch {
    Write-Host "[BLOCKED] Ollama CLI exists but the local API is not reachable." -ForegroundColor Red
  }
}

python ops/gates/validate_taskpack.py ops/tasks/route-policy-repair
if ($LASTEXITCODE -ne 0) { throw "Task contract gate failed." }

python ops/gates/selftest_reference_task.py ops/tasks/route-policy-repair
if ($LASTEXITCODE -ne 0) { throw "Reference self-test failed." }

Write-Host "Preflight complete." -ForegroundColor Green
