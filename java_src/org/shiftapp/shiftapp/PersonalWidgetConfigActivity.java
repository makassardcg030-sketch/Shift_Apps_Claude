package org.shiftapp.shiftapp;

import android.app.Activity;
import android.app.AlertDialog;
import android.appwidget.AppWidgetManager;
import android.content.DialogInterface;
import android.content.Intent;
import android.os.Bundle;
import android.widget.Toast;

import java.util.List;

public class PersonalWidgetConfigActivity extends Activity {

    private int appWidgetId = AppWidgetManager.INVALID_APPWIDGET_ID;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setResult(RESULT_CANCELED);

        Intent intent = getIntent();
        Bundle extras = intent.getExtras();
        if (extras != null) {
            appWidgetId = extras.getInt(
                    AppWidgetManager.EXTRA_APPWIDGET_ID,
                    AppWidgetManager.INVALID_APPWIDGET_ID
            );
        }

        if (appWidgetId == AppWidgetManager.INVALID_APPWIDGET_ID) {
            finish();
            return;
        }

        final List<String> names = PersonalWidgetProvider.getAvailableNames(this);
        if (names.isEmpty()) {
            Toast.makeText(this, "Unggah file jadwal di aplikasi terlebih dahulu!", Toast.LENGTH_LONG).show();
            finish();
            return;
        }

        final String[] items = names.toArray(new String[0]);
        new AlertDialog.Builder(this)
                .setTitle("Pilih Nama untuk Widget")
                .setItems(items, new DialogInterface.OnClickListener() {
                    @Override
                    public void onClick(DialogInterface dialog, int which) {
                        String chosen = items[which];
                        PersonalWidgetProvider.saveSelectedName(
                                PersonalWidgetConfigActivity.this, appWidgetId, chosen);

                        AppWidgetManager manager = AppWidgetManager.getInstance(PersonalWidgetConfigActivity.this);
                        PersonalWidgetProvider.updateWidget(PersonalWidgetConfigActivity.this, manager, appWidgetId);

                        Intent resultValue = new Intent();
                        resultValue.putExtra(AppWidgetManager.EXTRA_APPWIDGET_ID, appWidgetId);
                        setResult(RESULT_OK, resultValue);
                        finish();
                    }
                })
                .setOnCancelListener(new DialogInterface.OnCancelListener() {
                    @Override
                    public void onCancel(DialogInterface dialog) {
                        finish();
                    }
                })
                .show();
    }
}
