package org.shiftapp.shiftapp;

import android.app.AlarmManager;
import android.app.PendingIntent;
import android.appwidget.AppWidgetManager;
import android.appwidget.AppWidgetProvider;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.widget.RemoteViews;

import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.Date;
import java.util.List;
import java.util.Locale;

/**
 * Widget homescreen "Jadwal Shift" (4x2, bisa diperkecil ke 2x2 -> shift_widget_small.xml):
 *
 *   JADWAL SHIFT: Kamis, 19 Nov                 Jam 11:23   (TextClock, jalan sendiri)
 *   DUTY                       | NEXT
 *   1. Nama a        06+8      | 1. Nama d   14:00
 *   2. Nama b        08+8      |
 *   3. Nama c        11+8      |
 *
 * Kolom NEXT hanya menampilkan jam (tanpa hari/tanggal).
 * Data disimpan aplikasi Python (saveSchedule), satu baris per shift:
 *     yyyy-MM-dd|Nama|jamMulai|durasiJam        mis. 2026-11-15|Dirlan|14|8
 * (baris 3 kolom "yyyy-MM-dd|Nama|OFF" untuk hari libur/cuti diabaikan di sini.)
 * Widget menjadwalkan pembaruan sendiri tepat saat shift berganti.
 */
public class ShiftWidgetProvider extends AppWidgetProvider {

    private static final String PREFS = "shift_widget";
    private static final String KEY_SCHEDULE = "schedule";
    private static final String ACTION_REFRESH = "org.shiftapp.shiftapp.REFRESH";
    private static final long HOUR_MS = 60L * 60L * 1000L;
    private static final int ROWS = 3;   // jumlah baris per kolom (Duty / Next)

    private static class Entry {
        String name;
        int hour;
        int dur;
        long start;
        long end;
    }

    // ------------------------------------------------------------ lifecycle
    @Override
    public void onUpdate(Context context, AppWidgetManager manager, int[] appWidgetIds) {
        for (int id : appWidgetIds) {
            updateWidget(context, manager, id);
        }
        scheduleNext(context);
    }

    @Override
    public void onAppWidgetOptionsChanged(Context context, AppWidgetManager manager, int widgetId, Bundle newOptions) {
        updateWidget(context, manager, widgetId);   // ukuran berubah -> pilih layout 2x2 / 4x2
    }

    @Override
    public void onReceive(Context context, Intent intent) {
        super.onReceive(context, intent);
        if (intent != null && ACTION_REFRESH.equals(intent.getAction())) {
            updateAll(context);
        }
    }

    @Override
    public void onDisabled(Context context) {
        AlarmManager am = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
        if (am != null) {
            am.cancel(refreshIntent(context));
        }
    }

    // Ganti bagian method saveSchedule di ShiftWidgetProvider.java dengan ini:
    public static void saveSchedule(Context context, String data) {
        SharedPreferences sp = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        sp.edit().putString(KEY_SCHEDULE, data == null ? "" : data).apply();
        PersonalWidgetProvider.updateAll(context);
    }

    public static void updateAll(Context context) {
        AppWidgetManager manager = AppWidgetManager.getInstance(context);
        ComponentName cn = new ComponentName(context, ShiftWidgetProvider.class);
        int[] ids = manager.getAppWidgetIds(cn);
        for (int id : ids) {
            updateWidget(context, manager, id);
        }
        scheduleNext(context);
    }

