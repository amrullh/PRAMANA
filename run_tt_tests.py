# ============================================================
# run_tt_tests.py — Uji wrapper Tiny Tapeout (tt_um_pramana)
# ------------------------------------------------------------
# Pemakaian:
#   python run_tt_tests.py
#
# Yang dijalankan: 7 test protokol serial lewat cocotb + Icarus,
# termasuk test "operand basi" yang menangkap bug timing 1 siklus.
#
# Hasil resmi dibaca dari results.xml (bukan exit code), karena
# Icarus di Windows kadang crash saat menutup setelah test lulus.
# ============================================================
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from cocotb_tools.runner import get_runner

HERE = Path(__file__).resolve().parent
BUILD = HERE / "sim_tt"          # tanpa spasi di path (batasan GNU Make)
RESULTS = BUILD / "results.xml"


def main():
    # Hapus results.xml lama DULU. Kalau build gagal, file hasil run
    # sebelumnya akan tetap ada dan skrip ini bisa melaporkan "LULUS"
    # dari hasil BASI. Pernah terjadi: setelah tt_um_pramana.v
    # korup, results.xml lama masih terbaca sebagai lulus.
    if RESULTS.exists():
        RESULTS.unlink()

    runner = get_runner("icarus")
    try:
        runner.build(
            sources=[
                HERE / "src" / "tt_um_pramana.v",
                HERE / "src" / "mac_unit.v",
            ],
            hdl_toplevel="tt_um_pramana",
            build_dir=BUILD,
            always=True,
            waves=True,
        )
    except RuntimeError:
        print()
        print("=" * 64)
        print("  HASIL AKHIR: GAGAL - BUILD tidak selesai (compiler menolak RTL).")
        print("  Baca pesan error di atas. results.xml lama sudah dihapus,")
        print("  jadi tidak ada risiko hasil basi terbaca sebagai lulus.")
        print("=" * 64)
        sys.exit(1)

    crash = False
    try:
        runner.test(
            hdl_toplevel="tt_um_pramana",
            test_module="test_tt_um_pramana",
            test_dir=HERE / "tb",
            build_dir=BUILD,
            waves=True,
            results_xml=str(RESULTS),
        )
    except RuntimeError:
        crash = True     # crash-on-exit Icarus (kosmetik, sudah diketahui)

    print()
    print("=" * 64)

    if not RESULTS.exists():
        print("  TIDAK ADA results.xml. Simulasi gagal sebelum menulis hasil.")
        print("  Baca pesan error di atas untuk detailnya.")
        print("=" * 64)
        sys.exit(1)

    suite = ET.parse(RESULTS).getroot().find("testsuite")
    tests = int(suite.get("tests", 0))
    fails = int(suite.get("failures", 0))
    errs = int(suite.get("errors", 0))
    skipped = int(suite.get("skipped", 0))
    passed = tests - fails - errs - skipped

    if fails == 0 and errs == 0 and tests > 0:
        print(f"  HASIL AKHIR: LULUS ({passed} dari {tests} test PASS, 0 FAIL)")
        if crash:
            print("  (Icarus crash saat shutdown: bug kosmetik Windows,")
            print("   hasil di atas tetap valid)")
        print("=" * 64)
        sys.exit(0)

    print(f"  HASIL AKHIR: GAGAL ({passed} dari {tests} PASS, {fails} FAIL, {errs} ERROR)")
    print("  Cek log di atas untuk melihat test mana yang gagal.")
    print("=" * 64)
    sys.exit(1)


if __name__ == "__main__":
    main()
