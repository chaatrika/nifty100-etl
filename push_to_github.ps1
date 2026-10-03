# push_to_github.ps1 - run from the project root in PowerShell:  .\push_to_github.ps1
# Puts this project on top of the existing repo history (no force-push).
$ErrorActionPreference = "Stop"
$repo = "https://github.com/chaatrika/nifty100-etl.git"

if (-not (Test-Path ".git")) { git init }
if (git remote) { git remote set-url origin $repo } else { git remote add origin $repo }

git fetch origin
git reset origin/main
git add -A
git status --short | Select-Object -First 25
Write-Host "`nCheck the list above (no .venv / .env). Press Enter to commit and push, Ctrl+C to cancel."
Read-Host | Out-Null

git commit -m "Final fixes: SIMULATED labels, 92 tearsheets, 11 sector reports"
git branch -M main
git push -u origin main
