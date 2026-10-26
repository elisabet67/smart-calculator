@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo 전자계산기를 실행하는 중입니다...
start pythonw main.py
if errorlevel 1 (
    echo [알림] 콘솔 모드로 재실행합니다.
    python main.py
    pause
)
exit
