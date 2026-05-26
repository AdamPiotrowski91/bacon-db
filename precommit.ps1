$repoRoot = Resolve-Path "$PSScriptRoot\."
$py = Join-Path $repoRoot "venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    Write-Error "venv python not found: $py"
    exit 1
}

Write-Host "Running isort..."
& isort .\src .\tests
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Running codespell..."
& codespell .\src .\tests
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

exit 0
