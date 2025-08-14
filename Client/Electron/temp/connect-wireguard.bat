@echo off
echo Starting WireGuard VPN connection...
cd /d "C:\Program Files\WireGuard"
wireguard.exe /installtunnelservice "C:\Users\hadip\AppData\Local\WireGuard\Configurations\GhostSwitch.conf"
echo WireGuard service installation completed with exit code %ERRORLEVEL%
exit /b %ERRORLEVEL%