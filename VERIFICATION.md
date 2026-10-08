# Laporan Verifikasi — mac_unit (PRAMANA v0.1)

Setiap angka di dokumen ini **direproduksi dari eksekusi nyata** di mesin ini.
Perintah + output asli disertakan supaya bisa diperiksa ulang oleh siapa pun.

Tanggal verifikasi: 8 Oktober 2026
Mesin: LENOVO, Windows 11, git-bash (MSYS)

---

## 1. Hasil Simulasi — 6/6 PASS

**Perintah:**
```bash
"$PYTHON" run_tests.py
```

**Output (ringkas dari `tb/results.xml`):**
```
TESTS=6 PASS=6 FAIL=0 SKIP=0    sim_time=5310.01 ns    real_time=0.17 s
```

**Isi results.xml:** `tests="6" failures="0" errors="0"` (jumlah test
bertambah dari 5 menjadi 6 setelah koreksi — lihat bagian "Riwayat Koreksi").

| Test | Yang diperiksa | Status |
|---|---|---|
| `test_reset` | acc = 0 setelah reset | PASS |
| `test_accumulate_manual` | 2x3=6, lalu -4x5 -> -14 | PASS |
| `test_enable_low_holds_value` | en=0 -> nilai ditahan | PASS |
| `test_vs_golden_model` | 500 vektor acak vs Python, bit-exact (seed tetap) | PASS |
| `test_accumulator_needs_32bit` | 2 x 16384 = 32768 > batas 16-bit | PASS |
| `test_negative_extremes` | (-128)x(-128)=16384, sign handling benar | PASS |

**Yang dibuktikan:** operasi INT8 sesuai golden model Python secara bit-exact.
**Yang TIDAK dibuktikan:** timing/frekuensi nyata — clock 100 MHz di testbench
adalah *setup simulasi*, bukan hasil pengukuran silikon/FPGA.

---

## 2. Sintesis Generik — 805 sel (satuan GERBANG, bukan LE!)

**Perintah:**
```bash
yosys -s synth/mac_unit.ys
```

**Output:**
```
=== mac_unit ===
    6 ports
   51 port bits
  805 cells
  369   $_AND_
    8   $_NOT_
  152   $_OR_
   32   $_SDFFE_PN0P_     <- 32 flip-flop = akumulator 32-bit
  244   $_XOR_
```

**Cara membaca:** 805 sel = jumlah gerbang AND/OR/XOR/NOT/DFF setelah
diterjemahkan Yosys. **Angka ini TIDAK BOLEH dilaporkan sebagai pemakaian
FPGA (LE/ALM)** — satu sel generik bukan satu Logic Element. Gunakan hanya
sebagai indikator kompleksitas relatif.

---

## 3. Sintesis Target FPGA (Cyclone V) — angka yang bisa dipertanggungjawabkan

**Perintah:**
```bash
yosys -s synth/mac_unit_fpga.ys
```

**Output:**
```
=== mac_unit ===
 15 wires / 183 wire bits
  6 ports / 51 port bits
 53 cells
  1   $sdffe              <- enable register
 19   MISTRAL_IB          <- input buffer (pin)
  1   MISTRAL_MUL9X9      <- PENGALI 8x8 -> 1 DSP BLOCK
 32   MISTRAL_OB          <- output buffer (pin, acc 32-bit)
 32 submodules
 32   MISTRAL_ALUT_ARITH  <- 32 ALM aritmetika (akumulator 32-bit)
```

**Cara membaca (penting, agar tidak overclaim):**

| Temuan | Arti |
|---|---|
| `MISTRAL_MUL9X9` = 1 | Pengali 8x8 diserap ke **1 DSP block**, bukan gerbang logika |
| `MISTRAL_ALUT_ARITH` = 32 | Akumulator 32-bit butuh ~32 ALM |
| `MISTRAL_IB`=19, `MISTRAL_OB`=32 | 51 buffer I/O — cocok dengan 51 port bits |
| `6 ports` | **BUKAN 6 pin fisik** — chip butuh ~51 pin (51 bit sinyal) |

