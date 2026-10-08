# SDC untuk mac_unit — clock constraint 50 MHz (target desain)
create_clock -name clk -period 20.000 [get_ports {clk}]
derive_clock_uncertainty
