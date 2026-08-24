@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

set "PYTHON_LAUNCHER="
where py >nul 2>nul
if not errorlevel 1 set "PYTHON_LAUNCHER=py -3"
if not defined PYTHON_LAUNCHER (
  where python >nul 2>nul
  if not errorlevel 1 set "PYTHON_LAUNCHER=python"
)

if not defined PYTHON_LAUNCHER (
  echo [錯誤] 找不到 Python 3。
  echo 請先從 https://www.python.org/downloads/ 安裝 Python 3，再重新雙擊本檔案。
  pause
  exit /b 1
)

set "LOCAL_IP="
for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "$ip = Get-NetIPAddress -AddressFamily IPv4 ^| Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*' -and $_.PrefixOrigin -ne 'WellKnown' } ^| Sort-Object InterfaceMetric ^| Select-Object -First 1 -ExpandProperty IPAddress; if ($ip) { $ip }"`) do set "LOCAL_IP=%%I"

echo.
echo ========================================
echo   比手畫腳遊戲伺服器已準備啟動
echo ========================================
echo 本機開啟：http://localhost:8088
if defined LOCAL_IP echo 同 Wi-Fi 裝置：http://%LOCAL_IP%:8088
echo.
echo 請保留此視窗。結束時按 Ctrl+C 或關閉視窗。
echo.

start "" "http://localhost:8088"
%PYTHON_LAUNCHER% -m http.server 8088 --bind 0.0.0.0

if errorlevel 1 (
  echo.
  echo [錯誤] 伺服器無法啟動，可能是 8088 埠已被使用。
  pause
)
endlocal
