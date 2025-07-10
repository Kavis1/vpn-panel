# Setup script for VPN Panel Frontend (Based on Marzban)

# Clone Marzban frontend
Write-Host "Cloning Marzban frontend..." -ForegroundColor Cyan
if (Test-Path -Path "frontend") {
    Remove-Item -Recurse -Force frontend
}
git clone https://github.com/Gozargah/Marzban.git frontend

# Navigate to frontend directory
Set-Location frontend

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Cyan
npm install

# Create .env file with our configuration
Write-Host "Creating .env file..." -ForegroundColor Cyan
@"
VITE_API_BASE_URL=/api
VITE_APP_TITLE=VPN Panel
VITE_APP_DESCRIPTION=VPN Panel Management System
VITE_ENABLE_SIGNUP=false
VITE_DEFAULT_THEME=dark
"@ | Out-File -FilePath ".env" -Encoding utf8

# Modify package.json to match our project name
$packageJson = Get-Content "package.json" -Raw | ConvertFrom-Json
$packageJson.name = "vpn-panel-frontend"
$packageJson.version = "0.1.0"
$packageJson.description = "VPN Panel Frontend (Based on Marzban)"
$packageJson | ConvertTo-Json -Depth 10 | Out-File "package.json" -Encoding utf8

Write-Host "Frontend setup completed!" -ForegroundColor Green
Write-Host "To start the development server, run: cd frontend && npm run dev" -ForegroundColor Green