    // -------------------------------------------------------------- tampilan
    private static void updateWidget(Context context, AppWidgetManager manager, int widgetId) {
        String pkg = context.getPackageName();
        // Lebar < ~200dp (2x2) -> layout ringkas; selain itu layout 4x2 penuh.
        int minWidthDp = 250;
        try {
            Bundle opts = manager.getAppWidgetOptions(widgetId);
            if (opts != null) {
                minWidthDp = opts.getInt(AppWidgetManager.OPTION_APPWIDGET_MIN_WIDTH, 250);
            }
        } catch (Exception ignored) {
        }
        String layoutName = minWidthDp > 0 && minWidthDp < 200 ? "shift_widget_small" : "shift_widget";
        int layoutId = context.getResources().getIdentifier(layoutName, "layout", pkg);
        if (layoutId == 0) {
            return;
        }
        RemoteViews views = new RemoteViews(pkg, layoutId);
        // TEMA WIDGET IKUT APLIKASI: baca tema yang disimpan Python, terapkan ke semua baris.
        WidgetTheme.Palette th = WidgetTheme.load(context);
        WidgetTheme.bg(views, context, "widget_root", th.bg);
        WidgetTheme.bg(views, context, "w_header", th.card);
        WidgetTheme.fg(views, context, "w_title", th.text);
        WidgetTheme.fg(views, context, "w_date", th.nextBg);
        WidgetTheme.fg(views, context, "w_time_label", th.muted);
        WidgetTheme.fg(views, context, "w_time", th.text);
        for (String id : new String[]{"w_h_duty", "w_h_next"}) {
            WidgetTheme.bg(views, context, id, th.card);
            WidgetTheme.fg(views, context, id, th.text);
        }
        WidgetTheme.bg(views, context, "duty_col", th.accent);
        WidgetTheme.bg(views, context, "next_col", th.nextBg);
        for (int i = 1; i <= ROWS; i++) {
            WidgetTheme.fg(views, context, "duty_name" + i, th.onAccent);
            WidgetTheme.fg(views, context, "duty_time" + i, th.onAccent);
            WidgetTheme.fg(views, context, "next_name" + i, th.nextText);
            WidgetTheme.fg(views, context, "next_time" + i, th.nextText);
        }

        List<Entry> all = parse(prefs(context).getString(KEY_SCHEDULE, ""));
        List<String[]> duty = new ArrayList<String[]>();
        List<String[]> next = new ArrayList<String[]>();
        compute(all, System.currentTimeMillis(), duty, next);
        fillRows(context, views, "duty", duty);
        fillRows(context, views, "next", next);

        Intent launch = context.getPackageManager().getLaunchIntentForPackage(pkg);
        if (launch != null) {
            PendingIntent pi = PendingIntent.getActivity(
                    context, 0, launch,
                    PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
            views.setOnClickPendingIntent(idOf(context, "widget_root"), pi);
        }
        manager.updateAppWidget(widgetId, views);
    }

    private static void setText(Context context, RemoteViews views, String idName, String text) {
        views.setTextViewText(idOf(context, idName), text);
    }

    private static int idOf(Context context, String name) {
        return context.getResources().getIdentifier(name, "id", context.getPackageName());
    }

    private static SharedPreferences prefs(Context context) {
        return context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    // ------------------------------------------------ alarm pergantian shift
    private static PendingIntent refreshIntent(Context context) {
        Intent in = new Intent(context, ShiftWidgetProvider.class);
        in.setAction(ACTION_REFRESH);
        return PendingIntent.getBroadcast(
                context, 1, in, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
    }

    /** Alarm tidak-presisi (tanpa izin khusus): bisa meleset beberapa menit. */
    private static void scheduleNext(Context context) {
        AlarmManager am = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
        if (am == null) {
            return;
        }
        long now = System.currentTimeMillis();
        long next = Long.MAX_VALUE;
        for (Entry e : parse(prefs(context).getString(KEY_SCHEDULE, ""))) {
            if (e.start > now && e.start < next) {
                next = e.start;
            }
            if (e.end > now && e.end < next) {
                next = e.end;
            }
        }
        PendingIntent pi = refreshIntent(context);
        am.cancel(pi);
        if (next != Long.MAX_VALUE) {
            am.set(AlarmManager.RTC_WAKEUP, next + 1000L, pi);
        }
    }

    // ---------------------------------------------------------------- logika
    /**
     * Mengisi daftar duty (nama, "06+8") dan next (nama, "14:00").
     * Duty diurutkan berdasarkan jam mulai. Next = kelompok shift terdekat berikutnya,
     * hanya jam yang ditampilkan.
     */
    static void compute(List<Entry> entries, long now, List<String[]> duty, List<String[]> next) {
        if (entries.isEmpty()) {
            duty.add(new String[]{"-", ""});
            next.add(new String[]{"Buka app", ""});
            return;
        }

        List<Entry> onDuty = new ArrayList<Entry>();
        long nextStart = Long.MAX_VALUE;
        for (Entry e : entries) {
            if (e.start <= now && now < e.end) {
                onDuty.add(e);
            }
            if (e.start > now && e.start < nextStart) {
                nextStart = e.start;
            }
        }
        Collections.sort(onDuty, new Comparator<Entry>() {
            @Override
            public int compare(Entry a, Entry b) {
                return a.start < b.start ? -1 : (a.start > b.start ? 1 : 0);
            }
        });
        for (Entry e : onDuty) {
            duty.add(new String[]{e.name, String.format(Locale.US, "%02d+%d", e.hour, e.dur)});
        }
        if (nextStart != Long.MAX_VALUE) {
            String hhmm = fmt("HH:mm", nextStart);
            for (Entry e : entries) {
                if (e.start == nextStart) {
                    next.add(new String[]{e.name, hhmm});
                }
            }
        }
        if (duty.isEmpty()) {
            duty.add(new String[]{"-", ""});
        }
        if (next.isEmpty()) {
            next.add(new String[]{"-", ""});
        }
    }

    /**
     * Isi ROWS baris: "1. Nama" + waktu. Kalau lebih dari ROWS orang,
     * baris terakhir diberi akhiran " +N" (N = sisa yang tidak muat).
     */
    private static void fillRows(Context context, RemoteViews views, String prefix, List<String[]> items) {
        for (int i = 0; i < ROWS; i++) {
            String name = "";
            String time = "";
            if (i < items.size()) {
                String[] it = items.get(i);
                name = it[0];
                time = it[1];
                if (items.size() == 1 && ("-".equals(name) || "Buka app".equals(name))) {
                    // placeholder: tanpa nomor
                } else {
                    name = (i + 1) + ". " + name;
                }
                if (i == ROWS - 1 && items.size() > ROWS) {
                    name = name + " +" + (items.size() - ROWS);
                }
            }
            setText(context, views, prefix + "_name" + (i + 1), name);
            setText(context, views, prefix + "_time" + (i + 1), time);
        }
    }

    private static boolean sameDay(long a, long b) {
        return fmt("yyyyMMdd", a).equals(fmt("yyyyMMdd", b));
    }

    private static String fmt(String pattern, long millis) {
        return new SimpleDateFormat(pattern, new Locale("id", "ID")).format(new Date(millis));
    }

    private static List<Entry> parse(String data) {
        List<Entry> out = new ArrayList<Entry>();
        if (data == null || data.length() == 0) {
            return out;
        }
        SimpleDateFormat f = new SimpleDateFormat("yyyy-MM-dd HH:mm", Locale.US);
        f.setLenient(false);
        for (String line : data.split("\n")) {
            String[] p = line.trim().split("\\|", -1);
            if (p.length < 4) {
                continue;
            }
            try {
                Entry e = new Entry();
                e.name = p[1].trim();
                e.hour = Integer.parseInt(p[2].trim());
                e.dur = Integer.parseInt(p[3].trim());
                e.start = f.parse(p[0].trim() + " " + String.format(Locale.US, "%02d:00", e.hour))
                        .getTime();
                e.end = e.start + e.dur * HOUR_MS;
                out.add(e);
            } catch (Exception ignored) {
                // baris rusak dilewati
            }
        }
        return out;
    }
}
