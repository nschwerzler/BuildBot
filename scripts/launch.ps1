# Launch AI Hub locally
# Usage: .\scripts\launch.ps1 [-Port 8765] [-Page store]

param(
    [int]$Port = 8765,
    [string]$Page
)

$root = Split-Path $PSScriptRoot -Parent
$url = "http://localhost:$Port/ai_platform.html"
if ($Page) { $url += "?page=$Page" }

# Kill any existing http-server on this port
Get-Process -Name node -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -match "http-server.*-p $Port" } |
    Stop-Process -Force -ErrorAction SilentlyContinue

# Start http-server in the background
$job = Start-Process -FilePath npx -ArgumentList "http-server `"$root`" -p $Port --cors -s" `
    -WindowStyle Hidden -PassThru

Write-Host "Server started on port $Port (PID $($job.Id))" -ForegroundColor Green
Write-Host "Opening $url" -ForegroundColor Cyan

Start-Process $url

Write-Host "Press Ctrl+C to stop the server."
try { Wait-Process -Id $job.Id }
catch { }
finally { Stop-Process -Id $job.Id -Force -ErrorAction SilentlyContinue }
