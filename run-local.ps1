<#
.SYNOPSIS
    Run the AI Agentic World Cup locally with Docker (postgres + redis + azurite +
    api + worker + frontend), and optionally kick off a tournament.

.DESCRIPTION
    A thin, friendly wrapper around `docker compose`. It checks Docker is running,
    creates .env from .env.example on first use, builds + starts the stack, waits
    for the API to become healthy, and prints the URLs.

.PARAMETER Action
    up      (default) build + start the stack, wait for health, print URLs
    down    stop and remove containers (keeps data volumes)
    clean   stop and remove containers AND data volumes
    restart restart the api + worker only (after code changes)
    build   rebuild images without starting
    logs    follow logs (optionally for a single -Service)
    ps      show container status
    demo    run a full tournament via the API and print the result

.PARAMETER Service
    Service name for `logs` (e.g. api, worker, frontend, postgres, redis, azurite).

.PARAMETER Seed / Teams / Groups
    Tournament parameters used by `-Action demo`.

.EXAMPLE
    .\run-local.ps1                       # start everything
    .\run-local.ps1 demo                  # start + simulate a 32-team World Cup
    .\run-local.ps1 logs -Service worker  # tail the worker
    .\run-local.ps1 down                  # stop
#>
[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet('up', 'down', 'clean', 'restart', 'build', 'logs', 'ps', 'demo')]
    [string]$Action = 'up',

    [string]$Service = '',
    [int]$Seed = 2026,
    [int]$Teams = 32,
    [int]$Groups = 8
)

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$apiBase = 'http://localhost:8000'
$frontendUrl = 'http://localhost:5173'

function Write-Step([string]$msg) { Write-Host "==> $msg" -ForegroundColor Cyan }
function Write-Ok([string]$msg) { Write-Host "[ok] $msg" -ForegroundColor Green }
function Write-Warn2([string]$msg) { Write-Host "[!] $msg" -ForegroundColor Yellow }

function Test-Docker {
    try { docker info *> $null } catch { }
    if ($LASTEXITCODE -ne 0) {
        Write-Warn2 'Docker does not appear to be running. Start Docker Desktop and retry.'
        exit 1
    }
}

function Invoke-Compose {
    param([Parameter(ValueFromRemainingArguments = $true)] [string[]]$Args)
    Push-Location $root
    try { & docker compose @Args } finally { Pop-Location }
}

function Ensure-Env {
    $envPath = Join-Path $root '.env'
    if (-not (Test-Path $envPath)) {
        Copy-Item (Join-Path $root '.env.example') $envPath
        Write-Ok 'Created .env from .env.example (LLM disabled by default; edit to enable AI Foundry).'
    }
}

function Wait-Healthy {
    param([int]$TimeoutSec = 120)
    Write-Step "Waiting for the API at $apiBase/health ..."
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        try {
            $r = Invoke-RestMethod -Uri "$apiBase/health" -TimeoutSec 3
            if ($r.status -eq 'ok') { Write-Ok "API healthy (backend=$($r.backend))."; return $true }
        }
        catch { Start-Sleep -Seconds 2 }
    }
    Write-Warn2 "API did not become healthy within $TimeoutSec s. Check: .\run-local.ps1 logs -Service api"
    return $false
}

function Show-Urls {
    Write-Host ''
    Write-Host '  Frontend : ' -NoNewline; Write-Host $frontendUrl -ForegroundColor White
    Write-Host '  API      : ' -NoNewline; Write-Host $apiBase -ForegroundColor White
    Write-Host '  API docs : ' -NoNewline; Write-Host "$apiBase/docs" -ForegroundColor White
    Write-Host ''
    Write-Host '  Try a tournament:  .\run-local.ps1 demo' -ForegroundColor DarkGray
}

function Invoke-Demo {
    if (-not (Wait-Healthy)) { return }
    $perGroup = [int]($Teams / $Groups)
    $body = @{ config = @{
            teams = $Teams; groups = $Groups; perGroup = $perGroup
            advancePerGroup = 2; seed = $Seed
        } } | ConvertTo-Json -Depth 5

    Write-Step "Creating tournament (teams=$Teams groups=$Groups seed=$Seed) ..."
    $created = Invoke-RestMethod -Method Post -Uri "$apiBase/tournaments" -Body $body -ContentType 'application/json'
    $tid = $created.id
    Write-Ok "Tournament id: $tid"

    Write-Step 'Simulating (group stage + knockouts) ...'
    $status = $null
    for ($i = 0; $i -lt 120; $i++) {
        Start-Sleep -Milliseconds 800
        $status = Invoke-RestMethod -Uri "$apiBase/tournaments/$tid"
        if ($status.phase -eq 'done') { break }
        Write-Host ("    phase: {0}" -f $status.phase)
    }
    if ($status.phase -ne 'done') { Write-Warn2 'Tournament did not finish in time.'; return }

    $teams = Invoke-RestMethod -Uri "$apiBase/tournaments/$tid/teams"
    $champ = $teams | Where-Object { $_.id -eq $status.championId } | Select-Object -First 1
    $matches = Invoke-RestMethod -Uri "$apiBase/tournaments/$tid/matches"

    Write-Host ''
    Write-Ok ("CHAMPION: {0}  (tier {1})" -f $champ.nation, $champ.tier)
    Write-Host ("  matches played : {0}" -f $matches.Count)
    Write-Host ("  run hash       : {0}" -f $status.runHash.Substring(0, 16))
    Write-Host ("  standings      : {0}/tournaments/{1}/standings" -f $apiBase, $tid)
    Write-Host ("  bracket        : {0}/tournaments/{1}/bracket" -f $apiBase, $tid)
    Write-Host ("  open the app   : {0}" -f $frontendUrl)
}

# ---------------------------------------------------------------------------
Test-Docker

switch ($Action) {
    'up' {
        Ensure-Env
        Write-Step 'Building and starting the stack ...'
        Invoke-Compose up -d --build
        if (Wait-Healthy) { Show-Urls }
    }
    'build' {
        Ensure-Env
        Write-Step 'Building images ...'
        Invoke-Compose build
        Write-Ok 'Build complete.'
    }
    'restart' {
        Write-Step 'Restarting api + worker ...'
        Invoke-Compose up -d --build api worker
        if (Wait-Healthy) { Write-Ok 'Restarted.' }
    }
    'down' {
        Write-Step 'Stopping the stack ...'
        Invoke-Compose down
        Write-Ok 'Stopped (data volumes kept).'
    }
    'clean' {
        Write-Step 'Stopping the stack and removing volumes ...'
        Invoke-Compose down -v
        Write-Ok 'Stopped and volumes removed.'
    }
    'logs' {
        if ($Service) { Invoke-Compose logs -f $Service }
        else { Invoke-Compose logs -f }
    }
    'ps' { Invoke-Compose ps }
    'demo' {
        Ensure-Env
        Write-Step 'Ensuring the stack is up ...'
        Invoke-Compose up -d --build
        Invoke-Demo
    }
}