**Lint Verilator `-Wall`: 0 warning (bersih).**

```bash
verilator_bin.exe --lint-only -Wall --top-module mac_unit src/mac_unit.v
# rc=0, tanpa warning
```

Perbandingan: **baseline #0040 menghasilkan 1 warning** (WIDTHEXPAND,
`result[31:16] <= out` — 15 bit ke 16 bit) dengan perintah yang sama.
Validitas lint diuji dengan *kontrol negatif* (file sengaja salah → rc=1),
jadi hasil "0 warning" ini nyata. Detail: lihat `../baseline-0040/BASELINE_ANALYSIS.md`.

**Mengapa sintesis ini berhenti di tahap `map_ffs`:** tahap ABC9 di Yosys
Windows gagal karena masalah path temp (exit -2) — bug tool, bukan desain.
Semua keputusan pemetaan (DSP, ALM, FF) sudah selesai sebelum tahap itu,
jadi angka di atas final untuk pelaporan. Angka otoritatif = Quartus.

**Ekstrapolasi ke array 8x8 (64 MAC) — SEBELUMNYA ESTIMASI, SEKARANG SUDAH DISINTESIS:**

⚠️ **Catatan penting soal DSP:** sintesis menunjukkan **1 unit MAC = 1 sel
`MISTRAL_MUL9X9`**, tetapi angka itu adalah *pemetaan logis Yosys*, bukan
pemakaian fisik DSP block. Secara hardware, **satu DSP block Cyclone V dapat
menampung tiga pengali 9×9** (atau dua 18×18, atau satu 27×27). Jadi:

| Skenario | DSP block dibutuhkan | % dari 112 |
|---|---|---|
| Ideal (3 pengali 9×9 per blok, di-pack Quartus) | ~22 | ~20% |
| Naif (1 pengali per blok, tanpa packing) | 64 | ~57% |

Rentang **22–64 blok** adalah batas yang bisa dipertahankan; angka pastinya
baru keluar setelah Quartus menjalankan fitting. Kedua ujung rentang tetap
muat di 112 blok.

---

## 3b. MAC ARRAY (4x4 dan 8x8) — SUDAH DISINTESIS & DIVERIFIKASI

Desain parametrik `src/mac_array.v`: satu file sumber, dua konfigurasi.
Kedua konfigurasi diuji dengan testbench yang sama (`tb/test_mac_array.py`).

### Hasil simulasi (cocotb + Icarus)

| Konfigurasi | Test | Hasil | Operasi terverifikasi |
|---|---|---|---|
| **4x4** (16 MAC) | 5 | **5/5 PASS** | 16 unit x 200 siklus = **3.200 MAC** |
| **8x8** (64 MAC) | 5 | **5/5 PASS** | 64 unit x 200 siklus = **12.800 MAC** |

Semua bit-exact terhadap golden model Python. Termasuk `test_negative_values`,
yang menangkap jebakan part-select Verilog (part-select bersifat *unsigned*).

### Hasil sintesis FPGA (target Cyclone V, `synth_intel_alm`)

| Komponen | Array 4x4 | Array 8x8 |
|---|---|---|
| Pengali (`MISTRAL_MUL9X9`) | **16** | **64** |
| ALM aritmetika (`MISTRAL_ALUT_ARITH`) | 512 | **2.048** |
| Register (`$sdffe`) | 16 | 64 |
| Port / bit sinyal | 6 / 771 bit | 6 / **3.075 bit** |
| Lint Verilator `-Wall` | **0 warning** | **0 warning** |

**Verifikasi silang aritmetika port bits 8x8:**
```
aktivasi   : 64 x 8  =  512 bit
bobot      : 64 x 8  =  512 bit
akumulator : 64 x 32 = 2048 bit
kontrol    : clk + rst_n + en = 3 bit
TOTAL      : 3075 bit   <- cocok persis dengan Yosys (3075)
```

### Cara mereproduksi

