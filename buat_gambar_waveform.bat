@echo off
rem ============================================================
rem  buat_gambar_waveform.bat
rem  Regenerasi gambar gelombang untuk proposal (Gambar 1).
rem  CARA PAKAI: klik dua kali. Selesai.
rem
rem  Langkah:
rem    [1/2] simulasi ulang tb_wave di Questa -> wave.vcd
rem    [2/2] parse wave.vcd -> waveform_mac.png
rem ============================================================
setlocal

set "QUESTA_BIN=C:\altera_standard\25.1std\questa_fse\win64"
set "SALT_LICENSE_SERVER=C:/Users/LENOVO/questa_lic.dat"
set "PYTHON=C:\Users\LENOVO\AppData\Local\Programs\Python\Python312\python.exe"
set "PATH=%QUESTA_BIN%;%PATH%"

cd /d "C:\Users\LENOVO\Documents\PERURI Chip Hackathon 2026\rtl-starter\wave_build"

echo ============================================================
echo   [1/2] Simulasi tb_wave di Questa
echo ============================================================
del /q wave.vcd 2>nul
vlib work >nul 2>nul
vlog -quiet ..\src\mac_unit.v ..\tb\tb_wave.v
if errorlevel 1 goto :gagal
vsim -quiet -voptargs="+acc" -c -do "run -all; quit" tb_wave
if errorlevel 1 goto :gagal

cd /d "C:\Users\LENOVO\Documents\PERURI Chip Hackathon 2026"

echo.
echo ============================================================
echo   [2/2] Bangun gambar waveform_mac.png
echo ============================================================
"%PYTHON%" pramana_waveform_figure.py
if errorlevel 1 goto :gagal

echo.
echo ============================================================
echo   Selesai. Gambar: waveform_mac.png (folder ini)
echo ============================================================
start "" "C:\Users\LENOVO\Documents\PERURI Chip Hackathon 2026\waveform_mac.png"
pause >nul
exit /b 0

:gagal
echo.
echo  [GAGAL] Baca pesan error di atas.
pause >nul
exit /b 1
