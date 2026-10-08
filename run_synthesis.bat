@echo off
rem ============================================================
rem  run_synthesis.bat
rem  Jalankan sintesis Yosys (generik + FPGA target Cyclone V).
rem  CARA PAKAI: klik dua kali file ini. Selesai.
rem ============================================================
setlocal

set "OSS_ROOT=D:\fpga-tools\oss-cad-suite"
set "PATH=%OSS_ROOT%\bin;%OSS_ROOT%\lib;%PATH%"

cd /d "C:\Users\LENOVO\Documents\PERURI Chip Hackathon 2026\rtl-starter"

echo ============================================================
echo   SINTESIS RTL - mac_unit (PRAMANA)
echo ============================================================
echo.

echo [1/2] Sintesis generik (jumlah sel)...
yosys -s synth/mac_unit.ys > build\generic_synth_log.txt 2>&1
echo      rc=%errorlevel%  -^> build\generic_synth_log.txt
echo.

echo [2/2] Sintesis FPGA target Cyclone V (DSP/ALM/FF)...
yosys -s synth/mac_unit_fpga.ys > build\fpga_synth_log.txt 2>&1
echo      rc=%errorlevel%  -^> build\fpga_synth_log.txt
echo.

echo === HASIL SINTESIS FPGA (angka yang bisa dikutip) ===
echo.
powershell -NoProfile -Command "Get-Content 'build\fpga_synth_log.txt' -Tail 24 | Select-String -Pattern 'ports|port bits|cells|MISTRAL' | Select-Object -Last 12"

echo.
echo === Angka ini juga terdokumentasi di VERIFICATION.md ===
echo.
echo ============================================================
echo   Selesai. Tekan tombol apa saja untuk menutup jendela ini.
echo ============================================================
pause >nul
