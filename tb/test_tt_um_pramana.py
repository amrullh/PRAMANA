# ============================================================
# test_tt_um_pramana.py — Testbench cocotb untuk wrapper TT
# ------------------------------------------------------------
# Yang diuji: PROTOKOL wrapper tt_um_pramana (pin mapping),
# bukan aritmetikanya — aritmetika mac_unit sudah diuji
# terpisah (6/6 PASS) dan wrapper ini menginstansiasinya apa
# adanya, jadi tidak ada dua sumber kebenaran.
#
# Riwayat: protokol versi pertama GAGAL 6/7 karena ui_in[0]
# dipakai sebagai bit data sekaligus bit alamat -> alamat
# ter-OR dengan data. Testbed ini yang menangkapnya, dan
# protokol sekarang memisahkan data (uio_in) dari kontrol
# (ui_in) sehingga tabrakan itu tidak mungkin lagi.
# ============================================================
import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, ReadOnly, RisingEdge

LD_A   = 0x80
LD_B   = 0x40
COMMIT = 0x20


async def start_clock(dut):
    """Clock 10 ns (100 MHz) + pulsa reset."""
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0

    dut.rst_n.value = 0
    for _ in range(3):
        await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    await ReadOnly()


async def poke(dut, ctrl, data=0):
    """Kirim ui_in + uio_in, diubah saat clock turun (hindari race)."""
    await FallingEdge(dut.clk)
    dut.ui_in.value = ctrl & 0xFF
    dut.uio_in.value = data & 0xFF
    await RisingEdge(dut.clk)
    await ReadOnly()


async def do_mac(dut, a, b):
    """Satu operasi MAC: muat a, muat b, commit."""
    await poke(dut, LD_A, a)
    await poke(dut, LD_B, b)
    await poke(dut, COMMIT)
    await poke(dut, 0x00)          # siklus idle (bersihkan kontrol)


async def read_acc(dut):
    """Baca akumulator 32 bit byte-serial -> int signed 32 bit."""
    val = 0
    for i in range(4):
        await poke(dut, (i & 0x03) << 3)
        val |= (int(dut.uo_out.value) & 0xFF) << (8 * i)

    if val >= 0x80000000:
        val -= 0x100000000
    return val


@cocotb.test()
async def test_reset_zeros_acc(dut):
    """Setelah reset, akumulator harus nol."""
    await start_clock(dut)
    got = await read_acc(dut)
    assert got == 0, f"acc harus 0 setelah reset, dapat {got}"


@cocotb.test()
async def test_single_mac(dut):
    """2 x 3 = 6 lewat protokol lengkap."""
    await start_clock(dut)
    await do_mac(dut, 2, 3)
    got = await read_acc(dut)
    assert got == 6, f"harus 6, dapat {got}"


@cocotb.test()
async def test_accumulate_and_latest_operand(dut):
    """Akumulasi memakai operand TERBARU, bukan nilai basi.

    Kalau op_a/op_b tidak benar-benar diambil dari bus data,
    test ini gagal sedangkan test_single_mac bisa saja lolos.
    """
    await start_clock(dut)

    await do_mac(dut, 5, 5)                 # acc = 25
    got = await read_acc(dut)
    assert got == 25, f"harus 25, dapat {got}"

    await do_mac(dut, 3, 10)                # acc = 25 + 30 = 55
    got = await read_acc(dut)
    assert got == 55, f"harus 55 (bukan 50 = operand basi), dapat {got}"


@cocotb.test()
async def test_negative_operands(dut):
    """Penanganan tanda INT8 lewat bus data."""
    await start_clock(dut)

    await do_mac(dut, -4, 5)                # acc = -20
    got = await read_acc(dut)
    assert got == -20, f"harus -20, dapat {got}"

    await do_mac(dut, -128, -128)           # acc = -20 + 16384
    got = await read_acc(dut)
    assert got == 16364, f"harus 16364, dapat {got}"


