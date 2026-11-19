import os
from datetime import date, datetime, timedelta

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.utils import platform

import schedule_logic as sl

PICK_REQUEST = 4711
PKG = "org.shiftapp.shiftapp"

# Pilihan Palet Tema Warna UI (Fleksibel / Poin 4)
THEMES = {
    "Slate Dark": {
        "BG_DARK": (0.06, 0.09, 0.16, 1),       # #0F172A Slate 900
        "CARD_BG": (0.12, 0.16, 0.23, 1),       # #1E293B Slate 800
        "CARD_BORDER": (0.20, 0.25, 0.33, 1),   # #334155 Slate 700
        "ACCENT_BLUE": (0.15, 0.39, 0.92, 1),   # #2563EB Royal Blue
    },
    "Midnight Blue": {
        "BG_DARK": (0.04, 0.06, 0.12, 1),
        "CARD_BG": (0.09, 0.13, 0.22, 1),
        "CARD_BORDER": (0.16, 0.22, 0.35, 1),
        "ACCENT_BLUE": (0.20, 0.50, 0.95, 1),
    },
    "Emerald Dark": {
        "BG_DARK": (0.05, 0.09, 0.07, 1),
        "CARD_BG": (0.10, 0.18, 0.14, 1),
        "CARD_BORDER": (0.18, 0.30, 0.24, 1),
        "ACCENT_BLUE": (0.06, 0.55, 0.35, 1),
    }
}

# Default Active Theme
CURRENT_THEME = THEMES["Slate Dark"]
BG_DARK = CURRENT_THEME["BG_DARK"]
CARD_BG = CURRENT_THEME["CARD_BG"]
CARD_BORDER = CURRENT_THEME["CARD_BORDER"]
ACCENT_BLUE = CURRENT_THEME["ACCENT_BLUE"]

ACCENT_CYAN = (0.02, 0.52, 0.78, 1)   # #0284C7 Sky 600
ACCENT_RED = (0.86, 0.15, 0.15, 1)    # #DC2626 Red 600
ACCENT_YELLOW = (0.98, 0.80, 0.08, 1) # #FACC15 Yellow 400
TEXT_PRIMARY = (0.97, 0.98, 0.99, 1)
TEXT_MUTED = (0.58, 0.64, 0.72, 1)
WHITE = (1, 1, 1, 1)
BLACK = (0.06, 0.09, 0.16, 1)

COL_WEIGHTS = (1.0, 1.6, 1.1, 1.6, 1.1)
Window.clearcolor = BG_DARK


class RoundedCard(BoxLayout):
    """Container kartu dengan sudut membulat."""
    def __init__(self, bg=CARD_BG, radius=14, **kwargs):
        super().__init__(**kwargs)
        self._bg = bg
        self._radius = dp(radius)
        with self.canvas.before:
            self._color = Color(*self._bg)
            self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[self._radius])
        self.bind(pos=self._sync, size=self._sync)

    def _sync(self, *_):
        self._rect.pos = self.pos
        self._rect.size = self.size
    def set_bg(self, bg):
        self._bg = bg; self._color.rgba = bg


class ModernButton(Button):
    """Tombol modern dengan sudut membulat."""
    def __init__(self, bg=ACCENT_BLUE, fg=WHITE, radius=10, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_down = ""
        self.background_color = (0, 0, 0, 0)
        self.color = fg
        self.bold = True
        self._bg = bg
        self._radius = dp(radius)
        with self.canvas.before:
            self._c = Color(*self._bg)
            self._r = RoundedRectangle(pos=self.pos, size=self.size, radius=[self._radius])
        self.bind(pos=self._sync, size=self._sync, state=self._on_state)

    def _sync(self, *_):
        self._r.pos = self.pos
        self._r.size = self.size

    def set_bg(self, bg):
        self._bg = bg; self._c.rgba = bg
    def _on_state(self, _, state):
        if state == "down":
            self._c.rgba = (self._bg[0] * 0.8, self._bg[1] * 0.8, self._bg[2] * 0.8, 1)
        else:
            self._c.rgba = self._bg


class Cell(Label):
    """Sel tabel pratinjau widget."""
    def __init__(self, text="", bg=WHITE, fg=BLACK, bold=False, **kwargs):
        super().__init__(
            text=text, color=fg, bold=bold, shorten=True,
            shorten_from="right", font_size=dp(12), **kwargs
        )
        with self.canvas.before:
            Color(*bg)
            self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(4)])
        self.bind(pos=self._sync, size=self._sync)
        self.bind(size=lambda *_: setattr(self, "text_size", self.size))
        self.halign = "center"
        self.valign = "middle"

    def _sync(self, *_):
        self._rect.pos = self.pos
        self._rect.size = self.size


