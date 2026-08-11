@echo off
chcp 65001 >nul
title ACM校队管理系统

echo ============================================
echo   ACM校队管理系统 - 启动中...
echo ============================================
echo.

cd /d "%~dp0"

:: Install dependencies if needed
pip install -r requirements.txt -q 2>nul

:: Init database if not exists
python seed.py 2>nul

echo.
echo >>> [生产模式] 服务器启动: http://0.0.0.0:5000
echo.

python run.py --prod
pause
