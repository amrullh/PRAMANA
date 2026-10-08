// ============================================================
// tt_um_pramana.v — Wrapper Tiny Tapeout untuk PRAMANA
// PERURI Chip Hackathon 2026
// ------------------------------------------------------------
// MASALAH YANG DIPECAHKAN FILE INI:
//
// mac_unit punya port lebar: a[7:0], b[7:0], acc[31:0] = 48 bit
// sinyal. Tiny Tapeout hanya memberi 8 pin ui_in, 8 pin uo_out,
// dan 8 pin bidirectional uio — total 24 pin. Array 8x8 butuh
// 3075 bit sinyal, jadi mustahil dipasang langsung.
//
// SOLUSI: bagi peran pin sesuai JENIS pin, bukan menjejalkan
// semua lewat ui_in:
//
//   uio_in[7:0] -> DATA byte masuk (operan)  <-- pin bidirectional
//   uo_out[7:0] -> DATA byte keluar (hasil)
//   ui_in[7:0]  -> KONTROL saja
//
// Inilah pemakaian yang benar dari pin bidirectional: 8 pin data
// masuk lewat uio (kalau tidak dipakai akan sia-sia), bukan
// memaksa 8 bit data masuk lewat pin kontrol yang sempit.
//
// Protokol versi PERTAMA (data + alamat + kontrol semua di
// ui_in) GAGAL 6 dari 7 test: ui_in[0] jadi bit data sekaligus
// bit alamat, sehingga alamat ter-OR dengan data. Testbench yang
// menangkapnya. Pemisahan data/kontrol di atas menghapus kelas
// bug itu sepenuhnya, bukan menambal gejalanya.
//
// ------------------------------------------------------------
// PROTOKOL — ui_in (kontrol), uio_in (data masuk), uo_out (hasil):
//
//   ui_in[7]   ld_a   : 1 = a <= uio_in        (1 siklus)
//   ui_in[6]   ld_b   : 1 = b <= uio_in        (1 siklus)
//   ui_in[5]   commit : 1 = acc += a * b       (1 pulsa)
//   ui_in[4:3] b_idx  : byte akumulator di uo_out
//                       0 -> acc[7:0]     2 -> acc[23:16]
//                       1 -> acc[15:8]    3 -> acc[31:24]
//   ui_in[2:0] RESERVED: harus 0 (ada test khusus untuk ini)
//
// URUTAN PAKAI (4 siklus per operasi MAC):
//   1) ui_in=0x80, uio_in=a   -> a dimuat
//   2) ui_in=0x40, uio_in=b   -> b dimuat
//   3) ui_in=0x20             -> acc += a*b
//   4) ui_in=b_idx<<3         -> baca byte hasil di uo_out
//
// ATURAN PENTING (diuji, bukan sekadar ditulis di komentar):
//   ld_a/ld_b adalah REGISTER. commit harus dikirim pada siklus
//   TERPISAH setelah pemuatan terakhir. Kalau ld bersamaan
//   commit, MAC memakai operand SEBELUMNYA.
//   Test test_commit_same_cycle_uses_previous mengunci perilaku
//   ini secara eksplisit supaya tidak jadi kejutan di kemudian
//   hari — kalau protokol diubah, test itu yang memberi tahu.
//
// AKUMULATOR DI-NOL-KAN lewat pin rst_n: mac_unit memang tidak
// punya port clear. Satu pulsa reset mengosongkan akumulator DAN
// operand. Untuk menolkan akumulator di tengah jalan, pulsa rst_n.
//
// CATATAN JUJUR (batasan yang diketahui):
//   - 1 MAC per commit, bukan 64 MAC paralel seperti mac_array
//     8x8 (butuh 3075 bit, tidak mungkin masuk 24 pin).
//     Yang dipasang di sini satu mac_unit, aritmetikanya identik,
//     sudah 6/6 PASS sebagai modul mandiri.
//   - Belum ada pengukuran Fmax/daya (butuh Quartus).
//   - Belum dijalankan lewat flow resmi Tiny Tapeout (butuh
//     container Linux / GDS). Yang sudah diverifikasi: lint,
//     simulasi protokol, dan sintesis.
//
// Aritmetika TIDAK ditulis ulang di sini: wrapper ini
// menginstansiasi mac_unit yang sudah terverifikasi, supaya
// tidak ada dua sumber kebenaran untuk operasi MAC.
// ============================================================
`default_nettype none
`timescale 1ns/1ps

module tt_um_pramana (
    input  wire [7:0] ui_in,    // kontrol
    output wire [7:0] uo_out,   // data hasil
    input  wire [7:0] uio_in,   // data operan (masuk)
    output wire [7:0] uio_out,  // tidak dipakai
    output wire [7:0] uio_oe,   // arah pin uio (0 = input)
    input  wire       ena,      // 1 terus saat chip hidup
    input  wire       clk,      // clock
    input  wire       rst_n     // reset, aktif rendah
);

    // ------------------------------------------------------------
    // Dekode kontrol
    // ------------------------------------------------------------
    wire       ld_a   = ui_in[7];
    wire       ld_b   = ui_in[6];
    wire       commit = ui_in[5];
    wire [1:0] b_idx  = ui_in[4:3];

    // ------------------------------------------------------------
    // Register operand — di-latch langsung dari bus data uio_in
    // ------------------------------------------------------------
    reg signed [7:0] op_a;
    reg signed [7:0] op_b;

    always @(posedge clk) begin
        if (!rst_n) begin
            op_a <= 8'sd0;
            op_b <= 8'sd0;
        end else if (ld_a) begin
            op_a <= $signed(uio_in);
        end else if (ld_b) begin
            op_b <= $signed(uio_in);
        end
    end

    // ------------------------------------------------------------
    // Aritmetika: mac_unit yang sudah terverifikasi (6/6 PASS,
    // bit-exact vs golden model Python). Tidak ditulis ulang.
    // ------------------------------------------------------------
    wire signed [31:0] mac_acc;

    mac_unit u_mac (
        .clk   (clk),
        .rst_n (rst_n),
        .en    (commit),
        .a     (op_a),
        .b     (op_b),
        .acc   (mac_acc)
    );

    // ------------------------------------------------------------
    // Keluaran byte-serial dari akumulator
    // ------------------------------------------------------------
    reg [7:0] o_byte;
    always @(*) begin
        case (b_idx)
            2'd0:    o_byte = mac_acc[7:0];
            2'd1:    o_byte = mac_acc[15:8];
            2'd2:    o_byte = mac_acc[23:16];
            default: o_byte = mac_acc[31:24];
        endcase
    end

    assign uo_out  = o_byte;
    assign uio_oe  = 8'b0000_0000;   // semua pin uio: input
    assign uio_out = 8'd0;

    // Pin & sinyal tak terpakai -> ditandai supaya lint bersih
    wire _unused = &{ena, ui_in[2:0], 1'b0};

endmodule

`default_nettype wire
