# Install semester-kit skills into %USERPROFILE%\.claude\skills (overwrites older versions of these skills only).
#   .\install.ps1
$ErrorActionPreference = 'Stop'
$target = Join-Path $env:USERPROFILE '.claude\skills'
New-Item -ItemType Directory -Force $target | Out-Null
Get-ChildItem (Join-Path $PSScriptRoot 'skills') -Directory | ForEach-Object {
    $dst = Join-Path $target $_.Name
    if (Test-Path $dst) { Remove-Item $dst -Recurse -Force }
    Copy-Item $_.FullName $dst -Recurse
    "installed $($_.Name)"
}
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { Write-Warning 'Python not found in PATH – install Python 3.10+ (python.org, "Add to PATH")' }
else { & python -m pip install --quiet python-docx pymupdf openpyxl python-pptx latex2mathml lxml }
'Done. Restart Claude, open a session in an empty semester folder and run /semester-init'
