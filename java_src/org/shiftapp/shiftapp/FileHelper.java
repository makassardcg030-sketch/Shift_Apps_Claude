package org.shiftapp.shiftapp;

import android.content.ContentResolver;
import android.content.ContentValues;
import android.content.Context;
import android.database.Cursor;
import android.net.Uri;
import android.os.Build;
import android.os.Environment;
import android.provider.MediaStore;
import android.provider.OpenableColumns;
import java.io.FileInputStream;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;

/** Menyalin file pilihan pengguna (content://) ke cache aplikasi agar bisa dibaca Python. */
public class FileHelper {

    public static String copyToCache(Context context, Uri uri) throws IOException {
        String name = "jadwal";
        Cursor cursor = context.getContentResolver().query(uri, null, null, null, null);
        try {
            if (cursor != null && cursor.moveToFirst()) {
                int idx = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME);
                if (idx >= 0) {
                    String n = cursor.getString(idx);
                    if (n != null && n.length() > 0) {
                        name = n;
                    }
                }
            }
        } finally {
            if (cursor != null) {
                cursor.close();
            }
        }
        name = name.replaceAll("[^A-Za-z0-9._-]", "_");

        File out = new File(context.getCacheDir(), name);
        InputStream in = context.getContentResolver().openInputStream(uri);
        if (in == null) {
            throw new IOException("Tidak bisa membuka file");
        }
        try {
            OutputStream os = new FileOutputStream(out);
            try {
                byte[] buf = new byte[8192];
                int n;
                while ((n = in.read(buf)) > 0) {
                    os.write(buf, 0, n);
                }
            } finally {
                os.close();
            }
        } finally {
            in.close();
        }
        return out.getAbsolutePath();
    }

    /** Menyalin file dari folder aplikasi ke folder Download publik. Mengembalikan lokasi/nama tersimpan. */
    public static String saveToDownloads(Context context, String srcPath, String displayName,
                                         String mime) throws IOException {
        InputStream in = new FileInputStream(new File(srcPath));
        try {
            if (Build.VERSION.SDK_INT >= 29) {
                ContentResolver resolver = context.getContentResolver();
                ContentValues values = new ContentValues();
                values.put(MediaStore.MediaColumns.DISPLAY_NAME, displayName);
                values.put(MediaStore.MediaColumns.MIME_TYPE, mime);
                values.put(MediaStore.MediaColumns.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS);
                Uri uri = resolver.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values);
                if (uri == null) {
                    throw new IOException("Gagal membuat file di Download");
                }
                OutputStream os = resolver.openOutputStream(uri);
                if (os == null) {
                    throw new IOException("Gagal menulis ke Download");
                }
                try {
                    copy(in, os);
                } finally {
                    os.close();
                }
                return "Download/" + displayName;
            } else {
                File dir = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS);
                if (!dir.exists()) {
                    dir.mkdirs();
                }
                File out = new File(dir, displayName);
                OutputStream os = new FileOutputStream(out);
                try {
                    copy(in, os);
                } finally {
                    os.close();
                }
                return out.getAbsolutePath();
            }
        } finally {
            in.close();
        }
    }

    private static void copy(InputStream in, OutputStream os) throws IOException {
        byte[] buf = new byte[8192];
        int n;
        while ((n = in.read(buf)) > 0) {
            os.write(buf, 0, n);
        }
    }
}
