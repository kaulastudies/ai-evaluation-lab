$ErrorActionPreference = "Stop"

$LocalHarbor = ".\.venv-harbor\Scripts\harbor.exe"

if (Test-Path $LocalHarbor) {
  $Harbor = $LocalHarbor
}
elseif (Get-Command harbor -ErrorAction SilentlyContinue) {
  $Harbor = "harbor"
}
else {
  throw "Harbor is not installed. Run .\scripts\install-evalops-tools.ps1 first."
}

& $Harbor run -p ".\ops\tasks\route-policy-repair" --agent oracle
if ($LASTEXITCODE -ne 0) {
  throw "Harbor oracle run failed."
}
