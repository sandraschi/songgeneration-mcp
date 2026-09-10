#Requires -Version 7
<#
.SYNOPSIS
Build the songgeneration-mcp .mcpb bundle for Claude Desktop.

Implements the mandatory pipeline from MCPB_PACKAGING_STANDARDS.md section 2.5:
wipe + fresh-copy src -> mcpb/src (never edit the staged copy by hand), ensure
mcpb/.mcpbignore exists (the mcpb CLI reads .mcpbignore from the pack root,
not the repo root), run the required mechanical checks, then pack.

mcpb/src is a build artifact -- regenerated every run, gitignored, never
committed. This script deletes and recreates it each time.
#>
$ErrorActionPreference = 'Stop'

$RepoRoot = Split-Path -Parent $PSScriptRoot
$McpbDir = Join-Path $RepoRoot 'mcpb'
$Pkg = 'songgeneration_mcp'
$SrcPkg = Join-Path $RepoRoot "src\$Pkg"
$StageRoot = Join-Path $McpbDir 'src'
$StagePkg = Join-Path $StageRoot $Pkg
$VerifyScript = Join-Path $McpbDir 'verify_pack.py'

function Step($n, $msg) { Write-Host "== $n. $msg ==" -ForegroundColor Cyan }

Step 1 'Wipe + fresh-copy src -> mcpb/src (never a stale/hand-edited stage)'
if (Test-Path $StageRoot) { Remove-Item -Recurse -Force $StageRoot }
if (-not (Test-Path $SrcPkg)) { throw "Copy source missing: $SrcPkg" }
New-Item -ItemType Directory -Force -Path $StageRoot | Out-Null
Copy-Item -Recurse -Force $SrcPkg $StagePkg
Write-Host "  copied $SrcPkg -> $StagePkg"

Step 2 'Strip pollution from the fresh stage'
Get-ChildItem -Recurse -Path $StageRoot -Include '__pycache__' -Directory -ErrorAction SilentlyContinue |
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Recurse -Path $StageRoot -Include '*.pyc', '*.bak', '*.bak.*', '*.bak-*', '*.orig', '*.rej' -File -ErrorAction SilentlyContinue |
    Remove-Item -Force -ErrorAction SilentlyContinue

Step 3 'Sync mcpb/.mcpbignore from repo root (pack root, not repo root, is what mcpb reads)'
# Always overwrite, not "only if missing" -- the standard's own gotcha section is
# about exactly this file silently drifting between the two locations.
$McpbIgnore = Join-Path $McpbDir '.mcpbignore'
Copy-Item (Join-Path $RepoRoot '.mcpbignore') $McpbIgnore -Force
Write-Host '  synced repo-root .mcpbignore -> mcpb/.mcpbignore'

Step 4 'Required check: import isolation (only mcpb/src on sys.path)'
# Checked against mcp_server.py -- the actual manifest.json entry_point (the
# stdio MCP server Claude Desktop launches), not server.py (the web/ASGI
# dashboard backend -- wrong transport shape for an MCPB stdio launch).
$env:PYTHONDONTWRITEBYTECODE = '1'
uv run --project $RepoRoot python $VerifyScript import $StageRoot "$Pkg.mcp_server"
if ($LASTEXITCODE -ne 0) { throw 'Import-isolation check failed' }

Step 5 'Required check: AST call-site binding (catches missing imports)'
uv run --project $RepoRoot python $VerifyScript ast (Join-Path $StagePkg 'mcp_server.py')
if ($LASTEXITCODE -ne 0) { throw 'AST check failed' }
Remove-Item Env:\PYTHONDONTWRITEBYTECODE -ErrorAction SilentlyContinue

Step 6 'Required check: pollution, run AFTER import (which itself writes bytecode)'
uv run --project $RepoRoot python $VerifyScript pollution $McpbDir
if ($LASTEXITCODE -ne 0) { throw 'Pollution check failed (import step above may have written __pycache__)' }