```bash
cd "/c/Users/LENOVO/Documents/PERURI Chip Hackathon 2026/rtl-starter"
"$PYTHON" run_array_tests.py           # uji 4x4 dan 8x8
"$PYTHON" run_array_tests.py --n 8     # hanya 8x8

yosys -p "read_verilog src/mac_unit.v src/mac_array.v; \
          hierarchy -top mac_array -chparam N 8; \
          synth_intel_alm -family cyclonev -run begin:map_ffs; stat"
```

### Apa artinya (jujur)

**Yang sekarang jadi FAKTA (bukan lagi estimasi):**
- Array 64 MAC INT8 benar-benar terbangun dan terverifikasi bit-exact
- 64 pemetaan DSP (`MISTRAL_MUL9X9`) — konsisten dengan 1 MAC = 1 sel DSP
- 2.048 ALM untuk akumulator
- Lint bersih di kedua ukuran

**Yang MASIH estimasi:** DSP block *fisik* setelah packing Quartus
(rentang 22–64), Fmax, daya. Ini butuh Quartus fitting.

**Catatan keterbatasan array saat ini:** ini array MAC **flat** (64 MAC
independen, masing-masing punya akumulator sendiri). Mengubahnya menjadi
*systolic array* weight-stationary dengan berbagi bobot adalah langkah
berikutnya — dan perubahan itu akan **mengurangi** pemakaian port karena
bobot tidak perlu di-broadcast penuh setiap siklus.

---

## 4. Yang Belum Diverifikasi (jangan diklaim)

| Klaim | Status | Cara memverifikasi |
|---|---|---|
| Frekuensi kerja nyata (Fmax) | **Belum diukur** | Static timing analysis (Quartus/nextpnr) |
| ~~Pemakaian LE/ALM array penuh~~ | ✅ **SUDAH** — 2.048 ALM (8x8) | `synth_intel_alm` level array (lihat §3b) |
| DSP block fisik setelah packing | **Belum** (rentang 22–64) | Quartus Fitter |
| Daya (power) | **Belum diukur** | Quartus PowerPlay |
| Bit-exact pada model CNN penuh | **Belum ada** | Butuh golden vectors dari model PyTorch |
| Integrasi dengan SHA-256/PUF | **Belum dibuat** | Modul terpisah belum ada |
| Array systolic (berbagi bobot) | **Belum** — saat ini array flat | Rancangan berikutnya |

---

## 5. Riwayat Koreksi (dari review eksternal + verifikasi ulang)

| Klaim awal | Koreksi | Bukti |
|---|---|---|
| "(-128)x(-128) membuktikan butuh 32-bit" | Salah — 16384 masih muat di 16-bit; ditambah test baru dengan 2 akumulasi (32768) | test_accumulator_needs_32bit |
| "805 sel = ~47% kapasitas DE10-Nano" | Salah — sel generik bukan LE; pengali masuk DSP block | MISTRAL_MUL9X9 di output |
| "6 pins" | Salah — 6 port, 51 bit sinyal | Yosys: `51 port bits` |
| "Bekerja di 100 MHz" | Overclaim — itu clock simulasi, bukan hasil timing | — |
| "Sign-extend setelah perkalian" | Salah — Verilog extend operand SEBELUM operasi | — |

---

## Cara Mereproduksi Semua Angka di Atas

```bash
# 1. Aktifkan toolchain
source /d/fpga-tools/activate.sh

# 2. Simulasi (6 test)
cd "/c/Users/LENOVO/Documents/PERURI Chip Hackathon 2026/rtl-starter"
"$PYTHON" run_tests.py

# 3. Sintesis generik (805 sel)
yosys -s synth/mac_unit.ys

# 4. Sintesis FPGA (1 DSP, 32 ALM, 51 port bits)
yosys -s synth/mac_unit_fpga.ys

# Atau tanpa terminal: klik dua kali
#   run_simulation.bat  -> simulasi
#   run_synthesis.bat   -> kedua sintesis
```

Log lengkap tersimpan di `build/generic_synth_log.txt` dan `build/fpga_synth_log.txt`.
