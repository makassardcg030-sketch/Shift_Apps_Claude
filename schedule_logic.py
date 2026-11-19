"""Logika jadwal shift fleksibel (murni Python, tanpa Kivy/Android)."""
import csv
import datetime as dt
import re

HARI = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"]

MONTHS = {
    "januari": 1, "january": 1, "jan": 1,
    "februari": 2, "february": 2, "feb": 2, "pebruari": 2,
    "maret": 3, "march": 3, "mar": 3,
    "april": 4, "apr": 4,
    "mei": 5, "may": 5,
    "juni": 6, "june": 6, "jun": 6,
    "juli": 7, "july": 7, "jul": 7,
    "agustus": 8, "august": 8, "agu": 8, "agt": 8, "aug": 8,
    "september": 9, "sep": 9, "sept": 9,
    "oktober": 10, "october": 10, "okt": 10, "oct": 10,
    "november": 11, "nopember": 11, "nov": 11,
    "desember": 12, "december": 12, "des": 12, "dec": 12,
}

class ScheduleError(Exception):
    pass

def _find_month(rows):
    for row in rows:
        for v in row:
            if isinstance(v, (dt.datetime, dt.date)):
                return v.year, v.month
            if isinstance(v, str):
                m = re.search(r"([A-Za-z]+)\.?\s*[-/ ]?\s*(\d{4})", v)
                if m and m.group(1).lower() in MONTHS:
                    return int(m.group(2)), MONTHS[m.group(1).lower()]
    raise ScheduleError("Judul bulan tidak ditemukan di baris atas file.")

def _day_number(v):
    if isinstance(v, (dt.datetime, dt.date)):
        return v.day
    try:
        f = float(str(v).strip())
    except (TypeError, ValueError):
        return None
    if f.is_integer() and 1 <= int(f) <= 31:
        return int(f)
    return None

DEFAULT_SHIFT_DEFS = {"P": (6,8), "Q": (6,5), "R": (11,8), "S": (14,8), "M": (22,8), "C": None, "OFF": None, "LIBUR": None}  # None = tidak kerja
# Format dinamis: {"P": (6,8), "S": (14,8), "M": (22,8), "C": None, "OFF": None}
# Kalau user tidak definisikan, fallback ke angka jam di Excel + durasi full/short.

def _as_variants(val):
    if val is None: return None
    if isinstance(val, (list, tuple)):
        if len(val) == 2 and all(isinstance(x, (int, float)) for x in val):
            return [(int(val[0]), int(val[1]))]
        out = []
        for item in val:
            if isinstance(item, (list, tuple)) and len(item) == 2:
                out.append((int(item[0]), int(item[1])))
        return out or None
    return None

LEGACY_ALIAS = {"P": "P1", "S": "S2", "M": "M1"}

def parse_defs_text(text):
    """Parse blok definisi. Satu kode = satu jam+durasi, tapi kode beda boleh banyak.
    P1=6,8 / P2=6,5 / S1=11,8 / C=CUTI / OFF=OFF / LIBUR=LIBUR
    Hasil: {"P1": [(6,8)], "C": None, "OFF": None, "LIBUR": None}"""
    out = {}
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line or "=" not in line: continue
        k, v = line.split("=", 1); k = k.strip().upper(); v = v.strip().upper()
        if v in ("LIBUR", "OFF", "CUTI", "C", "-", "", "NONE", "NULL"):
            out[k] = None; continue
        try: h, d = v.split(","); h = int(h); d = int(d)
        except Exception: continue
        if not (0 <= h <= 23 and 1 <= d <= 24): continue
        out[k] = [(h, d)]
    return out

def parse_code(v, off_words=("OFF", "LIBUR"), cuti_words=("C", "CUTI", "IZIN", "SAKIT"), shift_defs=None):
    # shift_defs dipakai untuk mengenali kode huruf baru (Q, R, dst) - jangan dibuang jadi X.
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, dt.datetime):
        v = v.time()
    if isinstance(v, dt.time):
        return str(v.hour)
    if isinstance(v, (int, float)):
        if float(v).is_integer() and 0 <= int(v) <= 23:
            return str(int(v))
        return "X"
    s = str(v).strip().upper()
    if not s:
        return None
    if s in off_words:
        return "OFF"
    if s in cuti_words:
        return "C"
    m = re.fullmatch(r"(\d{1,2})(?:[:.]00)?", s)
    if m and int(m.group(1)) <= 23:
        return str(int(m.group(1)))
    # Kode huruf (P/Q/R/S/M/dll) dipertahankan apa adanya.
    # build_entries() yang memutuskan: kalau ada di shift_defs -> dipakai,
    # kalau tidak ada -> dilewati. Jangan pernah jadi "X" lagi.
    # Kode P1/S2/M1 (huruf + angka) dan P/S/M lama dipertahankan apa adanya.
    if re.fullmatch(r"[A-Z]{1,3}", s) or re.fullmatch(r"[A-Z]{1,2}[0-9]{1,2}", s):
        return s
    return "X"

