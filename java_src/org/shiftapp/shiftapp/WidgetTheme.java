package org.shiftapp.shiftapp;

import android.content.Context;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.widget.RemoteViews;

/**
 * TEMA WIDGET IKUT TEMA APLIKASI.
 * Alur: main.py change_theme() -> WidgetTheme.saveTheme(ctx, namaTema)
 *       -> saveSchedule / updateAll -> provider baca get() -> apply() ke RemoteViews.
 * RemoteViews tidak bisa pakai drawable dinamis, jadi warna diterapkan lewat
 * setInt(..., "setBackgroundColor", warna) + setTextColor. Ini satu-satunya
 * cara yang aman untuk widget homescreen.
 *
 * Palet ini HARUS sama persis dengan THEMES di main.py. Kalau tambah tema di
 * Python, tambah juga di sini dengan nama yang sama persis.
 */
public class WidgetTheme {
    private static final String PREFS = "shift_widget";
    private static final String KEY_THEME = "widget_theme";

    public static class Palette {
        public int bg, card, border, accent, accent2, text, muted, onAccent, nextBg, nextText;
        Palette(String bg, String card, String border, String accent, String accent2,
                String text, String muted, String onAccent, String nextBg, String nextText) {
            this.bg = Color.parseColor(bg); this.card = Color.parseColor(card);
            this.border = Color.parseColor(border); this.accent = Color.parseColor(accent);
            this.accent2 = Color.parseColor(accent2); this.text = Color.parseColor(text);
            this.muted = Color.parseColor(muted); this.onAccent = Color.parseColor(onAccent);
            this.nextBg = Color.parseColor(nextBg); this.nextText = Color.parseColor(nextText);
        }
    }

    public static Palette forName(String name) {
        if ("Midnight Blue".equals(name))
            return new Palette("#0A0F1E","#162036","#293957","#3380F2","#05A8D6","#F7F8FA","#99A3BA","#FFFFFF","#FACC15","#0F172A");
        if ("Emerald Dark".equals(name))
            return new Palette("#0D1712","#1A2E24","#2E4D3D","#0F8C59","#0AA68C","#F2F8F2","#99ADA0","#FFFFFF","#FACC15","#0F172A");
        if ("Terang".equals(name))
            return new Palette("#F2F4F7","#FFFFFF","#D9DDE6","#2563EB","#0284C7","#0F172A","#666E82","#FFFFFF","#FACC15","#0F172A");
        // Slate Dark (default)
        return new Palette("#0F172A","#1E293B","#334155","#2563EB","#0284C7","#F7F8FA","#94A3B8","#FFFFFF","#FACC15","#0F172A");
    }

    public static void saveTheme(Context ctx, String name) {
        if (name == null || name.isEmpty()) name = "Slate Dark";
        ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit().putString(KEY_THEME, name).apply();
    }
    public static String loadName(Context ctx) {
        return ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE).getString(KEY_THEME, "Slate Dark");
    }
    public static Palette load(Context ctx) { return forName(loadName(ctx)); }

    static int idOf(Context ctx, String name) {
        return ctx.getResources().getIdentifier(name, "id", ctx.getPackageName());
    }
    static void bg(RemoteViews v, Context ctx, String viewId, int color) {
        int id = idOf(ctx, viewId); if (id != 0) v.setInt(id, "setBackgroundColor", color);
    }
    static void fg(RemoteViews v, Context ctx, String viewId, int color) {
        int id = idOf(ctx, viewId); if (id != 0) v.setTextColor(id, color);
    }
}
