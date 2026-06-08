param(
    [ValidateSet("install", "test", "lint", "run", "migrate", "postgres", "staging", "eval", "loadtest")]
    [string]$Task = "run"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

switch ($Task) {
    "install" {
        python -m venv .venv
        .\.venv\Scripts\Activate.ps1
        pip install -r requirements.txt -r requirements-dev.txt
    }
    "test" {
        $env:MOCK_LLM = "true"
        .\.venv\Scripts\python.exe -m pytest -v
    }
    "lint" {
        .\.venv\Scripts\ruff.exe check app tests
    }
    "run" {
        .\.venv\Scripts\uvicorn.exe app.main:app --reload --host 127.0.0.1 --port 8000
    }
    "migrate" {
        .\.venv\Scripts\alembic.exe upgrade head
    }
    "postgres" {
        docker compose up -d postgres
        Write-Host "Postgres: postgresql://support:support@localhost:5432/support_agent"
    }
    "staging" {
        docker compose -f docker-compose.staging.yml up --build
    }
    "eval" {
        $env:MOCK_LLM = "true"
        .\.venv\Scripts\python.exe tests\eval\run_eval.py
    }
    "loadtest" {
        $env:MOCK_LLM = "true"
        .\.venv\Scripts\python.exe scripts\load_test.py --concurrency 50
    }
}
