# Run the agent with the project virtual environment (recommended).
$Root = $PSScriptRoot
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Host "Creating virtual environment..."
    python -m venv (Join-Path $Root ".venv")
}

$DepsMarker = Join-Path $Root ".venv\.deps-installed"
if (-not (Test-Path $DepsMarker)) {
    Write-Host "Installing dependencies..."
    & $VenvPython -m pip install -r (Join-Path $Root "requirements.txt") -q
    New-Item -ItemType File -Path $DepsMarker -Force | Out-Null
}

if ($args.Count -gt 0 -and $args[0] -eq "ui") {
    & $VenvPython -m streamlit run (Join-Path $Root "app.py")
} else {
    & $VenvPython (Join-Path $Root "main.py") @args
}
