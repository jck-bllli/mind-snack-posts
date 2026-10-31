# Renders night_town.mp4 on the home PC. Run from this folder in PowerShell.
$ErrorActionPreference = "Stop"
if (-not (Test-Path node_modules\three)) { npm init -y | Out-Null; npm i three@0.170 playwright@1 }
npx playwright install chromium
python -m pip install --quiet numpy
if (Test-Path frames) { Remove-Item -Recurse -Force frames }
node render.js frames 30 5
python audio.py
$ff = if (Get-Command ffmpeg -ErrorAction SilentlyContinue) { "ffmpeg" } else { "C:\ffmpeg\bin\ffmpeg.exe" }
& $ff -v error -y -framerate 30 -i frames/f%04d.png -i audio.wav -vf "scale=1080:1920:flags=neighbor,eq=saturation=1.35:contrast=1.12:brightness=0.02,vignette=PI/5" -c:v libx264 -pix_fmt yuv420p -crf 20 -maxrate 12M -bufsize 24M -c:a aac -b:a 128k -ac 2 -shortest -movflags +faststart night_town.mp4
Write-Host "done: night_town.mp4"
