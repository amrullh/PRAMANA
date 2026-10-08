@echo off
rem ============================================================
rem  run_simulation.bat
rem  Jalankan simulasi cocotb untuk mac_unit (PRAMANA).
rem  CARA PAKAI: cukup KLIK DUA KALI file ini. Selesai.
rem  Tidak perlu mengetik perintah apa pun.
rem ============================================================
setlocal

set "OSS_ROOT=D:\fpga-tools\oss-cad-suite"
set "PYTHON=C:\Users\LENOVO\AppData\Local\Programs\Python\Python312\python.exe"
set "MINGW_BIN=C:\Users\LENOVO\scoop\apps\mingw\current\bin"

rem susun PATH: mingw (g++) + wrapper + oss-cad-suite + PATH lama
set "PATH=%MINGW_BIN%;D:\fpga-tools\bin;%OSS_ROOT%\bin;%OSS_ROOT%\lib;%PATH%"
set "VERILATOR_ROOT=%OSS_ROOT%\share\verilator"

rem pindah ke folder proyek (tempat run_tests.py berada)
cd /d "C:\Users\LENOVO\Documents\PERURI Chip Hackathon 2026\rtl-starter"

echo ============================================================
echo   SIMULASI RTL - mac_unit (PRAMANA)
echo ============================================================
echo.

"%PYTHON%" run_tests.py

echo.
echo ============================================================
echo   Selesai. Tekan tombol apa saja untuk menutup jendela ini.
echo ============================================================
pause >nul
