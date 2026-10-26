@echo off
rem Private Buffy sp00nznet build. Usage: build.cmd [target ...]  (default: all)
setlocal
set "VS=C:\Programming\VisualStudio\2026\Community"
call "%VS%\Common7\Tools\VsDevCmd.bat" -arch=amd64 -host_arch=amd64 >nul
if errorlevel 1 exit /b 1
cd /d "%~dp0"
if not exist build\build.ninja (
  cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=RelWithDebInfo -DCMAKE_C_COMPILER=cl
  if errorlevel 1 exit /b 1
)
if "%~1"=="" (
  cmake --build build --parallel 8
) else (
  cmake --build build --parallel 8 --target %*
)
exit /b %errorlevel%
