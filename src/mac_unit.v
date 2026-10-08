// ============================================================
// mac_unit.v — Satu unit Multiply-Accumulate (MAC) INT8
// Bagian dari PRAMANA — PERURI Chip Hackathon 2026
// ------------------------------------------------------------
// Ini blok paling dasar dari AI accelerator.
// Satu MAC = a x b + acc, dikerjakan sekali per detak clock.
// Nanti di PRAMANA, 64 unit ini disusun jadi array 8x8.
// ============================================================
`default_nettype none
`timescale 1ns/1ps

module mac_unit (
    input  wire               clk,     // clock
    input  wire               rst_n,   // reset, aktif rendah (0 = reset)
    input  wire               en,      // enable: 1 = akumulasi, 0 = tahan nilai
    input  wire signed [7:0]  a,       // operand 1 — bilangan INT8 (-128..127)
    input  wire signed [7:0]  b,       // operand 2 — bilangan INT8 (-128..127)
    output reg  signed [31:0] acc      // akumulator 32-bit (hasil penjumlahan)
);

    // Setiap naik clock:
    //   - kalau reset aktif  -> acc = 0
    //   - kalau en aktif     -> acc = acc + (a x b)
    //   - selain itu         -> acc menahan nilai (tidak berubah)
    //
    // Catatan aritmetika (dikoreksi setelah review):
    // Verilog mengekstensi tanda OPERAND (a dan b) ke lebar ekspresi
    // SEBELUM operasi dijalankan — bukan hasil perkaliannya setelah.
    // Hasilnya sama, tapi urutannya begitu: sign-extend dulu, baru hitung.
    // Itulah alasan hasil negatif tetap benar di akumulator 32-bit.
    always @(posedge clk) begin
        if (!rst_n)
            acc <= 32'sd0;
        else if (en)
            acc <= acc + (a * b);
    end

endmodule

`default_nettype wire
