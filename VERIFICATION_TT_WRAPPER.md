# ============================================================
# VERIFICATION_TT_WRAPPER.md
# Verifikasi wrapper Tiny Tapeout (tt_um_pramana)
# PRAMANA — PERURI Chip Hackathon 2026
# ------------------------------------------------------------
# Setiap angka di dokumen ini berasal dari perintah yang BENAR-
# BENAR dijalankan di mesin ini. Perintah + output disertakan
# supaya bisa diperiksa ulang.
# ============================================================

Tanggal: 8 Oktober 2026
Mesin: LENOVO, Windows 11, git-bash (MSYS), toolchain OSS CAD Suite

---

## 0. Kenapa wrapper ini ada

`mac_unit` punya port lebar (a[7:0], b[7:0], acc[31:0] = 48 bit).
Tiny Tapeout hanya memberi 24 pin (8 `ui_in` + 8 `uo_out` + 8 `uio`).
Array 8x8 butuh **3075 bit sinyal** — mustahil dipasang langsung.

Karena itu wrapper memetakan pin menurut JENIS pin:

| Pin TT | Dipakai untuk | Alasan |
|---|---|---|
| `uio_in[7:0]` | data operan masuk | 8 pin bidirectional yang kalau tidak dipakai jadi sia-sia |
| `uo_out[7:0]` | data hasil keluar | jalur output khusus |
| `ui_in[7:0]` | kontrol saja | tidak menjejalkan data ke pin kontrol yang sempit |

**Versi pertama protokol ini GAGAL 6 dari 7 test** — semua sinyal
(alamat bit, data bit, kontrol) dijejalkan ke `ui_in[7:0]`, sehingga
`ui_in[0]` menjadi bit data sekaligus bit alamat dan alamat ter-OR
dengan data. Pemisahan data (`uio_in`) dari kontrol (`ui_in`) di
versi final menghapus kelas bug itu, bukan menambal gejalanya.

---

## 1. Hasil simulasi protokol — 9/9 PASS

**Perintah:**
```bash
source /d/fpga-tools/activate.sh
cd "$HOME/Documents/PERURI Chip Hackathon 2026/rtl-starter"
"$PYTHON" run_tt_tests.py
```

**Output resmi (`sim_tt/results.xml`):**
```
TESTS=9 PASS=9 FAIL=0 SKIP=0    sim_time=4770.01 ns
```

| Test | Yang diperiksa | Status |
|---|---|---|
| `test_reset_zeros_acc` | acc = 0 setelah reset | PASS |
| `test_single_mac` | 2x3 = 6 lewat protokol penuh | PASS |
| `test_accumulate_and_latest_operand` | operand TERBARU dipakai, bukan nilai basi | PASS |
| `test_negative_operands` | -4x5 = -20, (-128)x(-128) benar | PASS |
| `test_accumulator_32bit` | 2 x 16384 = 32768 > batas 16-bit | PASS |
| `test_byte_read_order` | pembacaan byte little-endian konsisten | PASS |
| `test_commit_same_cycle_uses_previous` | aturan ld+commit satu siklus dikunci eksplisit | PASS |
| `test_reserved_pins_ignored` | `ui_in[2:0]` reserved tidak mengganggu | PASS |
| `test_vs_golden_model` | 40 vektor acak vs golden model Python, bit-exact | PASS |

**Yang dibuktikan:** protokol pin wrapper benar; operasi MAC lewat
wrapper bit-exact terhadap golden model Python.
**Yang TIDAK dibuktikan:** timing/frekuensi nyata — 100 MHz di
testbench adalah *setup simulasi*, bukan hasil pengukuran.

---

## 2. Lint Verilator `-Wall` — 0 warning

```bash
verilator_bin.exe --lint-only -Wall --top-module tt_um_pramana \
    src/tt_um_pramana.v src/mac_unit.v
# rc=0, 0 warning
```

Validitas lint dijaga **kontrol negatif**: file yang sengaja salah
(undefined signal) menghasilkan `rc=1` dengan perintah yang sama.
Tanpa kontrol itu, "0 warning" tidak bisa dibedakan dari "linter
tidak membaca filenya".

**Catatan penting:** lint harus diberi SELURUH modul sekaligus
(`tt_um_pramana.v` + `mac_unit.v`). Melint hanya file top memberi
`%Error-MODMISSING` karena submodul tidak ditemukan.

---

## 3. Sintesis

### 3a. Generik (GERBANG, bukan LE FPGA)

```bash
yosys -s synth/tt_um_pramana_synth.ys
```

