# ============================================================
# run_array_tests.py — Jalankan test mac_array untuk N=4 dan N=8
# ------------------------------------------------------------
# Mendemonstrasikan kekuatan desain PARAMETRIK: satu file sumber,
# dua konfigurasi perangkat keras, dua hasil yang terverifikasi.
#
# Pemakaian:
#   python run_array_tests.py          -> uji 4x4 lalu 8x8
#   python run_array_tests.py --n 4    -> hanya 4x4
#   python run_array_tests.py --n 8    -> hanya 8x8
# ============================================================
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from cocotb_tools.runner import get_runner

HERE = Path(__file__).resolve().parent


def run_for_n(n: int) -> bool:
    print(f"\n{'='*64}")
    print(f"  MAC ARRAY {n}x{n}  ({n*n} unit MAC paralel)")
    print(f"{'='*64}")

    build_dir = HERE / f"sim_array_{n}x{n}"
    results = build_dir / "results.xml"

    runner = get_runner("icarus")
    runner.build(
        sources=[
            HERE / "src" / "mac_array.v",
            HERE / "src" / "mac_unit.v",
        ],
        hdl_toplevel="mac_array",
        parameters={"N": n},
        build_dir=build_dir,
        always=True,
        waves=True,
    )

    os.environ["ARRAY_N"] = str(n)
    crash = False
    try:
        runner.test(
            hdl_toplevel="mac_array",
            test_module="test_mac_array",
            test_dir=HERE / "tb",
            build_dir=build_dir,
            waves=True,
            results_xml=str(results),
            extra_env={"ARRAY_N": str(n)},
        )
    except RuntimeError:
        crash = True     # crash-on-exit Icarus (kosmetik, sudah diketahui)

    if not results.exists():
        print(f"  {n}x{n}: TIDAK ADA results.xml — gagal.")
        return False

    suite = ET.parse(results).getroot().find("testsuite")
    tests = int(suite.get("tests", 0))
    fails = int(suite.get("failures", 0))
    errs = int(suite.get("errors", 0))
    passed = tests - fails - errs

    if fails == 0 and errs == 0 and tests > 0:
        print(f"  {n}x{n}: LULUS — {passed}/{tests} test PASS")
        if crash:
            print("  (Icarus crash saat shutdown — kosmetik, hasil tetap valid)")
        return True
    else:
        print(f"  {n}x{n}: GAGAL — {passed}/{tests} PASS, {fails} FAIL, {errs} ERROR")
        return False


def main():
    target = None
    if "--n" in sys.argv:
        target = int(sys.argv[sys.argv.index("--n") + 1])
    sizes = [target] if target else [4, 8]

    hasil = {}
    for n in sizes:
        hasil[n] = run_for_n(n)

    print(f"\n{'='*64}")
    print("  RINGKASAN")
    print(f"{'='*64}")
    for n, ok in hasil.items():
        status = "LULUS" if ok else "GAGAL"
        print(f"  mac_array {n}x{n} ({n*n:2d} MAC paralel): {status}")
    print(f"{'='*64}")

    sys.exit(0 if all(hasil.values()) else 1)


if __name__ == "__main__":
    main()
