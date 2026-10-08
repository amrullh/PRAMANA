# Makefile — alternatif menjalankan simulasi mac_unit
# Pemakaian:
#   make          -> jalankan semua test
#   make synth    -> sintesis generik (jumlah gerbang)
#   make fpga     -> sintesis target Cyclone V (ALM/DSP/FF)
#   make clean    -> hapus hasil build
#
# CATATAN: Makefile ini HANYA berfungsi kalau folder proyek tidak
# mengandung spasi. Folder sekarang ("PERURI Chip Hackathon 2026")
# ADA spasinya -> GNU Make akan gagal. Gunakan run_tests.py /
# run_simulation.bat sebagai gantinya. Makefile ini disimpan untuk
# dokumentasi dan untuk dipakai kalau repo dipindah ke path tanpa spasi.

TOPLEVEL_LANG := verilog
SIM           ?= icarus

VERILOG_SOURCES := $(PWD)/src/mac_unit.v
TOPLEVEL        := mac_unit
MODULE          := test_mac

include $(shell cocotb-config --makefiles)/Makefile.sim

synth:
	yosys -s synth/mac_unit.ys

fpga:
	yosys -s synth/mac_unit_fpga.ys

clean::
	rm -rf sim_build results.xml __pycache__ tb/__pycache__ build/*.v
