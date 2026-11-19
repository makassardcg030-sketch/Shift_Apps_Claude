# jalankan.py - Launcher Shift_App (V3, perbaiki error openpyxl)
# Cara pakai: python jalankan.py
# Aman untuk di-push ke GitHub: tidak ada path laptop / password / data pribadi.
#
# KENAPA VERSI LAMA GAGAL?
# Versi lama baru cek modul hilang SETELAH main.py jalan. Padahal main.py
# menangkap error openpyxl dan hanya menampilkannya di label status
# ("Gagal membaca file... No module named openpyxl"), jadi app tidak crash
# dan launcher kira semuanya normal. Versi baru ini cek DULU sebelum jalan.
import subprocess, sys, importlib.util
from pathlib import Path

FOLDER_PROJECT = Path(__file__).parent
FILE_UTAMA = FOLDER_PROJECT / "main.py"

# Modul yang WAJIB ada agar semua fitur jalan. openpyxl = baca .xlsx
WAJIB = {
    "kivy": "kivy",
    "openpyxl": "openpyxl",
    "et_xmlfile": "et_xmlfile",
}

print("=== MENJALANKAN Shift_App ===")
print(f"File: {FILE_UTAMA.name}")

if not FILE_UTAMA.exists():
    print("❌ File main.py tidak ditemukan di folder ini.")
    sys.exit(1)

hilang = [nama for nama in WAJIB if importlib.util.find_spec(nama) is None]
if hilang:
    print()
    print("=" * 52)
    print(f"❌ MODUL BELUM TERINSTALL: {', '.join(hilang)}")
    print("=" * 52)
    print("Tanpa modul ini, file Excel (.xlsx) TIDAK BISA dibaca.")
    print("Error yang muncul di aplikasi:")
    print(f"  Gagal membaca file (ModuleNotFoundError): No module named '{hilang[0]}'")
    print()
    print("Perintah manual (kalau mau install sendiri):")
    for h in hilang:
        print(f"  python -m pip install {WAJIB[h]}")
    print()
    tanya = input("Mau langsung saya install-in sekarang? (y/n): ").strip().lower()
    if tanya != "y":
        print("Dibatalkan. Install manual dulu, lalu jalankan lagi: python jalankan.py")
        sys.exit(1)
    for h in hilang:
        print(f"Menginstall {WAJIB[h]}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", WAJIB[h]])
    print("✅ Berhasil! Menjalankan aplikasi...")

hasil = subprocess.run([sys.executable, str(FILE_UTAMA)], capture_output=True, text=True, cwd=FOLDER_PROJECT)
if hasil.stdout:
    print(hasil.stdout)
if hasil.stderr:
    print(hasil.stderr)
else:
    print("✅ Berjalan tanpa error.")