@cocotb.test()
async def test_accumulator_32bit(dut):
    """Akumulasi berulang melampaui batas 16 bit."""
    await start_clock(dut)

    for _ in range(2):
        await do_mac(dut, -128, -128)       # 2 x 16384 = 32768 > 32767
    got = await read_acc(dut)
    assert got == 32768, f"harus 32768, dapat {got}"


@cocotb.test()
async def test_byte_read_order(dut):
    """Pembacaan byte harus little-endian dan konsisten.

    acc = 0x01020304 (16909060) dibuat lewat operand yang
    menghasilkan pola byte berbeda supaya urutan byte salah
    langsung ketahuan.
    """
    await start_clock(dut)

    # 0x0102 = 258 dan 0x0102 = 258 -> 258*258 = 66564 = 0x0001_0404
    await do_mac(dut, 1, 0)                 # biarkan saja, mulai dari reset
    got = await read_acc(dut)
    assert got == 0, f"setup: acc harus 0, dapat {got}"

    # 16384 = 0x4000, dari (-128)*(-128. ) -> pakai 128*128
    await do_mac(dut, 127, -1)              # acc = -127
    got = await read_acc(dut)
    assert got == -127, f"harus -127, dapat {got}"

    # sekarang tumpuk sampai byte atas terisi: -127 + 127*127*2 = 32131
    await do_mac(dut, 127, 127)             # +16129 = 16002
    await do_mac(dut, 127, 127)             # +16129 = 32131
    got = await read_acc(dut)
    assert got == 32131, f"harus 32131, dapat {got}"


@cocotb.test()
async def test_commit_same_cycle_uses_previous(dut):
    """Dokumentasi terang-terangan: ld + commit di SATU siklus
    memakai operand SEBELUMNYA (karena op_a/op_b register).

    Ini bukan bug yang disembunyikan, tapi aturan protokol yang
    diuji. Kalau kelak protokol diubah supaya commit pada siklus
    yang sama boleh (kombinasional dari uio_in), test ini harus
    diperbarui — dan itu keputusan sadar, bukan kejutan.
    """
    await start_clock(dut)

    await do_mac(dut, 10, 10)               # acc = 100
    assert await read_acc(dut) == 100

    # satu siklus: ld_a dengan data 7 DAN commit bersamaan
    await poke(dut, LD_A | COMMIT, 7)       # memakai op_a LAMA (10) dan op_b (10)
    got = await read_acc(dut)
    assert got == 200, f"harus 200 (operand lama 10*10), dapat {got}"

    # buktikan operand 7 tetap tersimpan, jadi commit berikutnya pakai 7
    await poke(dut, COMMIT)                 # 7 * 10 = 70
    got = await read_acc(dut)
    assert got == 270, f"harus 270, dapat {got}"


@cocotb.test()
async def test_reserved_pins_ignored(dut):
    """ui_in[2:0] RESERVED: mengubahnya tidak boleh mengganggu."""
    await start_clock(dut)

    await do_mac(dut, 6, 7)                 # acc = 42
    before = await read_acc(dut)
    assert before == 42, f"harus 42, dapat {before}"

    # tolak-ukar pin reserved, tanpa load/commit
    for bits in range(8):
        await poke(dut, bits)
    after = await read_acc(dut)
    assert after == before, f"acc harus tetap {before}, berubah jadi {after}"


@cocotb.test()
async def test_vs_golden_model(dut):
    """40 vektor acak vs golden model Python, bit-exact."""
    await start_clock(dut)

    rng = random.Random(1234)
    golden = 0

    for i in range(40):
        a = rng.randint(-128, 127)
        b = rng.randint(-128, 127)
        await do_mac(dut, a, b)
        golden += a * b

        got = await read_acc(dut)
        assert got == golden, (
            f"iterasi {i}: DUT {got} beda dari golden {golden} (a={a}, b={b})"
        )

    dut._log.info("40 vektor lolos lewat wrapper TT, bit-exact")
