@echo off
rem Build TGP482 xbe_recomp + xbe_symbols for the Buffy probe into the PRIVATE workspace (never this repo).
rem Usage: Build-RecompHost.cmd <workspace root> [zydis src] [toml++ src]
rem   zydis/toml++ src default to BLACK's already-fetched copies (read only), so no network fetch is needed.
setlocal
set "WS=%~1"
if "%WS%"=="" set "WS=C:\Users\Public\App Developement\Decomps - Recomps"
set "SDK=%WS%\Tools\Sources\XboxXBERecomp-TGP482"
set "ZYDIS=%~2"
if "%ZYDIS%"=="" set "ZYDIS=%WS%\Projects\BLACK\build\host\_deps\zydis-src"
set "TOML=%~3"
if "%TOML%"=="" set "TOML=%WS%\Projects\BLACK\build\host\_deps\tomlplusplus-src"
set "OUT=%WS%\Projects\Buffy The Vampire Slayer\private\build\host"
set "VS=C:\Programming\VisualStudio\2026\Community"
call "%VS%\Common7\Tools\VsDevCmd.bat" -arch=amd64 -host_arch=amd64 >nul
if errorlevel 1 exit /b 1
set "CLANG=%VS%\VC\Tools\Llvm\x64\bin\clang-cl.exe"
cmake -S "%~dp0host-tools" -B "%OUT%" -G Ninja -DCMAKE_BUILD_TYPE=Release "-DCMAKE_C_COMPILER=%CLANG%" "-DCMAKE_CXX_COMPILER=%CLANG%" "-DXBE_SDK=%SDK%" "-DFETCHCONTENT_SOURCE_DIR_ZYDIS=%ZYDIS%" "-DFETCHCONTENT_SOURCE_DIR_TOMLPLUSPLUS=%TOML%" -DFETCHCONTENT_FULLY_DISCONNECTED=ON
if errorlevel 1 exit /b 1
cmake --build "%OUT%" --parallel 4
exit /b %errorlevel%
