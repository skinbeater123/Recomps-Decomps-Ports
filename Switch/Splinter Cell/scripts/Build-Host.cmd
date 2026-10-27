@echo off
setlocal
set "VS=C:\Programming\VisualStudio\2026\Community"
call "%VS%\Common7\Tools\VsDevCmd.bat" -arch=amd64 -host_arch=amd64 >nul
if errorlevel 1 exit /b 1
set "CLANG=%VS%\VC\Tools\Llvm\x64\bin\clang-cl.exe"
python "%~dp0generate.py" --prepare-only
if errorlevel 1 exit /b 1
python "%~dp0prepare_runtime.py"
if errorlevel 1 exit /b 1
"C:\Programming\CMake\bin\cmake.exe" -S "%~dp0.." -B "%~dp0..\build\host" -G Ninja -DCMAKE_BUILD_TYPE=Release "-DCMAKE_C_COMPILER=%CLANG%" "-DCMAKE_CXX_COMPILER=%CLANG%"
if errorlevel 1 exit /b 1
"C:\Programming\CMake\bin\cmake.exe" --build "%~dp0..\build\host" --target sc1 --parallel 4
exit /b %errorlevel%
