@echo off
setlocal EnableDelayedExpansion
cd %~dp0
Runtime\python.exe app.py
pause