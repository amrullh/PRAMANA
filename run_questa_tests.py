# ============================================================
# run_questa_tests.py — Jalankan test mac_unit dengan Questa FSE
# ------------------------------------------------------------
# Questa Altera Starter FPGA Edition (gratis, license ada di
# C:\Users\LENOVO\questa_lic.dat — fitur "intelqsimstarter").
#
# Pemakaian:  python run_questa_tests.py
#
# Kenapa ada file ini padahal sudah ada run_tests.py (Icarus)?
# Questa lebih "industri" dari Icarus: pesan error lebih jelas,
# mendukung Verilog + SystemVerilog + VHDL, dan waveform-nya
# bisa dibuka di Questa GUI. Icarus tetap dipakai untuk CI/cepat.
# ============================================================
import os
import re
import sys
from pathlib import Path

# --- setup environment (WAJIB sebelum import runner) ---
os.environ["SALT_LICENSE_SERVER"] = r"C:/Users/LENOVO/questa_lic.dat"
os.environ["PATH"] = (
    r"C:\altera_standard\25.1std\questa_fse\win64"
    + os.pathsep
    + os.environ.get("PATH", "")
)

HERE = Path(__file__).resolve().parent
BUILD = HERE / "sim_build_questa"
RESULTS = BUILD / "results.xml"

# cocotb runner menimpa PYTHONPATH dengan sys.path proses ini
# (lihat runner.py: self.env["PYTHONPATH"] = os.pathsep.join(sys.path)),
# jadi folder tb/ harus dimasukkan ke sys.path DI SINI, bukan via extra_env.
sys.path.insert(0, str(HERE / "tb"))


def main() -> int:
    # hapus results.xml lama supaya tidak ada risiko membaca hasil basi
    if RESULTS.exists():
        RESULTS.unlink()

    from cocotb_tools.runner import get_runner

    runner = get_runner("questa")
    print("=" * 64)
    print("  SIMULASI mac_unit via Questa Altera Starter FPGA Edition")
    print("=" * 64)

    runner.build(
        sources=[HERE / "src" / "mac_unit.v"],
        hdl_toplevel="mac_unit",
        build_dir=BUILD,
        always=True,
    )
    print("BUILD OK")

    failed = False
    try:
        runner.test(
            hdl_toplevel="mac_unit",
            test_module="test_mac",
            # JANGAN pakai test_dir=tb — vsim harus dijalankan dari folder
            # tempat library 'top' dibuat (build dir), kalau tidak:
            # "Failed to access library 'top'". Tes ditemukan lewat PYTHONPATH.
            test_dir=str(BUILD),
            build_dir=BUILD,
            extra_env={
                "PYTHONPATH": os.pathsep.join([str(HERE / "tb"), str(HERE)]),
            },
        )
    except Exception as exc:  # noqa: BLE001
        failed = True
        print(f"TEST exception: {exc}")

    print()
    print("=" * 64)
    if not RESULTS.exists():
        print("  TIDAK ADA results.xml — cek pesan error di atas.")
        print("=" * 64)
        return 1

    text = RESULTS.read_text()
    # cari <testsuite ...tests=...> (bukan <testsuites>) — cocotb menulis
    # <testsuites> wrapper di level atas, suite aslinya di dalamnya.
    m = re.search(r"<testsuite\s[^>]*tests=[^>]*>", text)
    print("  ", m.group(0) if m else text[:300])
    print("=" * 64)

    if m and 'failures="0"' in m.group(0) and 'errors="0"' in m.group(0):
        total = re.search(r'tests="(\d+)"', m.group(0))
        print(f"  HASIL AKHIR: LULUS — {total.group(1) if total else '?'} test PASS (dari results.xml)")
        return 0
    if failed:
        return 1
    return 1


if __name__ == "__main__":
    sys.exit(main())
