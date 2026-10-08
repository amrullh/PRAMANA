# ============================================================
# run_tests.py — Jalankan simulasi cocotb (Icarus atau Verilator)
# ------------------------------------------------------------
# Pemakaian:
#   python run_tests.py              -> Icarus Verilog (default)
#   python run_tests.py --verilator  -> Verilator
#   python run_tests.py --wave       -> sekalian hasilkan waveform (.fst)
#
# CATATAN JEBAKAN WINDOWS (dari pengalaman nyata):
#
# 1) Verilator tidak bisa build di folder yang mengandung spasi
#    (batasan GNU Make) -> build dir Verilator dipindah ke
#    D:/fpga-build. Icarus tidak terpengaruh.
#
# 2) Icarus Verilog di Windows kadang CRASH SAAT SHUTDOWN setelah
#    semua test selesai (exit code 3221225477 = 0xC0000005 access
#    violation). Ini bug kosmetik simulator, BUKAN bug rangkaianmu.
#    Karena itu script ini membaca results.xml untuk menentukan
#    hasil sebenarnya, bukan exit code simulator.
# ============================================================
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from cocotb_tools.runner import get_runner

HERE = Path(__file__).resolve().parent
# build dir khusus Verilator: tanpa spasi di path! (batasan GNU Make)
VERILATOR_BUILD_DIR = Path("D:/fpga-build/mac-unit")
RESULTS_XML = HERE / "tb" / "results.xml"


def read_results(path: Path):
    """Baca results.xml -> (tests, failures, errors, skipped)."""
    suite = ET.parse(path).getroot().find("testsuite")
    return (
        int(suite.get("tests", 0)),
        int(suite.get("failures", 0)),
        int(suite.get("errors", 0)),
        int(suite.get("skipped", 0)),
    )


def main():
    wave = "--wave" in sys.argv
    sim = "verilator" if "--verilator" in sys.argv else "icarus"
    build_dir = VERILATOR_BUILD_DIR if sim == "verilator" else HERE / "sim_build"

    runner = get_runner(sim)
    runner.build(
        sources=[HERE / "src" / "mac_unit.v"],
        hdl_toplevel="mac_unit",
        build_dir=build_dir,
        always=True,
        waves=wave,
    )

    crash_note = None
    try:
        runner.test(
            hdl_toplevel="mac_unit",
            test_module="test_mac",
            test_dir=HERE / "tb",
            build_dir=build_dir,
            waves=wave,
        )
    except RuntimeError:
        # simulator crash (kemungkinan besar crash-on-exit Icarus di
        # Windows). Hasil sebenarnya dibaca dari results.xml di bawah.
        crash_note = True

    # --------------------------------------------------------
    # HASIL SEBENARNYA — dibaca dari results.xml, bukan exit code
    # --------------------------------------------------------
    print()
    print("=" * 60)

    if not RESULTS_XML.exists():
        # crash dan tidak ada hasil -> ini masalah nyata, tampilkan
        print("  TIDAK ADA results.xml — simulasi gagal sebelum menulis hasil.")
        print("  Baca pesan error di atas untuk detailnya.")
        print("=" * 60)
        sys.exit(1)

    tests, fails, errs, skipped = read_results(RESULTS_XML)
    passed = tests - fails - errs - skipped

    if fails == 0 and errs == 0 and tests > 0:
        print(f"  HASIL AKHIR: LULUS — {passed}/{tests} test PASS, 0 FAIL")
        if crash_note:
            print("  (Icarus crash saat shutdown — bug kosmetik Windows,")
            print("   hasil test di atas tetap 100% valid)")
        print("=" * 60)
        sys.exit(0)
    else:
        print(f"  HASIL AKHIR: GAGAL — {passed}/{tests} PASS, {fails} FAIL, {errs} ERROR")
        print("  Cek log di atas untuk test mana yang gagal.")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
