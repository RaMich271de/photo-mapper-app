#!/bin/bash
# Dieses Skript führt den Build in einer kontrollierten Umgebung aus.

# 1. Aktiviere die virtuelle Umgebung
source venv/bin/activate

# 2. Setze die entscheidenden Umgebungsvariablen, um Host Contamination zu verhindern
export CFLAGS="--sysroot=/home/ramich/.buildozer/android/platform/android-ndk-r25b/toolchains/llvm/prebuilt/linux-x86_64/sysroot"
export LDFLAGS="--sysroot=/home/ramich/.buildozer/android/platform/android-ndk-r25b/toolchains/llvm/prebuilt/linux-x86_64/sysroot"
export PKG_CONFIG_PATH=/home/ramich/.buildozer/android/platform/android-ndk-r25b/toolchains/llvm/prebuilt/linux-x86_64/sysroot/usr/lib/pkgconfig
export USE_PKG_CONFIG=1 # Explizit sagen, dass er den PKG_CONFIG_PATH benutzen soll

# 3. Räume alte Builds auf
buildozer android clean

# 4. Führe den eigentlichen Build aus
buildozer -v android debug 2>&1 | tee build_log.txt

# 5. Hebe die Umgebungsvariablen für die Terminalsitzung wieder auf
unset CFLAGS
unset LDFLAGS
unset PKG_CONFIG_PATH
unset USE_PKG_CONFIG
