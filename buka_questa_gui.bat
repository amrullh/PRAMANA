@echo off
rem ============================================================
rem  buka_questa_gui.bat
rem  Buka QUESTA (jendela penuh) + langsung jalankan simulasi
rem  tb_wave, dengan jendela Wave sudah terisi gelombang.
rem
rem  CARA PAKAI: klik dua kali. Tidak perlu mengetik apa pun.
rem  Setelah terbuka: jendela "Wave" di tengah layar sudah
rem  menampilkan clock dan nilai naik-turun untuk di-screenshot.
rem ============================================================
setlocal

set "QUESTA_BIN=C:\altera_standard\25.1std\questa_fse\win64"
set "SALT_LICENSE_SERVER=C:/Users/LENOVO/questa_lic.dat"
set "PATH=%QUESTA_BIN%;%PATH%"

cd /d "C:\Users\LENOVO\Documents\PERURI Chip Hackathon 2026\rtl-starter\wave_build"

echo ============================================================
echo   Membuka Questa GUI - simulasi tb_wave (PRAMANA mac_unit)
echo   Jendela Wave akan otomatis terbuka dan terisi gelombang.
echo ============================================================
echo.

vlib work >nul 2>nul
vlog -quiet ..\src\mac_unit.v ..\tb\tb_wave.v
vsim -gui -voptargs="+acc" tb_wave -do gui_wave.do

echo.
echo Questa telah ditutup.
pause >nul
