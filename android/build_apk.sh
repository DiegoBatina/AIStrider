#!/usr/bin/env bash
# Gera android/AIStrider.apk sem Gradle: aapt2 + javac + dx + apksigner.
# Precisa de: JDK, o pacote android-sdk do Ubuntu (build-tools), dalvik-exchange e um android.jar (ANDROID_JAR).
set -euo pipefail
cd "$(dirname "$0")"
BT=${BUILD_TOOLS:-/usr/lib/android-sdk/build-tools/debian}
JAR=${ANDROID_JAR:?defina ANDROID_JAR com o caminho do android.jar}
rm -rf build && mkdir -p build/classes build/dex
python3 build_www_android.py
"$BT/aapt2" compile --dir res -o build/res.zip
"$BT/aapt2" link -I "$JAR" --manifest AndroidManifest.xml -A assets -o build/base.apk build/res.zip --auto-add-overlay
javac --release 8 -nowarn -classpath "$JAR" -d build/classes $(find src -name '*.java')
dalvik-exchange --dex --output=build/dex/classes.dex build/classes
cp build/base.apk build/unsigned.apk
(cd build/dex && zip -q ../unsigned.apk classes.dex)
"$BT/zipalign" -f 4 build/unsigned.apk build/aligned.apk
KS=${KEYSTORE:-$HOME/.android/aistrider.keystore}
if [ ! -f "$KS" ]; then
  mkdir -p "$(dirname "$KS")"
  keytool -genkeypair -keystore "$KS" -storepass aistrider -keypass aistrider -alias aistrider \
    -keyalg RSA -keysize 2048 -validity 10000 -dname "CN=AI Strider" >/dev/null
fi
"$BT/apksigner" sign --ks "$KS" --ks-pass pass:aistrider --ks-key-alias aistrider --out AIStrider.apk build/aligned.apk
echo "PRONTO: android/AIStrider.apk"
