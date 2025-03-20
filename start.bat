@echo off
setlocal EnableDelayedExpansion
cd %~dp0

:: 启动程序
Runtime\python.exe app.py

:: 等待几秒钟确保服务启动
echo Starting MTC-WebUI, please wait...
timeout /t 3 /nobreak > nul

:: 打开浏览器访问应用
start http://127.0.0.1:7860

pause