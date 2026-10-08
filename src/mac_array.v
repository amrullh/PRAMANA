// ============================================================
// mac_array.v — Array MAC INT8 parametrik NxN
// Bagian dari PRAMANA — PERURI Chip Hackathon 2026
// ------------------------------------------------------------
// Ini upgrade dari mac_unit.v: N*N unit MAC yang bekerja
// PARALEL dalam satu siklus clock.
//
//   N=4  ->  16 MAC paralel   (versi fallback, aman)
//   N=8  ->  64 MAC paralel   (target utama PRAMANA)
//
// Kedua konfigurasi dibangun dari KODE YANG SAMA — hanya
// parameter N yang berbeda. Itu inti dari desain parametrik.
//
// Cara pakai:
//   mac_array #(.N(4)) dut (...);   // array 4x4
//   mac_array #(.N(8)) dut (...);   // array 8x8
//
// Antarmuka: vektor "flat".
//   a_flat   = N*N x INT8  (aktivasi)
//   b_flat   = N*N x INT8  (bobot)
//   acc_flat = N*N x INT32 (akumulator, satu per unit MAC)
// Elemen ke-i menempati bit [i*LEBAR +: LEBAR].
// ============================================================
`default_nettype none
`timescale 1ns/1ps

module mac_array #(
    parameter integer N = 4          // ukuran array: N x N
) (
    input  wire                       clk,       // clock
    input  wire                       rst_n,     // reset, aktif rendah
    input  wire                       en,        // enable global
    input  wire signed [N*N*8-1:0]    a_flat,    // N*N x INT8 (aktivasi)
    input  wire signed [N*N*8-1:0]    b_flat,    // N*N x INT8 (bobot)
    output wire signed [N*N*32-1:0]   acc_flat   // N*N x INT32 (hasil)
);

    // ------------------------------------------------------------
    // CATATAN PENTING SOAL VERILOG (kenapa butuh wire perantara):
    //
    // Part-select dari vector di Verilog bersifat UNSIGNED, meskipun
    // vector induknya signed. Jadi a_flat[i*8 +: 8] kehilangan tanda!
    // Solusinya: salurkan lewat wire signed [7:0] per elemen, supaya
    // nilai seperti 8'hFF benar-benar dibaca sebagai -1, bukan 255.
    //
    // (Ini jenis bug yang hanya ketahuan lewat test vektor negatif —
    //  makanya test_negative di testbench itu wajib, bukan pelengkap.)
    // ------------------------------------------------------------
    genvar i;
    generate
        for (i = 0; i < N*N; i = i + 1) begin : g_mac
            wire signed [7:0]  a_i;
            wire signed [7:0]  b_i;

            assign a_i = a_flat[i*8 +: 8];
            assign b_i = b_flat[i*8 +: 8];

            mac_unit u_mac (
                .clk   (clk),
                .rst_n (rst_n),
                .en    (en),
                .a     (a_i),
                .b     (b_i),
                .acc   (acc_flat[i*32 +: 32])
            );
        end
    endgenerate

endmodule

`default_nettype wire
