module cocotb_iverilog_dump();
initial begin
    string dumpfile_path;    if ($value$plusargs("dumpfile_path=%s", dumpfile_path)) begin
        $dumpfile(dumpfile_path);
    end else begin
        $dumpfile("C:\\Users\\LENOVO\\Documents\\PERURI Chip Hackathon 2026\\rtl-starter\\sim_array_8x8\\mac_array.fst");
    end
    $dumpvars(0, mac_array);
end
endmodule
