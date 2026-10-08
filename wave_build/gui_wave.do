# ============================================================
# gui_wave.do — tampilan gelombang tb_wave (untuk screenshot)
# ------------------------------------------------------------
# Dipakai oleh buka_questa_gui.bat:
#   vsim -gui -voptargs="+acc" tb_wave -do gui_wave.do
#
# Menampilkan clock, kontrol, dan nilai bertanda a/b/acc,
# lalu menjalankan seluruh simulasi (0-125 ns) + zoom penuh.
# ============================================================

onerror {resume}

add wave -noupdate -divider "kontrol"
add wave -noupdate -radix binary /tb_wave/clk
add wave -noupdate -radix binary /tb_wave/rst_n
add wave -noupdate -radix binary /tb_wave/en

add wave -noupdate -divider "data INT8 (desimal bertanda)"
add wave -noupdate -radix signed /tb_wave/a
add wave -noupdate -radix signed /tb_wave/b
add wave -noupdate -radix signed /tb_wave/acc

# jalankan simulasi sampai selesai (berhenti di $finish, 125 ns)
run -all

# tampilkan seluruh rentang waktu di jendela Wave
catch {wave zoom full}
