"""Membuat contoh_jadwal.xlsx dengan tata letak seperti jadwal asli (hanya untuk uji coba)."""
import datetime as dt
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

ROWS = [
 ("2013051606", "Dirlan", "14 11 8 6 6 off 22 14 14 8 6 off 22 22 14 14 11 6 off 22 22 14 14 11 6 off 22 22 14 14"),
 ("2013159109", "Alwyd",  "off 22 22 14 11 8 6 off C C C C C 8 off 8 8 8 8 6 8 off 8 8 8 8 6 off 8 8"),
 ("2015158719", "Cum",    "22 14 14 11 8 6 off 22 22 14 14 6 6 off 22 22 14 14 11 6 off 22 22 14 14 11 8 6 off 22"),
 ("2015400447", "Ichzan", "8 8 6 off 22 22 14 8 6 6 off 22 22 14 6 6 off 22 22 14 14 11 off 22 22 14 14 11 6 off"),
 ("2015385065", "Asrul",  "6 6 off 22 14 14 8 off 22 22 14 14 11 8 8 6 off 22 14 8 off 6 6 6 off 14 14 8 6 off"),
 ("2015698380", "Yasid",  "14 14 11 6 off 22 22 22 8 11 6 off 14 14 14 11 8 8 off 11 11 6 off 22 22 14 14 11 8 6"),
]
YEAR, MONTH, N = 2026, 11, 30
HARI = ["SEN", "SEL", "RAB", "KAM", "JUM", "SAB", "MIN"]

wb = Workbook()
ws = wb.active
ws["A1"] = "November 2026"
ws["A1"].font = Font(bold=True, size=14)
yellow = PatternFill("solid", fgColor="FFFF00")
red = PatternFill("solid", fgColor="FF0000")
green = PatternFill("solid", fgColor="00B050")
for c, t in ((1, "NIK"), (2, "Nama")):
    ws.cell(2, c, t).fill = yellow
    ws.cell(3, c).fill = yellow
    ws.merge_cells(start_row=2, start_column=c, end_row=3, end_column=c)
    ws.cell(2, c).font = Font(bold=True)
    ws.cell(2, c).alignment = Alignment(horizontal="center", vertical="center")
for d in range(1, N + 1):
    wd = dt.date(YEAR, MONTH, d).weekday()
    a = ws.cell(2, 2 + d, HARI[wd]); b = ws.cell(3, 2 + d, "%02d" % d)
    for x in (a, b):
        x.fill = yellow; x.font = Font(bold=True); x.alignment = Alignment(horizontal="center")
for r, (nik, nama, cells) in enumerate(ROWS, start=4):
    vals = cells.split()
    assert len(vals) == N, (nama, len(vals))
    ws.cell(r, 1, nik); ws.cell(r, 2, nama)
    for d, v in enumerate(vals, start=1):
        c = ws.cell(r, 2 + d)
        if v.isdigit():
            c.value = int(v)
        else:
            c.value = v
            c.fill = red if v == "off" else green
            c.font = Font(bold=True, color="FFFFFF")
        c.alignment = Alignment(horizontal="center")
ws.column_dimensions["A"].width = 13
import os
wb.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "contoh_jadwal.xlsx"))
print("ok")
