@echo off
cd /d %~dp0\..\dashboard
call npm install
call npm run dev
