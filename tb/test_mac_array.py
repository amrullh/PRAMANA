# ============================================================
# test_mac_array.py — Testbench cocotb untuk mac_array
# ------------------------------------------------------------
# Diuji untuk N=4 (16 MAC) DAN N=8 (64 MAC) — dari kode yang sama.
# Parameter N diambil dari environment variable ARRAY_N, yang
# di-set oleh runner. Itulah gunanya desain parametrik.
#
# Konsep verifikasi sama seperti test_mac.py:
#   golden model Python  vs  hasil sirkuit Verilog  -> bit-exact
#
# Untuk 64 MAC: 64 hasil dicek setiap siklus, 200 siklus.
# = 12.800 operasi MAC yang diverifikasi bit-exact.
# ============================================================
import os
import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, ReadOnly

# N diambil dari runner (ARRAY_N env var), default 4
N = int(os.environ.get("ARRAY_N", "4"))
TOTAL = N * N


async def start_clock(dut):
    """Nyalakan clock dan reset DUT."""
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    dut.rst_n.value = 0
    dut.en.value = 0
    dut.a_flat.value = 0
    dut.b_flat.value = 0
    for _ in range(3):
        await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    await ReadOnly()


def pack(values):
    """Kemas list INT8 -> integer flat (elemen i di bit i*8 +: 8)."""
    flat = 0
    for i, v in enumerate(values):
        flat |= (v & 0xFF) << (i * 8)
    return flat


def unpack(flat, width, count):
    """Baca flat integer -> list nilai signed."""
    result = []
    mask = (1 << width) - 1
    sign_bit = 1 << (width - 1)
    for i in range(count):
        v = (flat >> (i * width)) & mask
        if v & sign_bit:            # sign-extend manual
            v -= (1 << width)
        result.append(v)
    return result


async def drive(dut, a_list, b_list, en=1):
    """Masukkan satu set operand (aman: saat clock turun)."""
    await FallingEdge(dut.clk)
    dut.en.value = en
    dut.a_flat.value = pack(a_list)
    dut.b_flat.value = pack(b_list)
    await RisingEdge(dut.clk)
    await ReadOnly()


def get_acc(dut):
    """Baca acc_flat dari DUT sebagai list INT32 signed."""
    return unpack(int(dut.acc_flat.value), 32, TOTAL)


@cocotb.test()
async def test_array_reset(dut):
    """Semua akumulator harus 0 setelah reset."""
    await start_clock(dut)
    accs = get_acc(dut)
    assert all(a == 0 for a in accs), f"tidak semua 0 setelah reset: {accs}"


@cocotb.test()
async def test_all_units_parallel(dut):
    """SEMUA unit harus menghitung BERSAMAAN dalam satu siklus.

    Kalau array-nya tidak benar-benar paralel (misalnya ada unit
    yang tidak tersambung), test ini yang menangkapnya.
    """
    await start_clock(dut)

    # setiap unit dapat angka berbeda -> kalau ada yang ketuker, ketahuan
    a_vals = [i + 1 for i in range(TOTAL)]          # 1, 2, 3, ...
    b_vals = [2 for _ in range(TOTAL)]              # semua x2
    await drive(dut, a_vals, b_vals)

    accs = get_acc(dut)
    expected = [(i + 1) * 2 for i in range(TOTAL)]
    assert accs == expected, f"harus {expected}, dapat {accs}"


@cocotb.test()
async def test_negative_values(dut):
    """Nilai negatif harus tertangani di SETIAP unit array.

    Ini menguji jebakan part-select Verilog: part-select itu
    unsigned, jadi kalau tidak disalurkan lewat wire signed,
    -1 akan terbaca sebagai 255 dan test ini GAGAL.
    """
    await start_clock(dut)

    a_vals = [-128 if i % 2 == 0 else 127 for i in range(TOTAL)]
    b_vals = [-1 for _ in range(TOTAL)]
    await drive(dut, a_vals, b_vals)

    accs = get_acc(dut)
    expected = [(-128 if i % 2 == 0 else 127) * -1 for i in range(TOTAL)]
    assert accs == expected, f"harus {expected}, dapat {accs}"


@cocotb.test()
async def test_vs_golden_model(dut):
    """Uji acak: 200 siklus x N*N unit, bandingkan vs Python bit-exact."""
    await start_clock(dut)

    rng = random.Random(42)
    golden = [0] * TOTAL

    for cycle in range(200):
        a_vals = [rng.randint(-128, 127) for _ in range(TOTAL)]
        b_vals = [rng.randint(-128, 127) for _ in range(TOTAL)]

        await drive(dut, a_vals, b_vals)

        golden = [g + a * b for g, a, b in zip(golden, a_vals, b_vals)]
        got = get_acc(dut)

        assert got == golden, (
            f"siklus {cycle}: DUT != golden\n"
            f"  got    = {got}\n"
            f"  golden = {golden}"
        )

    dut._log.info(
        f"{N}x{N} array: {TOTAL} unit x 200 siklus = {TOTAL*200} operasi MAC "
        f"lolos — bit-exact dengan golden model Python"
    )


@cocotb.test()
async def test_enable_holds_all(dut):
    """en=0 harus menahan nilai SEMUA unit."""
    await start_clock(dut)

    await drive(dut, [3] * TOTAL, [7] * TOTAL)
    before = get_acc(dut)

    await drive(dut, [100] * TOTAL, [100] * TOTAL, en=0)
    after = get_acc(dut)

    assert after == before, f"nilai berubah saat en=0: {before} -> {after}"
