@echo off
rem Serve this folder and open the game in the default browser.
cd /d "%~dp0"
start "" http://localhost:8770/
python -m http.server 8770 --bind 127.0.0.1
