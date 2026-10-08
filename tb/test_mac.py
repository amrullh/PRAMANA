# ============================================================
# test_mac.py — Testbench cocotb untuk mac_unit
# ------------------------------------------------------------
# Konsep penting: GOLDEN MODEL.
# Kita hitung hasil yang BENAR di Python dulu (golden model),
# lalu bandingkan dengan hasil sirkuit Verilog (DUT = Device
# Under Test). Kalau beda satu angka pun -> ada bug di RTL.
# Pola inilah yang dipakai untuk seluruh verifikasi PRAMANA.
#
# CATATAN RACE CONDITION (penting, dibaca!):
# Kalau input diubah TEPAT pada saat clock naik, simulator bisa
# "menangkap" nilai lama atau baru -> hasil tidak deterministik.
# Solusinya pola standar:
#   1. Ubah input saat clock TURUN (FallingEdge)
#   2. Baca output setelah clock naik + ReadOnly() (tunggu
#      semua update register selesai)
# Ini pelajaran pertama yang harus dilalui semua orang RTL. :)
# ============================================================
import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, ReadOnly


async def start_clock(dut):
    """Nyalakan clock 10 ns (100 MHz) dan reset DUT."""
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    dut.rst_n.value = 0
    dut.en.value = 0
    dut.a.value = 0
    dut.b.value = 0
    for _ in range(3):
        await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    await ReadOnly()


async def drive(dut, a, b, en=1):
    """Masukkan satu pasangan operand dengan aman (saat clock turun)."""
    await FallingEdge(dut.clk)
    dut.en.value = en
    dut.a.value = a
    dut.b.value = b
    await RisingEdge(dut.clk)      # di sini DUT mengakumulasi
    await ReadOnly()               # tunggu sampai hasilnya benar-benar settle


@cocotb.test()
async def test_reset(dut):
    """Setelah reset, akumulator harus 0."""
    await start_clock(dut)
    got = dut.acc.value.to_signed()
    assert got == 0, f"acc harus 0 setelah reset, dapat {got}"


@cocotb.test()
async def test_accumulate_manual(dut):
    """Uji sederhana dengan angka yang gampang dicek manual.

    2 x 3 = 6, lalu + (-4 x 5) = -20  -> total -14
    """
    await start_clock(dut)

    await drive(dut, 2, 3)
    got = dut.acc.value.to_signed()
    assert got == 6, f"harus 6, dapat {got}"

    await drive(dut, -4, 5)
    got = dut.acc.value.to_signed()
    assert got == -14, f"harus -14, dapat {got}"


@cocotb.test()
async def test_enable_low_holds_value(dut):
    """Kalau enable = 0, akumulator harus menahan nilai (tidak berubah)."""
    await start_clock(dut)

    await drive(dut, 6, 7)
    before = dut.acc.value.to_signed()          # 42

    # masukkan operand baru tapi en = 0 -> nilai harus tetap 42
    await drive(dut, 100, 100, en=0)
    after = dut.acc.value.to_signed()
    assert after == before, f"acc harus tetap {before}, tapi berubah jadi {after}"


@cocotb.test()
async def test_vs_golden_model(dut):
    """Uji acak: bandingkan DUT vs golden model Python, bit-exact."""
    await start_clock(dut)

    rng = random.Random(42)            # seed tetap -> hasil bisa direproduksi
    golden = 0                         # golden model: hitungan Python

    for i in range(500):
        a = rng.randint(-128, 127)
        b = rng.randint(-128, 127)

        await drive(dut, a, b)

        golden += a * b                # yang benar menurut Python
        got = dut.acc.value.to_signed()  # yang keluar dari Verilog

        assert got == golden, (
            f"iterasi {i}: DUT={got} != golden={golden} (a={a}, b={b})"
        )

    dut._log.info("500 vektor lolos — DUT bit-exact dengan golden model Python")


@cocotb.test()
async def test_accumulator_needs_32bit(dut):
    """Bukti NYATA bahwa akumulator butuh 32 bit.

    Catatan penting (koreksi dari review):
    (-128)*(-128) = 16384 MASIH MUAT di signed 16-bit (maks 32767).
    Jadi satu perkalian ekstrem saja TIDAK membuktikan apa-apa.
    Yang benar-benar butuh 32 bit: akumulasi BERULANG dari hasil
    perkalian terbesar -> 2 x 16384 = 32768, yang melampaui 32767.
    Test inilah yang membuktikannya.
    """
    await start_clock(dut)

    await drive(dut, -128, -128)              # acc = 16384 (masih aman di 16-bit)
    assert dut.acc.value.to_signed() == 16384

    await drive(dut, -128, -128)              # acc = 32768 -> MELUAP kalau hanya 16-bit
    got = dut.acc.value.to_signed()
    assert got == 32768, f"harus 32768, dapat {got}"
    dut._log.info("32768 > batas 16-bit (32767) -> akumulator 32-bit memang diperlukan")


@cocotb.test()
async def test_negative_extremes(dut):
    """Uji nilai ekstrem INT8: penanganan tanda (-128 x -128).

    Test ini memverifikasi OPERASI INT8 x INT8 benar dan hasilnya
    ter-sign-extend dengan tepat — BUKAN bukti kebutuhan akumulator
    32 bit (lihat test_accumulator_needs_32bit untuk itu).
    """
    await start_clock(dut)

    await drive(dut, -128, -128)      # (-128) * (-128) = 16384
    got = dut.acc.value.to_signed()
    assert got == 16384, f"harus 16384, dapat {got}"

    await drive(dut, -128, 127)       # 16384 + (-16256) = 128
    got = dut.acc.value.to_signed()
    assert got == 128, f"harus 128, dapat {got}"
