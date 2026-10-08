@echo off
rem ============================================================
rem  run_questa_tests.bat
rem  Jalankan simulasi cocotb mac_unit pakai Questa FSE.
rem  CARA PAKAI: cukup KLIK DUA KALI file ini. Selesai.
rem
rem  Yang di-set otomatis di sini:
rem   - SALT_LICENSE_SERVER -> file license Questa milikmu
rem   - PATH -> folder vsim/vlog/vlib Questa
rem ============================================================
setlocal

set "QUESTA_BIN=C:\altera_standard\25.1std\questa_fse\win64"
set "SALT_LICENSE_SERVER=C:/Users/LENOVO/questa_lic.dat"
set "PYTHON=C:\Users\LENOVO\AppData\Local\Programs\Python\Python312\python.exe"

set "PATH=%QUESTA_BIN%;%PATH%"

cd /d "C:\Users\LENOVO\Documents\PERURI Chip Hackathon 2026\rtl-starter"

echo ============================================================
echo   SIMULASI RTL via QUESTA - mac_unit (PRAMANA)
echo ============================================================
echo.

"%PYTHON%" run_questa_tests.py

echo.
echo ============================================================
echo   Selesai. Tekan tombol apa saja untuk menutup jendela ini.
echo ============================================================
pause >nul