Step 7 '3-4-100 prompt check (report only -- does not block pack)'
$sysWords = (Get-Content -Raw (Join-Path $McpbDir 'assets/prompts/system.md') -ErrorAction SilentlyContinue) -split '\s+' | Where-Object { $_ } | Measure-Object | Select-Object -ExpandProperty Count
$userWords = (Get-Content -Raw (Join-Path $McpbDir 'assets/prompts/user.md') -ErrorAction SilentlyContinue) -split '\s+' | Where-Object { $_ } | Measure-Object | Select-Object -ExpandProperty Count
$exCount = (Get-Content -Raw (Join-Path $McpbDir 'assets/prompts/examples.json') -ErrorAction SilentlyContinue | ConvertFrom-Json -ErrorAction SilentlyContinue).Count
if ($sysWords -lt 3000 -or $userWords -lt 4000 -or $exCount -lt 100) {
    Write-Warning "3-4-100 FAIL (non-blocking): system.md=$sysWords/3000 user.md=$userWords/4000 examples.json=$exCount/100 -- this is a runt package per MCPB_PACKAGING_STANDARDS.md 2.3b"
} else {
    Write-Host "  OK: system.md=$sysWords user.md=$userWords examples.json=$exCount"
}

Step 8 'mcpb pack'
$manifest = Get-Content (Join-Path $McpbDir 'manifest.json') -Raw | ConvertFrom-Json
$OutDir = Join-Path $RepoRoot 'dist'
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$OutFile = Join-Path $OutDir "songgeneration_mcp-v$($manifest.version).mcpb"
if (Test-Path $OutFile) { Remove-Item -Force $OutFile }
bunx @anthropic-ai/mcpb pack $McpbDir $OutFile
if ($LASTEXITCODE -ne 0) { throw 'mcpb pack failed' }

Step 9 'Verify pack output'
if (-not (Test-Path $OutFile)) { throw "Pack did not produce $OutFile" }
$size = (Get-Item $OutFile).Length
Write-Host "  built: $OutFile ($([math]::Round($size / 1kb, 1)) KB)"
bunx @anthropic-ai/mcpb info $OutFile
if ($LASTEXITCODE -ne 0) { throw 'mcpb info failed on the freshly-built bundle' }

Step 10 'Required check: launch the packaged bundle in a clean unpacked copy'
# Static checks (import isolation, AST) cannot prove the bundle actually
# serves -- only launching it, exactly as Claude Desktop would, can. Unpack
# to a scratch dir and run the manifest's own command/args against it.
$LaunchDir = Join-Path ([System.IO.Path]::GetTempPath()) "songgeneration-mcpb-launchtest-$([guid]::NewGuid().ToString('N').Substring(0,8))"
try {
    bunx @anthropic-ai/mcpb unpack $OutFile $LaunchDir | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'mcpb unpack failed' }

    $manifestArgs = $manifest.server.mcp_config.args | ForEach-Object { $_ -replace '\$\{PWD\}', $LaunchDir }
    Write-Host "  launching: $($manifest.server.mcp_config.command) $($manifestArgs -join ' ')"

    $stdoutFile = Join-Path $LaunchDir '_launch_stdout.log'
    $stderrFile = Join-Path $LaunchDir '_launch_stderr.log'
    $proc = Start-Process -FilePath $manifest.server.mcp_config.command -ArgumentList $manifestArgs `
        -WorkingDirectory $LaunchDir -PassThru -NoNewWindow `
        -RedirectStandardOutput $stdoutFile -RedirectStandardError $stderrFile

    Start-Sleep -Seconds 12
    $stillRunning = -not $proc.HasExited
    $stderrText = if (Test-Path $stderrFile) { Get-Content -Raw $stderrFile -ErrorAction SilentlyContinue } else { '' }
    $hasTraceback = $stderrText -match 'Traceback \(most recent call last\)'

    if ($stillRunning) { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue }

    if (-not $stillRunning -or $hasTraceback) {
        Write-Host '--- stderr ---'
        Write-Host $stderrText
        throw "Launch check FAILED: process $(if (-not $stillRunning) {'exited early'} else {'logged a traceback'}) -- see stderr above"
    }
    Write-Host '  OK: process stayed alive 12s on stdio with no traceback (blocked waiting for MCP input, as expected)'
} finally {
    if (Test-Path $LaunchDir) { Remove-Item -Recurse -Force $LaunchDir -ErrorAction SilentlyContinue }
}

Step 11 'Clean up staging copy (derived, regenerable, never committed)'
Remove-Item -Recurse -Force $StageRoot

Write-Host "Done: $OutFile" -ForegroundColor Green
