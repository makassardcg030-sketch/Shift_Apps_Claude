[app]

# (str) Judul aplikasi
title = Jadwal Shift App

# (str) Nama package -> package lengkap: org.shiftapp.shiftapp
package.name = shiftapp
package.domain = org.shiftapp

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,xlsx
source.exclude_dirs = tests, tools, bin, venv, java_src, widget_res, .github, .git

# Ikon aplikasi (simpan gambar logo sebagai icon.png di root folder)
icon.filename = %(source.dir)s/icon.png

version = 1.6

requirements = python3,kivy,pyjnius,openpyxl,et_xmlfile

orientation = portrait
fullscreen = 0

# ---- Android ----
android.api = 35
android.minapi = 24
android.archs = arm64-v8a, armeabi-v7a
android.permissions = com.android.alarm.permission.SET_ALARM
android.release_artifact = aab

android.accept_sdk_license = True

# ---- Widget homescreen ----
android.add_src = java_src
android.add_resources = widget_res/layout:layout, widget_res/xml:xml, widget_res/drawable:drawable

[buildozer]

log_level = 2
warn_on_root = 1
bin_dir = ./bin
