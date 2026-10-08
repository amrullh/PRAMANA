# ============================================================
# mac_unit_quartus.tcl — Alur Quartus untuk mac_unit (Fmax nyata)
# PERURI Chip Hackathon 2026 — PRAMANA
# Target: Cyclone V SE 5CSEBA6U23I7 (DE10-Nano), family Cyclone V
# ============================================================
package require ::quartus::project
package require ::quartus::flow
package require ::quartus::sta

set proj_dir "C:/Users/LENOVO/Documents/PERURI Chip Hackathon 2026/rtl-starter/quartus"
file mkdir $proj_dir
cd $proj_dir

project_new mac_unit_q -overwrite

set_global_assignment -name FAMILY "Cyclone V"
set_global_assignment -name DEVICE 5CSEBA6U23I7
set_global_assignment -name TOP_LEVEL_ENTITY mac_unit
set_global_assignment -name VERILOG_FILE "../src/mac_unit.v"
set_global_assignment -name PROJECT_OUTPUT_DIRECTORY output_files
set_global_assignment -name EDA_SIMULATION_TOOL "Questa Intel FPGA (Verilog)"
set_global_assignment -name NUM_PARALLEL_PROCESSORS 4

# SDC di file terpisah
set_global_assignment -name SDC_FILE mac_unit.sdc

project_close

puts "PROJECT CREATED OK"
