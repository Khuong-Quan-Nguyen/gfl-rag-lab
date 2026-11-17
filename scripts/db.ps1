<#
.SYNOPSIS
  Native Windows Postgres 16 + pgvector for gfl-rag-lab (no Docker / no admin).

.DESCRIPTION
  Postgres and pgvector come from conda-forge, installed into .tools\pg with micromamba:
    micromamba create -p .tools\pg -c conda-forge "postgresql=16" pgvector
  Data lives in .pgdata. Listens on localhost:5433 (user rag / password rag / db gfl),
  matching docker-compose.yml so PG_DSN is the same either way.

.EXAMPLE
  .\scripts\db.ps1 init     # first time: initdb, start, create db, apply sql\schema.sql
  .\scripts\db.ps1 start
  .\scripts\db.ps1 stop
  .\scripts\db.ps1 status
  .\scripts\db.ps1 psql     # interactive shell
#>
param(
    [Parameter(Mandatory)][ValidateSet('init', 'start', 'stop', 'status', 'psql')][string]$Action
)
$ErrorActionPreference = 'Stop'

$Root    = Split-Path -Parent $PSScriptRoot
$Bin     = Join-Path $Root '.tools\pg\Library\bin'
$Data    = Join-Path $Root '.pgdata'
$Log     = Join-Path $Root '.tools\postgres.log'
$Port    = 5433
$User    = 'rag'
$Db      = 'gfl'
$env:PGPASSWORD = 'rag'

function Invoke-Pg([string]$Exe, [string[]]$PgArgs) {
    & (Join-Path $Bin $Exe) @PgArgs
    if ($LASTEXITCODE -ne 0) { throw "$Exe failed with exit code $LASTEXITCODE" }
}

function Start-Db {
    # Start-Process so the long-lived server doesn't inherit (and hold open) the caller's stdout pipe.
    $ctlArgs = "-D `"$Data`" -l `"$Log`" -o `"-p $Port -c listen_addresses=localhost`" -w start"
    # Not -Wait: in PS 5.1 that waits for the whole process tree, including the server itself.
    $p = Start-Process -FilePath (Join-Path $Bin 'pg_ctl.exe') -ArgumentList $ctlArgs -WindowStyle Hidden -PassThru
    $p.WaitForExit()
    if ($p.ExitCode -ne 0) { throw "pg_ctl start failed (exit $($p.ExitCode)); see $Log" }
    Write-Host "Postgres running on localhost:$Port"
}

switch ($Action) {
    'init' {
        if (Test-Path $Data) { throw "$Data already exists. Delete it yourself if you really want a fresh cluster." }
        $pw = Join-Path $env:TEMP 'gfl-pg-pw.txt'
        Set-Content -Path $pw -Value 'rag' -NoNewline -Encoding ascii
        try {
            Invoke-Pg 'initdb.exe' @('-D', $Data, '-U', $User, "--pwfile=$pw", '-A', 'scram-sha-256', '-E', 'UTF8', '--locale=C')
        } finally { Remove-Item $pw -ErrorAction SilentlyContinue }
        Start-Db
        Invoke-Pg 'createdb.exe' @('-h', 'localhost', '-p', $Port, '-U', $User, $Db)
        Invoke-Pg 'psql.exe' @('-h', 'localhost', '-p', $Port, '-U', $User, '-d', $Db, '-v', 'ON_ERROR_STOP=1', '-q', '-f', (Join-Path $Root 'sql\schema.sql'))
        Write-Host "Initialized: postgresql://${User}:rag@localhost:$Port/$Db"
    }
    'start'  { Start-Db }
    'stop'   { Invoke-Pg 'pg_ctl.exe' @('-D', $Data, '-m', 'fast', 'stop') }
    'status' { & (Join-Path $Bin 'pg_ctl.exe') -D $Data status }
    'psql'   { & (Join-Path $Bin 'psql.exe') -h localhost -p $Port -U $User -d $Db }
}
