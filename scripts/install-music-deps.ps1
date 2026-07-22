param([switch]$All, [switch]$Minimal)
# Install music generation backends for songgeneration-mcp
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

Write-Host "=== songgeneration-mcp: Install Music Backends ===" -ForegroundColor Cyan

# Always install base
Write-Host "-> Installing base dependencies..." -ForegroundColor Yellow
uv sync

if ($Minimal) {
    Write-Host "  Minimal mode: only Studio API (no local models)" -ForegroundColor Green
    exit 0
}

# MusicGen (transformers)
Write-Host "-> Installing MusicGen (HuggingFace)..." -ForegroundColor Yellow
uv add transformers scipy

# Stable Audio Open (diffusers)
Write-Host "-> Installing Stable Audio Open (diffusers)..." -ForegroundColor Yellow
uv add diffusers soundfile

# Lyria (google-genai SDK, only if GOOGLE_CLOUD_PROJECT is set)
if ($env:GOOGLE_CLOUD_PROJECT) {
    Write-Host "-> Installing Lyria (Google Vertex AI)..." -ForegroundColor Yellow
    uv add google-genai
}

# Verify
Write-Host "-> Verifying imports..." -ForegroundColor Yellow
uv run python -c "
try:
    from diffusers import StableAudioPipeline; print('  [OK] diffusers (Stable Audio)')
except: print('  [--] diffusers not installed')
try:
    from transformers import AutoProcessor; print('  [OK] transformers (MusicGen)')
except: print('  [--] transformers not installed')
try:
    from google.genai import Client; print('  [OK] google-genai (Lyria)')
except: print('  [--] google-genai not installed')
"

Write-Host "=== Done ===" -ForegroundColor Green
Write-Host "Backend chain: Lyria -> Stable Audio -> MusicGen -> Studio API"
Write-Host "First load will download models (~2-3GB each)"
