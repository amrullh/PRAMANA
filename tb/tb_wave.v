// ============================================================
// tb_wave.v — Testbench gelombang untuk mac_unit (PRAMANA)
// ------------------------------------------------------------
// Tujuan: merekam gelombang nyata (VCD) dari simulasi mac_unit
// untuk keperluan gambar di proposal.
//
// Vektor stimulus terinspirasi test_mac.py (testbench cocotb yang
// lulus 6/6), tetapi akumulasi di sini KONTINU tanpa reset antar
// tahap — seperti pemakaian nyata pada array MAC:
//   1) reset            -> acc = 0
//   2) 2 x 3            -> acc = 6
//   3) + (-4 x 5)       -> acc = -14      (turun; perkalian negatif)
//   4) enable = 0       -> acc TAHAN di -14
//   5) + 6 x 7          -> acc = 28       (naik)
//   6) + (-128 x -128)  -> acc = 16412    (naik tajam; +16384)
//   7) + (-128 x -128)  -> acc = 32796    (lewati batas 16-bit 32767!)
//   8) + (-128 x 127)   -> acc = 16540    (turun; perkalian negatif)
//   Setelah itu enable = 0 -> nilai tahan sampai simulasi selesai.
//
// Clock 100 MHz (periode 10 ns) -> clock yang sama dengan
// test_mac.py ("nyalakan clock 10 ns").
// ============================================================
`timescale 1ns/1ps

module tb_wave;

    reg               clk   = 1'b0;
    reg               rst_n = 1'b0;
    reg               en    = 1'b0;
    reg signed [7:0]  a     = 8'sd0;
    reg signed [7:0]  b     = 8'sd0;
    wire signed [31:0] acc;

    // ------------------------------------------------------------
    // DUT: satu unit MAC INT8
    // ------------------------------------------------------------
    mac_unit dut (
        .clk   (clk),
        .rst_n (rst_n),
        .en    (en),
        .a     (a),
        .b     (b),
        .acc   (acc)
    );

    // clock 100 MHz: periode 10 ns, naik tiap 5 ns
    always #5 clk = ~clk;

    // ------------------------------------------------------------
    // Rekaman gelombang -> wave.vcd
    // ------------------------------------------------------------
    initial begin
        $dumpfile("wave.vcd");
        $dumpvars(0, tb_wave);
    end

    // ------------------------------------------------------------
    // Satu langkah: tulis operand saat clock TURUN (biar bebas
    // race condition), lalu biarkan clock NAIK mengakumulasi.
    // ------------------------------------------------------------
    task drive(input signed [7:0] av, input signed [7:0] bv, input integer ev);
        begin
            @(negedge clk);
            a  = av;
            b  = bv;
            en = ev[0];
            @(posedge clk);   // <- di sini acc bertambah
        end
    endtask

    // ------------------------------------------------------------
    // Urutan stimulus
    // ------------------------------------------------------------
    initial begin
        // reset: tahan 3 detak, lalu lepas saat clock turun
        rst_n = 0;
        repeat (3) @(posedge clk);
        @(negedge clk);
        rst_n = 1;

        drive(   2,    3, 1);   // acc = 6
        drive(  -4,    5, 1);   // acc = -14   (turun)
        drive( 100,  100, 0);   // en=0 -> tahan di -14
        drive(   6,    7, 1);   // acc = 28    (naik)
        drive(-128, -128, 1);   // acc = 16412 (+16384)
        drive(-128, -128, 1);   // acc = 32796 -> lewati batas 16-bit!
        drive(-128,  127, 1);   // acc = 16540 (turun)

        // Matikan enable supaya akumulasi berhenti; clock tetap
        // jalan dua detak agar ujung gelombang terlihat bersih.
        @(negedge clk);
        en = 0;
        repeat (2) @(posedge clk);
        $finish;
    end

endmodule
