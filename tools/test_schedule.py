"""Tes logika jadwal.  Jalankan dari folder proyek:  python3 tools/test_schedule.py"""
import datetime as dt
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, ROOT)
import schedule_logic as sl  # noqa: E402

key, days = sl.load_days(os.path.join(ROOT, "contoh_jadwal.xlsx"))
assert key == "2026-11" and len(days) == 180


def durs(entries, name):
    return {e["date"][-2:]: (e["hour"], e["dur"]) for e in entries if e["name"] == name}


ent = sl.build_entries(days)
d = durs(ent, "Dirlan")
assert d["11"] == (6, 8)    # 5 hari kerja di antara off 06 dan off 12 -> tetap +8
assert d["18"] == (6, 5)    # 6 hari kerja -> hari sebelum off +5
assert d["25"] == (6, 5)
assert d["15"] == (14, 8)   # hari biasa
assert d["30"] == (14, 8)   # hari terakhir bulan: besok tidak diketahui -> +8
assert d["05"] == (6, 5)    # rangkaian terpotong awal bulan -> tidak bisa dipastikan 5 hari

# Bulan sebelumnya diketahui: off 31 Okt -> 1..5 Nov persis 5 hari -> +8
e2 = sl.build_entries([("2026-10-31", "Dirlan", "OFF")] + days)
assert durs(e2, "Dirlan")["05"] == (6, 8)

# Persis kasus gambar widget: 15-Nov 17:29
duty, nxt = sl.compute(ent, dt.datetime(2026, 11, 15, 17, 29))
assert duty == [("Dirlan", "14+8"), ("Yasid", "14+8")], duty
assert nxt == [("Cum", "22:00")], nxt

# Shift malam melewati tengah malam
duty, _ = sl.compute(ent, dt.datetime(2026, 11, 16, 2, 0))
assert ("Cum", "22+8") in duty

# Simpan/baca & gabung
assert sl.text_to_days(sl.days_to_text(days)) == days
assert len(sl.merge_days(days, key, days, dt.date(2026, 11, 15))) == len(days)
print("semua tes lulus")
