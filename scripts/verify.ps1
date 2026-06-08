# Full local verification — run before pilot or after changes.
param(
    [string]$BaseUrl = "http://127.0.0.1:8000",
    [string]$ApiKey = "staging-key-cust456",
    [string]$AdminKey = "staging-admin-key",
    [switch]$SkipDocker,
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

Write-Host "=== Support Agent verify ===" -ForegroundColor Cyan
Write-Host "URL: $BaseUrl"

if (-not $SkipDocker) {
    Write-Host "`n[1/6] Docker staging containers" -ForegroundColor Yellow
    docker compose -f docker-compose.staging.yml ps
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Docker not running. Start: .\scripts\dev.ps1 -Task staging" -ForegroundColor Red
        exit 1
    }
}

if (-not $SkipTests) {
    Write-Host "`n[2/6] Ruff lint" -ForegroundColor Yellow
    .\.venv\Scripts\ruff.exe check app tests plugins
    if ($LASTEXITCODE -ne 0) { exit 1 }

    Write-Host "`n[3/6] Pytest" -ForegroundColor Yellow
    $env:MOCK_LLM = "true"
    .\.venv\Scripts\python.exe -m pytest -q --tb=no
    if ($LASTEXITCODE -ne 0) { exit 1 }

    Write-Host "`n[4/6] Golden eval" -ForegroundColor Yellow
    .\.venv\Scripts\python.exe tests\eval\run_eval.py
    if ($LASTEXITCODE -ne 0) { exit 1 }

    Write-Host "`n[5/6] A/B eval" -ForegroundColor Yellow
    .\.venv\Scripts\python.exe tests\eval\run_ab_eval.py --no-langfuse
    if ($LASTEXITCODE -ne 0) { exit 1 }
}

Write-Host "`n[6/6] Smoke test (live API)" -ForegroundColor Yellow
.\.venv\Scripts\python.exe scripts\smoke_test.py `
    --url $BaseUrl `
    --api-key $ApiKey `
    --admin-key $AdminKey
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "`n=== ALL CHECKS PASSED ===" -ForegroundColor Green
Write-Host "Widget:  $BaseUrl/widget/?customer_id=cust_456&api_key=$ApiKey"
Write-Host "Swagger: $BaseUrl/docs"
Write-Host "Admin:   $BaseUrl/admin-ui/  (X-Admin-Key: $AdminKey)"