def parse_grid(rows, off_words=("OFF", "LIBUR"), cuti_words=("C", "CUTI", "IZIN", "SAKIT"), shift_defs=None):
    rows = [list(r) for r in rows]
    if not rows:
        raise ScheduleError("File kosong.")
    year, month = _find_month(rows[:6])

    hdr = name_col = None
    for ri, row in enumerate(rows[:10]):
        for ci, v in enumerate(row):
            if isinstance(v, str) and v.strip().lower() == "nama":
                hdr, name_col = ri, ci
                break
        if hdr is not None:
            break
    if hdr is None:
        raise ScheduleError("Kolom \"Nama\" tidak ditemukan.")

    day_row, day_cols = None, {}
    for ri in range(hdr, min(hdr + 4, len(rows))):
        cols = {}
        for ci in range(name_col + 1, len(rows[ri])):
            d = _day_number(rows[ri][ci])
            if d is not None:
                cols[ci] = d
        if len(cols) >= 28:
            day_row, day_cols = ri, cols
            break
    if day_row is None:
        raise ScheduleError("Baris tanggal (01..30) tidak ditemukan.")

    days = []
    for row in rows[day_row + 1:]:
        name = str(row[name_col] if name_col < len(row) else "").strip()
        if not name or name.lower() == "none":
            continue
        got = False
        for ci, d in day_cols.items():
            code = parse_code(row[ci] if ci < len(row) else None, off_words, cuti_words, shift_defs)
            if code is None:
                continue
            try:
                date = dt.date(year, month, d)
            except ValueError:
                continue
            days.append((date.isoformat(), name, code))
            got = True
        if not got:
            continue
    if not days:
        raise ScheduleError("Tidak ada data jadwal terbaca.")
    return "%04d-%02d" % (year, month), days


def _sniff_kind(path):
    """Tentukan 'xlsx' / 'csv' dari ekstensi, atau dari isi file bila ekstensi hilang
    (Google Drive / WhatsApp / Downloads kadang memberi nama tanpa .xlsx)."""
    lower = path.lower()
    if lower.endswith(".xlsx") or lower.endswith(".xlsm"):
        return "xlsx"
    if lower.endswith(".csv"):
        return "csv"
    with open(path, "rb") as f:
        head = f.read(4)
    if head[:2] == b"PK":
        return "xlsx"
    if head[:4] == b"\xd0\xcf\x11\xe0":
        raise ScheduleError("File .xls (format lama) tidak didukung. Simpan ulang sebagai .xlsx.")
    return "csv"


def load_days(path, off_words=("OFF", "LIBUR"), cuti_words=("C", "CUTI", "IZIN", "SAKIT"), shift_defs=None):
    kind = _sniff_kind(path)
    if kind == "csv":
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            sample = f.read(4096)
            f.seek(0)
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
            except csv.Error:
                dialect = csv.excel
            return parse_grid(list(csv.reader(f, dialect)), off_words, cuti_words, shift_defs)
    from openpyxl import load_workbook
    # read_only=False: lebih toleran terhadap xlsx hasil ekspor Google Sheets/Mac
    # (dimensi sheet / drawing yang tidak standar).
    # Dibuka lewat objek file: openpyxl menolak path yang tidak berakhiran .xlsx.
    with open(path, "rb") as fh:
        wb = load_workbook(fh, data_only=True)
        try:
            return parse_grid(list(wb.worksheets[0].iter_rows(values_only=True)),
                              off_words, cuti_words, shift_defs)
        finally:
            wb.close()


def merge_days(old, month_key, new, today=None, keep_days=60):
    kept = [d for d in old if not d[0].startswith(month_key)]
    merged = kept + list(new)
    if today:
        limit = (today - dt.timedelta(days=keep_days)).isoformat()
        merged = [d for d in merged if d[0] >= limit]
    return merged

def days_to_text(days):
    return "\n".join("|".join(d) for d in days)

def text_to_days(text):
    out = []
    for line in (text or "").splitlines():
        p = line.strip().split("|")
        if len(p) == 3:
            out.append((p[0], p[1], p[2]))
    return out

