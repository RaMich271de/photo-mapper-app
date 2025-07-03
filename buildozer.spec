[app]
# --- Grundlegende App-Informationen ---
title = Photo Mapper
package.name = photomapper
package.domain = org.ramich.photomapper

# --- Quellcode-Definition ---
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ico
app_filename = PhotoMapper_004.py

version = 1.0
orientation = portrait

# --- Abhängigkeiten (Requirements) ---
requirements = python3,kivy,pillow,folium

# --- Visuelle Elemente ---
icon.filename = %(source.dir)s/icon.ico
presplash.filename = %(source.dir)s/icon.ico

# --- Android-Berechtigungen und API-Level ---
android.permissions = READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, INTERNET
android.api = 31
android.minapi = 24
android.archs = arm64-v8a

# --- FINALE KORREKTUR: Android SDK/NDK Versionen festpinnen ---
# Wir zwingen Buildozer, bewährte Versionen der Android-Werkzeuge zu verwenden,
# für die die Lizenzakzeptanz im Build-Automaten funktioniert.
android.sdk = 29
android.ndk = 21b
android.build_tools = 29.0.3

[buildozer]
log_level = 2
warn_on_root = 1