```
=== design hierarchy ===
      881 tt_um_pramana     <- termasuk submodule
      805 mac_unit

      881 cells             <- total termasuk submodule
      394   $_AND_
      173   $_OR_
      244   $_XOR_
       48   $_SDFFE_PN0P_   <- 48 flip-flop
        8   $_MUX_
       14   $_NOT_
```

`76 cells` adalah **local count** wrapper sendiri (di luar submodule),
sehingga 76 + 805 = 881. Angka 881 yang boleh dikutip sebagai total.

**Angka ini TIDAK BOLEH dilaporkan sebagai pemakaian FPGA (LE/ALM)** —
satu sel generik bukan satu Logic Element.

### 3b. Target FPGA Cyclone V (angka yang bisa dipertanggungjawabkan)

```bash
yosys -s synth/tt_um_pramana_fpga.ys
```

```
       8 ports
      43 port bits
      54 cells
       3   $sdffe              <- register operand (a, b) + elemen lain
      19   MISTRAL_IB          <- input buffer
       1   MISTRAL_MUL9X9      <- pengali 8x8 -> 1 DSP BLOCK
      24   MISTRAL_OB          <- output buffer
      32   MISTRAL_ALUT_ARITH  <- akumulator 32-bit
```

| Temuan | Arti |
|---|---|
| `MISTRAL_MUL9X9` = 1 | pengali 8x8 diserap ke **1 DSP block**, bukan gerbang logika |
| `MISTRAL_ALUT_ARITH` = 32 | akumulator 32-bit ~32 ALM |
| `MISTRAL_IB`=19, `MISTRAL_OB`=24 | 43 buffer I/O — cocok dengan `43 port bits` |
| `8 ports` | **BUKAN 8 pin fisik** — chip butuh 43 pin sinyal |

**Kenapa sintesis berhenti di tahap `map_ffs`:** tahap ABC9 di
`synth_intel_alm` gagal di Windows karena masalah path temp (exit -2)
— bug tool, bukan desain. Semua keputusan pemetaan (DSP, ALM, FF)
sudah selesai sebelum tahap itu. Angka otoritatif tetap Quartus.

---

## 4. Cara mereproduksi semua angka di atas

```bash
source /d/fpga-tools/activate.sh
cd "$HOME/Documents/PERURI Chip Hackathon 2026/rtl-starter"

"$PYTHON" run_tt_tests.py                     # 9/9 PASS
yosys -s synth/tt_um_pramana_synth.ys         # 881 sel generik
yosys -s synth/tt_um_pramana_fpga.ys          # 1 DSP, 32 ALM, 43 bit

# lint (butuh path native, bukan /c/... — binary Windows)
verilator_bin.exe --lint-only -Wall --top-module tt_um_pramana \
    src/tt_um_pramana.v src/mac_unit.v
```

Log lengkap: `build/tt_generic_synth_log.txt`,
`build/tt_fpga_synth_log.txt`, `sim_tt/results.xml`.

---

## 5. Yang BELUM diverifikasi (jangan diklaim)

| Klaim | Status | Cara memverifikasi |
|---|---|---|
| Lolos flow resmi Tiny Tapeout (GDS) | **Belum** | container Linux + TT hardening flow |
| Frekuensi kerja nyata (Fmax) | **Belum diukur** | Static timing analysis (Quartus) |
| DSP block fisik setelah packing Quartus | **Belum** | Quartus Fitter |
| Daya (power) | **Belum diukur** | Quartus PowerPlay |
| 64 MAC paralel di dalam chip | **Belum** — wrapper ini 1 MAC/commit | pin budget 24 pin tidak memungkinkan |
| Akurasi model CNN penuh | **Belum** | butuh golden vectors dari model PyTorch |
| Integrasi SHA-256/PUF | **Belum dibuat** | modul terpisah belum ada |

---

## 6. Langkah berikutnya (urut nilai)

1. **Modul `info.yaml` versi PRAMANA** — supaya wrapper ini bisa
   masuk repo Tiny Tapeout dengan nama top module yang benar.
2. **Pipelining** — saat ini commit menunggu operand; penambahan
   register pipeline bisa menaikkan throughput tanpa menambah pin.
3. **Verifikasi array 8x8 lewat jalur berbeda** (mis. UART/UART
   host I/O TT07 #0012) kalau ingin mengekspos MAC paralel —
   karena 24 pin tidak akan pernah cukup untuk 3075 bit langsung.
4. **Quartus** untuk Fmax + DSP fisik, kalau waktunya ada.