def build_entries(days, dur_full=8, dur_short=5, exact_full_run=5, shift_defs=None):
    """shift_defs: kode -> None | (jam,dur) | [(jam,dur)].
    Kode baru: P1,P2,... S1,S2,... M1,M2,... C, OFF, LIBUR. Semua jam+durasi bisa di-setting.
    ATURAN BLOK (dari user, menggantikan aturan run lama yang salah):
      - Cari BLOK kerja: hari-hari kerja berturut-turut yang DIAPIT 2 OFF
        (OFF / LIBUR / C di kedua ujungnya).
      - Blok 5 hari kerja -> hari TERAKHIR sebelum OFF dipaksa jadi 5 JAM.
        4 hari sebelumnya tetap sesuai definisi kodenya (mis. 8 jam).
      - Blok 6 hari kerja -> hari terakhir TETAP sesuai definisi (mis. 8 jam).
      - Blok panjang lain (1-4, 7+) -> tidak ada override, pakai definisi kode.
      - Blok yang tidak diapit 2 OFF (mis. terpotong awal/akhir bulan) -> tidak di-override,
        karena tidak terbukti "di antara 2 OFF".
    Contoh: OFF | P1 P1 P1 P1 P1 | OFF  -> 8,8,8,8,5
            OFF | P1 P1 P1 P1 P1 P1 | OFF -> 8,8,8,8,8,8
    """
    raw = shift_defs or {}
    defs = {}
    for k, v in raw.items():
        defs[str(k).upper()] = _as_variants(v)
    # Alias lama -> kode baru (hanya kalau kode lama tidak didefinisikan sendiri)
    for old, new_code in LEGACY_ALIAS.items():
        if old not in defs and new_code in defs:
            defs[old] = defs[new_code]
    # Peta jam_mulai -> durasi (untuk sel ANGKA di Excel, mis. sel berisi 6)
    start_map = {}
    for code, variants in defs.items():
        if variants:
            for (h, d) in variants:
                start_map.setdefault(h, []).append((code, d))
    OFF_SET = ("OFF", "LIBUR", "C", "CUTI", "IZIN", "SAKIT")
    order = {}; by_name = {}
    for date_iso, name, code in days:
        order.setdefault(name, len(order))
        by_name.setdefault(name, {})[dt.date.fromisoformat(date_iso)] = code
    one = dt.timedelta(days=1)
    entries = []
    entry_by_key = {}
    for name, m in by_name.items():
        for d, code in m.items():
            if code in OFF_SET:
                continue
            hour = dur = None
            if code in defs:
                variants = defs[code]
                if variants is None: continue
                hour, dur = variants[0]  # satu kode = satu jam+durasi (tidak ada lagi duplikat P)
            elif code.isdigit():
                hour = int(code)
                cands = start_map.get(hour, [])
                if len(cands) == 1: dur = cands[0][1]
                elif len(cands) > 1: dur = cands[0][1]  # angka ambigu -> varian pertama; pakai kode P1/S1 agar pasti
                else: dur = dur_full
            else:
                continue  # kode tak dikenal -> lewati, jangan jadi X
            e = {"date": d.isoformat(), "name": name, "hour": int(hour), "dur": int(dur), "_o": order[name]}
            entries.append(e); entry_by_key[(name, d)] = e
    # --- Terapkan ATURAN BLOK ---
    for name, m in by_name.items():
        dates = sorted(m.keys())
        i = 0
        while i < len(dates):
            if m[dates[i]] in OFF_SET:
                i += 1; continue
            j = i
            while j + 1 < len(dates) and dates[j+1] == dates[j] + one and m[dates[j+1]] not in OFF_SET:
                j += 1
            block = dates[i:j+1]
            prev_off = (block[0] - one) in m and m[block[0] - one] in OFF_SET
            next_off = (block[-1] + one) in m and m[block[-1] + one] in OFF_SET
            if prev_off and next_off and len(block) == 5:
                entry_by_key[(name, block[-1])]["dur"] = 5
            # len == 6 -> sengaja TIDAK diubah, tetap 8 jam (atau sesuai definisi)
            i = j + 1
    entries.sort(key=lambda e: (e["date"], e["hour"], e["_o"]))
    for e in entries: del e["_o"]
    return entries

def entries_to_text(entries, days=None):
    """Teks untuk widget. Satu baris per shift: tanggal|nama|jam|durasi.
    Jika `days` diberikan, hari tanpa shift ikut dikirim sebagai tanggal|nama|OFF atau
    tanggal|nama|CUTI (3 kolom) supaya widget personal bisa menampilkan OFF/CUTI/LIBUR
    pada jadwal akan datang, bukan melompat ke hari kerja berikutnya."""
    lines = ["%s|%s|%d|%d" % (e["date"], e["name"], e["hour"], e["dur"]) for e in entries]
    if days:
        for date_iso, name, code in sorted(days):
            if code == "OFF":
                lines.append("%s|%s|OFF" % (date_iso, name))
            elif code == "C":
                lines.append("%s|%s|CUTI" % (date_iso, name))
    return "\n".join(lines)

def _span(e):
    start = dt.datetime.fromisoformat(e["date"]) + dt.timedelta(hours=e["hour"])
    return start, start + dt.timedelta(hours=e["dur"])

def compute(entries, now):
    spans = [(_span(e), e) for e in entries]
    duty_entries = sorted([e for (s, en), e in spans if s <= now < en], key=lambda e: e["hour"])
    duty = [(e["name"], "%02d+%d" % (e["hour"], e["dur"])) for e in duty_entries]
    future = [s for (s, _), _e in spans if s > now]
    nxt = []
    if future:
        first = min(future)
        label = first.strftime("%H:%M") if first.date() == now.date() \
            else "%s %s" % (HARI[first.weekday()], first.strftime("%H:%M"))
        nxt = [(e["name"], label) for (s, _), e in sorted(spans, key=lambda x: x[1]["hour"]) if s == first]
    return duty, nxt