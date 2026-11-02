#!/usr/bin/env python3
"""Export a WebView-free Android Studio Java project from native Android sources."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
DIST=ROOT/"dist"
PROJECT=DIST/"MATCHLAB_AZ_Android_Studio_Native"
ARCHIVE=DIST/"MATCHLAB_AZ_Android_Studio_Native_v0946.zip"
SOURCE=ROOT/"native"/"android"

README="""MATCHLAB AZ v0.9.46 — TAM YERLI ANDROID TETBIQI (WebView YOXDUR)

1. ZIP faylini tam cixart, MATCHLAB_AZ_Android_Studio_Native qovlugunu sec.
2. Android Studio > File > Open bolmesinde hemin qovlugu ac.
3. Android SDK Platform 35, JDK 17 ve Gradle 8.9 gerekir.
4. Build > Build Bundle(s) / APK(s) > Build APK(s).
5. APK: app/build/outputs/apk/debug/app-debug.apk

Android interfeysi Java Activity / LinearLayout / ScrollView / Canvas ile
qurulub. WebView ve HTML kodu APK-ye daxil edilmir.
Canli hesablar, futbol arxivi ve profiller HTTPS JSON API-ye baglidir.
Taktika meydancasi Canvas ile yerli cekilir.
Android Ayarlar > Tetbiqler bolmesinde normal proqram kimi gorunur.

Bu, DEBUG imzali sinaq APK-sidir. Keystore-deki ferq sebebile kohne APK
uzerine qurasdirilmasi alinmaya biler. Kohneden evvel saxlanmis
secimleri ve taktikani qoruyun. Daimi release keystore parolunu ve faylini
GitHub-a ve ya sohbetlere yuklemeyin.
"""

def export():
    DIST.mkdir(exist_ok=True)
    if PROJECT.exists():shutil.rmtree(PROJECT)
    PROJECT.mkdir()
    for name in ["build.gradle","settings.gradle","gradle.properties"]:
        shutil.copy2(SOURCE/name,PROJECT/name)
    shutil.copytree(SOURCE/"app"/"src"/"main",PROJECT/"app"/"src"/"main")
    shutil.copy2(SOURCE/"app"/"build.gradle",PROJECT/"app"/"build.gradle")
    java=PROJECT/"app"/"src"/"main"/"java"/"az"/"matchlab"/"mobile"/"MainActivity.java"
    txt=java.read_text(encoding="utf-8")
    for forbidden in ("WebView","android.webkit","loadUrl","matchlab.local"):
        if forbidden in txt:raise ValueError("WebView reference not removed: "+forbidden)
    app_gradle=(PROJECT/"app"/"build.gradle").read_text(encoding="utf-8")
    for forbidden in ("bundleHtmlAssets","assets.srcDirs","from('../../../')"):
        if forbidden in app_gradle:raise ValueError("HTML bundling still active: "+forbidden)
    assert "versionCode 946" in app_gradle
    assets=PROJECT/"app"/"src"/"main"/"assets"
    if assets.is_dir() and any(assets.rglob("*")):
        raise ValueError("Unexpected browser asset in native Android project")
    (PROJECT/"README.txt").write_text(README,encoding="utf-8")
    (PROJECT/".gitignore").write_text(".gradle/\n.idea/\nlocal.properties\n**/build/\n*.jks\n*.keystore\n",encoding="utf-8")
    assert (PROJECT/"app"/"src"/"main"/"java"/"az"/"matchlab"/"mobile"/"PitchView.java").exists()
    assert (PROJECT/"app"/"src"/"main"/"res"/"mipmap-anydpi-v26"/"ic_launcher.xml").exists()
    print("PASS exported actual native Android project, no WebView and no HTML assets")

def pack():
    for f in ["gradlew","gradlew.bat","gradle/wrapper/gradle-wrapper.jar","gradle/wrapper/gradle-wrapper.properties"]:
        if not (PROJECT/f).is_file():raise FileNotFoundError(f)
    if ARCHIVE.exists():ARCHIVE.unlink()
    with ZipFile(ARCHIVE,"w",ZIP_DEFLATED,compresslevel=8) as z:
        for f in sorted(PROJECT.rglob("*")):
            if not f.is_file():continue
            name=f.relative_to(PROJECT).as_posix()
            if name.startswith((".gradle/",".idea/","app/build/")) or name=="local.properties":continue
            z.write(f,arcname=PROJECT.name+"/"+name)
    with ZipFile(ARCHIVE) as z:
        if z.testzip() is not None:raise RuntimeError("ZIP invalid")
        assert PROJECT.name+"/gradlew.bat" in z.namelist()
        assert PROJECT.name+"/app/src/main/java/az/matchlab/mobile/MainActivity.java" in z.namelist()
        assert all("assets/web/" not in p for p in z.namelist())
    print("PASS native Android Studio ZIP",ARCHIVE,ARCHIVE.stat().st_size)

if __name__=="__main__":
    if len(sys.argv)!=2 or sys.argv[1] not in ("export","pack"):
        raise SystemExit("Usage: python tools/export_android_studio.py export|pack")
    {"export":export,"pack":pack}[sys.argv[1]]()
