#!/usr/bin/env bash
# Android Studio olmadan, test amaçlı imzalı APK üretir.
# Gerekenler: Java 11+, Node.js (npm), Python 3 + "cryptography" paketi.
# Kullanım:  tools/quick-apk/build.sh      →  tools/quick-apk/out/Luna-Piano-Tiles-test.apk
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
OUT="$HERE/out"; WORK="$OUT/work"
rm -rf "$WORK" && mkdir -p "$WORK/proj" "$OUT/tools"

# 1) apktool 2.4.1'i npm'den indir (smali, aapt ve Android framework kaynaklarını içerir)
if [ ! -f "$OUT/tools/apktool.jar" ]; then
  (cd "$OUT/tools" && npm pack apktool-jar@2.4.1 --silent >/dev/null && tar xzf apktool-jar-2.4.1.tgz && mv package/bin/apktool_2.4.1.jar apktool.jar && rm -rf package apktool-jar-2.4.1.tgz)
fi

# 2) apktool projesini birleştir: manifest + smali (bu klasör), simgeler (android/), oyun (www/)
cp "$HERE/apktool.yml" "$HERE/AndroidManifest.xml" "$WORK/proj/"
cp -r "$HERE/smali" "$WORK/proj/smali"
cp -r "$ROOT/android/app/src/main/res" "$WORK/proj/res"
mkdir -p "$WORK/proj/assets" && cp -r "$ROOT/www/." "$WORK/proj/assets/"

# 3) derle, hizala ve v2 imzası at (anahtar ilk seferde tools/quick-apk/out/keys içine üretilir)
java -jar "$OUT/tools/apktool.jar" b -f "$WORK/proj" -o "$WORK/unsigned.apk" -p "$OUT/tools/framework"
python3 "$HERE/sign_v2.py" "$WORK/unsigned.apk" "$OUT/Luna-Piano-Tiles-test.apk" "$OUT/keys"
echo "Hazır: $OUT/Luna-Piano-Tiles-test.apk"