class ShiftApp(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.entries = []
        self.days = []
        self._next_personal_start = None
        self._next_personal_name = ""

        # Konfigurasi Fleksibel (Poin 2 & 3)
        self.dur_full = 8
        self.dur_short = 5
        self.off_words = ("OFF", "LIBUR")
        self.cuti_words = ("C", "CUTI", "IZIN", "SAKIT")

        self._buttons = []
        self._cards = []
        self.current_theme_name = "Slate Dark"

        scroll = ScrollView(do_scroll_x=False)
        root = BoxLayout(
            orientation="vertical",
            padding=[dp(16), dp(20), dp(16), dp(24)],
            spacing=dp(14),
            size_hint_y=None
        )
        root.bind(minimum_height=root.setter("height"))

        # --- HEADER ---
        header = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(58), spacing=dp(2))
        lbl_title = Label(
            text="[b]Jadwal Shift & Alarm[/b]", markup=True,
            font_size=dp(24), color=TEXT_PRIMARY, halign="left", valign="middle"
        )
        lbl_title.bind(size=lambda *_: setattr(lbl_title, "text_size", lbl_title.size))
        lbl_sub = Label(
            text="Pantau shift tim & pasang alarm otomatis 1 jam sebelum tugas",
            font_size=dp(13), color=TEXT_MUTED, halign="left", valign="middle"
        )
        lbl_sub.bind(size=lambda *_: setattr(lbl_sub, "text_size", lbl_sub.size))
        header.add_widget(lbl_title)
        header.add_widget(lbl_sub)
        root.add_widget(header)

        # --- KARTU 1: UPLOAD FILE & TEMPLATE ---
        card_upload = RoundedCard(orientation="vertical", padding=dp(14), spacing=dp(10),
                                  size_hint_y=None, height=dp(160))
        
        row_btns = BoxLayout(spacing=dp(8), size_hint_y=None, height=dp(44))
        self.btn_upload = ModernButton(
            text="📂 Unggah Jadwal",
            bg=ACCENT_BLUE, size_hint_x=0.6, font_size=dp(14)
        )
        self._buttons.append(self.btn_upload)
        self.btn_upload.bind(on_press=self.open_picker)
        
        self.btn_template = ModernButton(
            text="⬇️ Unduh Template",
            bg=ACCENT_CYAN, size_hint_x=0.4, font_size=dp(13)
        )
        self.btn_template.bind(on_press=self.download_template)
        
        row_btns.add_widget(self.btn_upload)
        row_btns.add_widget(self.btn_template)
        card_upload.add_widget(row_btns)

        # Spinner Pengaturan Tema (Poin 4)
        row_theme = BoxLayout(spacing=dp(8), size_hint_y=None, height=dp(36))
        lbl_theme = Label(text="Tema Warna:", color=TEXT_MUTED, font_size=dp(12),
                          size_hint_x=None, width=dp(90), halign="left", valign="middle")
        lbl_theme.bind(size=lambda *_: setattr(lbl_theme, "text_size", lbl_theme.size))
        
        self.spinner_theme = Spinner(
            text="Slate Dark",
            values=list(THEMES.keys()),
            background_normal="",
            background_color=CARD_BORDER,
            color=TEXT_PRIMARY,
            font_size=dp(12)
        )
        self.spinner_theme.bind(text=self.change_theme)
        row_theme.add_widget(lbl_theme)
        row_theme.add_widget(self.spinner_theme)
        card_upload.add_widget(row_theme)

        self.lbl_status = Label(
            text="Belum ada file jadwal yang dimuat.",
            font_size=dp(12), color=TEXT_MUTED, halign="left", valign="middle",
            size_hint_y=None, height=dp(26)
        )
        self.lbl_status.bind(size=lambda *_: setattr(self.lbl_status, "text_size", self.lbl_status.size))
        card_upload.add_widget(self.lbl_status)
        root.add_widget(card_upload)

        # --- KARTU 2: PRATINJAU WIDGET 1 (TIM) ---
        card_team = RoundedCard(orientation="vertical", padding=dp(14), spacing=dp(8),
                                size_hint_y=None, height=dp(215))
        self._cards.append(card_team)
        lbl_w1 = Label(
            text="[b]Widget 1 • Jadwal Shift Tim[/b]  [color=#94A3B8](Tanpa Alarm)[/color]",
            markup=True, font_size=dp(14), color=TEXT_PRIMARY,
            size_hint_y=None, height=dp(24), halign="left", valign="middle"
        )
        lbl_w1.bind(size=lambda *_: setattr(lbl_w1, "text_size", lbl_w1.size))
        card_team.add_widget(lbl_w1)

        self.table = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(156), spacing=dp(3))
        top = BoxLayout(spacing=dp(3))
        self.lbl_today = Cell("", WHITE, ACCENT_RED, bold=True, size_hint_x=1.0)
        self.lbl_clock = Cell("", WHITE, ACCENT_RED, bold=True, size_hint_x=1.0)
        top.add_widget(Cell("HARI INI", WHITE, BLACK, bold=True, size_hint_x=0.8))
        top.add_widget(self.lbl_today)
        top.add_widget(Cell("Jam", WHITE, BLACK, bold=True, size_hint_x=0.6))
        top.add_widget(self.lbl_clock)
        self.table.add_widget(top)
        self.table.add_widget(self._row(("SHIFT", "Nama", "Jam", "Nama", "Jam"), ACCENT_RED, WHITE, True))
        self.duty_cells = self._row(("Duty:", "-", "", "", ""), ACCENT_CYAN, WHITE, True)
        self.next_cells = self._row(("Next:", "-", "", "", ""), ACCENT_YELLOW, BLACK, True)
        self.table.add_widget(self.duty_cells)
        self.table.add_widget(self.next_cells)
        card_team.add_widget(self.table)
        root.add_widget(card_team)

        # --- KARTU 3: PRATINJAU WIDGET 2 (PERSONAL + ALARM) ---
        card_personal = RoundedCard(orientation="vertical", padding=dp(14), spacing=dp(10),
                                    size_hint_y=None, height=dp(230))
        self._cards.append(card_personal)
        lbl_w2 = Label(
            text="[b]Widget 2 • Jadwal Personal & Alarm[/b]",
            markup=True, font_size=dp(14), color=TEXT_PRIMARY,
            size_hint_y=None, height=dp(24), halign="left", valign="middle"
        )
        lbl_w2.bind(size=lambda *_: setattr(lbl_w2, "text_size", lbl_w2.size))
        card_personal.add_widget(lbl_w2)

        row_select = BoxLayout(spacing=dp(8), size_hint_y=None, height=dp(40))
        lbl_pilih = Label(text="Pilih Nama:", color=TEXT_MUTED, font_size=dp(13),
                          size_hint_x=None, width=dp(80), halign="left", valign="middle")
        lbl_pilih.bind(size=lambda *_: setattr(lbl_pilih, "text_size", lbl_pilih.size))
        self.spinner_name = Spinner(
            text="Belum ada data",
            values=[],
            background_normal="",
            background_color=CARD_BORDER,
            color=TEXT_PRIMARY,
            font_size=dp(13.5),
            bold=True
        )
        self.spinner_name.bind(text=lambda *_: self.refresh())
        row_select.add_widget(lbl_pilih)
        row_select.add_widget(self.spinner_name)
        card_personal.add_widget(row_select)

        self.lbl_p_duty = Label(
            text="Duty: -", color=TEXT_PRIMARY, font_size=dp(13.5),
            size_hint_y=None, height=dp(26), halign="left", valign="middle"
        )
        self.lbl_p_duty.bind(size=lambda *_: setattr(self.lbl_p_duty, "text_size", self.lbl_p_duty.size))
        card_personal.add_widget(self.lbl_p_duty)

        self.lbl_p_next = Label(
            text="Next: -", color=ACCENT_YELLOW, bold=True, font_size=dp(13.5),
            size_hint_y=None, height=dp(26), halign="left", valign="middle"
        )
        self.lbl_p_next.bind(size=lambda *_: setattr(self.lbl_p_next, "text_size", self.lbl_p_next.size))
        card_personal.add_widget(self.lbl_p_next)

        self.btn_test_alarm = ModernButton(
            text="⏰  Set Alarm 1 Jam Sebelum Shift",
            bg=ACCENT_RED, size_hint_y=None, height=dp(42), font_size=dp(13.5)
        )
        self._buttons.append(self.btn_test_alarm)
        self.btn_test_alarm.bind(on_press=self.trigger_personal_alarm)
        card_personal.add_widget(self.btn_test_alarm)
        root.add_widget(card_personal)

        # --- KARTU 4: PANDUAN SINGKAT ---
        card_info = RoundedCard(orientation="vertical", padding=dp(14), size_hint_y=None, height=dp(96))
        self._cards.append(card_info)
        lbl_guide = Label(
            text="[b]Cara Pasang Widget di Layar Utama:[/b]\n"
                 "• Tahan area kosong layar utama > pilih [b]Widget[/b] > [b]Jadwal Shift App[/b].\n"
                 "• Pilih [b]Jadwal Shift (Tim)[/b] atau [b]Jadwal Personal + Alarm[/b].",
            markup=True, font_size=dp(12), color=TEXT_MUTED, halign="left", valign="middle"
        )
        lbl_guide.bind(size=lambda *_: setattr(lbl_guide, "text_size", lbl_guide.size))
        card_info.add_widget(lbl_guide)
        root.add_widget(card_info)

        scroll.add_widget(root)
        self.add_widget(scroll)

    def change_theme(self, _, theme_name):
        global BG_DARK, CARD_BG, CARD_BORDER, ACCENT_BLUE
        if theme_name in THEMES:
            self.current_theme_name = theme_name
            t = THEMES[theme_name]
            BG_DARK = t["BG_DARK"]
            CARD_BG = t["CARD_BG"]
            CARD_BORDER = t["CARD_BORDER"]
            ACCENT_BLUE = t["ACCENT_BLUE"]
            Window.clearcolor = BG_DARK

            for card in self._cards:
                card.set_bg(CARD_BG)
            for btn in self._buttons:
                if btn != self.btn_test_alarm:
                    btn.set_bg(ACCENT_BLUE)

            self._set_status(f"Tema diubah ke {theme_name}")

    def download_template(self, *_):
        import shutil
        name = "template_jadwal_shift.xlsx"
        src = os.path.join(os.path.dirname(os.path.abspath(__file__)), name)
        if not os.path.exists(src):
            self._set_status("File template belum tersedia di aplikasi.")
            return
        try:
            if platform == "android":
                from jnius import autoclass
                PythonActivity = autoclass("org.kivy.android.PythonActivity")
                FileHelper = autoclass(PKG + ".FileHelper")
                mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                where = FileHelper.saveToDownloads(PythonActivity.mActivity, src, name, mime)
            else:
                dl = os.path.join(os.path.expanduser("~"), "Downloads")
                os.makedirs(dl, exist_ok=True)
                where = os.path.join(dl, name)
                shutil.copy(src, where)
            self._set_status("✓ Template tersimpan di %s" % where)
        except Exception as e:
            self._set_status("Gagal menyimpan template: %s" % e)

    def _row(self, texts, bg, fg, bold=False):
        row = BoxLayout(spacing=dp(3))
        for t, w in zip(texts, COL_WEIGHTS):
            row.add_widget(Cell(t, bg, fg, bold=bold, size_hint_x=w))
        return row

    def open_picker(self, *_):
        if platform == "android":
            self._open_android_picker()
        else:
            content = FileChooserListView(filters=["*.xlsx", "*.csv"])
            content.bind(on_submit=lambda inst, sel, touch: self._desktop_selected(sel))
            self.popup = Popup(title="Pilih File Jadwal", content=content, size_hint=(0.9, 0.9))
            self.popup.open()

    def _desktop_selected(self, selection):
        if selection:
            self.popup.dismiss()
            self.load_file(selection[0])

    def _open_android_picker(self):
        from android import activity
        from jnius import autoclass

        Intent = autoclass("android.content.Intent")
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        if not getattr(self, "_activity_bound", False):
            activity.bind(on_activity_result=self._on_activity_result)
            self._activity_bound = True

        intent = Intent(Intent.ACTION_OPEN_DOCUMENT)
        intent.addCategory(Intent.CATEGORY_OPENABLE)
        intent.setType("*/*")
        PythonActivity.mActivity.startActivityForResult(intent, PICK_REQUEST)

    def _on_activity_result(self, request_code, result_code, intent):
        if request_code != PICK_REQUEST:
            return
        if result_code != -1 or intent is None or intent.getData() is None:
            Clock.schedule_once(lambda dt: self._set_status("Pemilihan file dibatalkan / tidak ada file dipilih."))
            return
        try:
            from jnius import autoclass
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            FileHelper = autoclass(PKG + ".FileHelper")
            path = FileHelper.copyToCache(PythonActivity.mActivity, intent.getData())
        except Exception as exc:
            msg = "Gagal membuka file: %s" % exc
            Clock.schedule_once(lambda dt: self._set_status(msg))
            return
        Clock.schedule_once(lambda dt: self.load_file(path))

    def load_file(self, path):
        try:
            # Memanggil logika dengan parameter fleksibel (Poin 2 & 3)
            month_key, new_days = sl.load_days(path, self.off_words, self.cuti_words)
        except sl.ScheduleError as exc:
            self._set_status(str(exc))
            return
        except Exception as exc:
            self._set_status("Gagal membaca file (%s): %s" % (type(exc).__name__, exc))
            return
        self.days = sl.merge_days(self.days, month_key, new_days, date.today())
        self._rebuild()
        self._save_local()
        self._push_to_widget()
        people = len({d[1] for d in new_days})
        self._set_status("✓ %s dimuat (%d orang • %s)" % (os.path.basename(path), people, month_key))
        self.refresh()

    def _rebuild(self):
        # Menerapkan aturan durasi fleksibel (Poin 2)
        self.entries = sl.build_entries(self.days, self.dur_full, self.dur_short)
        names = []
        seen = set()
        for e in self.entries:
            if e["name"] not in seen:
                seen.add(e["name"])
                names.append(e["name"])
        if names:
            self.spinner_name.values = names
            if self.spinner_name.text not in seen:
                self.spinner_name.text = names[0]
        else:
            self.spinner_name.values = []
            self.spinner_name.text = "Belum ada data"

    def refresh(self, *_):
        now = datetime.now()
        self.lbl_today.text = now.strftime("%d-%b")
        self.lbl_clock.text = now.strftime("%H:%M")

        duty, nxt = sl.compute(self.entries, now)
        self._fill(self.duty_cells, "Duty:", duty)
        self._fill(self.next_cells, "Next:", nxt)

        selected = self.spinner_name.text
        self._next_personal_start = None
        self._next_personal_name = selected
        active_str = "Sedang Libur"
        next_str = "Tidak ada jadwal"
        next_dt = None

        for e in self.entries:
            if e["name"] != selected:
                continue
            start_dt = datetime.fromisoformat(e["date"]) + timedelta(hours=e["hour"])
            end_dt = start_dt + timedelta(hours=e["dur"])
            if start_dt <= now < end_dt:
                active_str = "%02d+%d (s/d %s)" % (e["hour"], e["dur"], end_dt.strftime("%H:%M"))
            elif start_dt > now:
                if next_dt is None or start_dt < next_dt:
                    next_dt = start_dt

        self.lbl_p_duty.text = "Duty:  " + active_str
        if next_dt is not None:
            self._next_personal_start = next_dt
            alarm_dt = next_dt - timedelta(hours=1)
            day_lbl = "Hari ini" if next_dt.date() == now.date() else sl.HARI[next_dt.weekday()] + ", " + next_dt.strftime("%d %b")
            next_str = "%s %s" % (day_lbl, next_dt.strftime("%H:%M"))
            self.btn_test_alarm.text = "⏰  Set Alarm %s %s (1 Jam Sebelum Shift)" % (sl.HARI[alarm_dt.weekday()], alarm_dt.strftime("%H:%M"))
        else:
            self.btn_test_alarm.text = "⏰  Tidak Ada Jadwal Berikutnya"

        self.lbl_p_next.text = "Next:  " + next_str

    def trigger_personal_alarm(self, *_):
        if self._next_personal_start is None:
            self._set_status("Tidak ada jadwal berikutnya untuk disetel alarm.")
            return
        alarm_dt = self._next_personal_start - timedelta(hours=1)
        if platform != "android":
            msg = "Simulasi PC: Alarm disetel pukul %s untuk %s" % (alarm_dt.strftime("%H:%M"), self._next_personal_name)
            self._set_status("✓ " + msg); self._show_popup("Alarm Berhasil Disetel", f"⏰ Alarm untuk {self._next_personal_name}\nPukul {alarm_dt.strftime('%H:%M')} (1 jam sebelum shift {self._next_personal_start.strftime('%H:%M')})")
            return
        try:
            from jnius import autoclass
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            Provider = autoclass(PKG + ".PersonalWidgetProvider")

            # Logika alarm (hari + jam) ada di Java supaya sama persis dengan widget:
            # alarm <24 jam -> sekali bunyi; lebih jauh -> dipasang di HARI alarm (bukan hari ini).
            alarm_ms = int(alarm_dt.timestamp() * 1000)
            intent = Provider.buildAlarmIntent(
                alarm_ms,
                "Shift %s (%s)" % (self._next_personal_name, self._next_personal_start.strftime("%H:%M"))
            )
            if intent is None:
                self._set_status("Waktu alarm (1 jam sebelum shift) sudah lewat.")
                return
            PythonActivity.mActivity.startActivity(intent)
            when = "%s %s" % (sl.HARI[alarm_dt.weekday()], alarm_dt.strftime("%H:%M"))
            self._set_status("✓ Alarm disetel %s (1 jam sebelum shift)" % when)
            self._show_popup("Alarm Berhasil Disetel", f"⏰ Alarm untuk {self._next_personal_name}\n{when} (1 jam sebelum shift {self._next_personal_start.strftime('%H:%M')})")
        except Exception as exc:
            self._set_status("Gagal menyetel alarm: %s" % exc)

    @staticmethod
    def _fill(row, label, items):
        cells = list(reversed(row.children))
        cells[0].text = label
        slots = items[:2]
        if len(items) > 2:
            slots = [items[0], (items[1][0] + " +%d" % (len(items) - 2), items[1][1])]
        for i in range(2):
            name, tm = slots[i] if i < len(slots) else (("-" if i == 0 else ""), "")
            cells[1 + 2 * i].text = name
            cells[2 + 2 * i].text = tm

    def _set_status(self, text):
        self.lbl_status.text = text

    def _show_popup(self, title, message):
        box = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))
        lbl = Label(text=message, font_size=dp(14), halign="center", valign="middle")
        lbl.bind(size=lambda *_: setattr(lbl, "text_size", lbl.size))
        btn = ModernButton(text="OK", bg=ACCENT_BLUE, size_hint_y=None, height=dp(40))
        box.add_widget(lbl)
        box.add_widget(btn)
        popup = Popup(title=title, content=box, size_hint=(0.82, 0.35))
        btn.bind(on_press=popup.dismiss)
        popup.open()

    def _store_path(self):
        return os.path.join(App.get_running_app().user_data_dir, "days.txt")

    def _save_local(self):
        try:
            with open(self._store_path(), "w", encoding="utf-8") as f:
                f.write(sl.days_to_text(self.days))
        except OSError:
            pass

    def load_saved(self):
        try:
            with open(self._store_path(), "r", encoding="utf-8") as f:
                self.days = sl.text_to_days(f.read())
        except OSError:
            self.days = []
        self._rebuild()
        try: self.change_theme(None, self.current_theme_name)
        except Exception: pass
        if self.days:
            self._set_status("✓ Jadwal tersimpan dimuat (%d orang)" % len({d[1] for d in self.days}))
        self.refresh()

    def _push_to_widget(self):
        if platform != "android":
            return
        try:
            from jnius import autoclass
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            Provider = autoclass(PKG + ".ShiftWidgetProvider")
            ctx = PythonActivity.mActivity
            WidgetTheme = autoclass(PKG + ".WidgetTheme")
            WidgetTheme.saveTheme(ctx, self.current_theme_name)
            Provider.saveSchedule(ctx, sl.entries_to_text(self.entries, self.days))
            Provider.updateAll(ctx)
        except Exception as exc:
            self._set_status("Widget gagal diperbarui: %s" % exc)


class MainApp(App):
    def build(self):
        self.root_widget = ShiftApp()
        return self.root_widget

    def on_start(self):
        self.root_widget.load_saved()
        if self.root_widget.entries:
            self.root_widget._push_to_widget()
        Clock.schedule_interval(self.root_widget.refresh, 10)

    def on_pause(self):
        return True

    def on_resume(self):
        self.root_widget.refresh()


if __name__ == "__main__":
    MainApp().run()