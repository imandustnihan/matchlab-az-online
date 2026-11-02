#!/usr/bin/env python3
"""Export the existing native app + production HTML as an Android Studio project."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import hashlib,shutil,sys

ROOT=Path(__file__).resolve().parents[1]
DIST=ROOT/"dist"
PROJECT=DIST/"MATCHLAB_AZ_Android_Studio"
ARCHIVE=DIST/"MATCHLAB_AZ_Android_Studio_v0945.zip"
NATIVE=ROOT/"native"/"android"
PUBLIC=[
    "index.html","styles.css","app.js","catalog.js",
    "featured_media.js","coach_tactics.js","install.js",
    "service-worker.js","manifest.webmanifest","assets/icon.svg",
    "assets/pwa-192.png","assets/pwa-512.png",
    "assets/pwa-512-maskable.png"
]
EXTRAS=["shell.css","shell.js"]

README="""MATCHLAB AZ v0.9.45 — Android Studio layihəsi

1. ZIP-i tam çıxart, MATCHLAB_AZ_Android_Studio qovluğunu seç.
2. Android Studio > File > Open vasitəsilə həmin qovluğu aç.
3. Gradle Sync: Gradle 8.9, Android Gradle Plugin 8.7.3, JDK 17, Android SDK 35.
4. Build > Build Bundle(s) / APK(s) > Build APK(s).
5. Hazır debug APK: app/build/outputs/apk/debug/app-debug.apk.

Telefonu USB debugging ilə qoşub Run düyməsi ilə də yoxlaya bilərsən.
Yayımlanan, stabil imzalı APK üçün Build > Generate Signed Bundle / APK
bölməsində öz release keystore faylını yarat; onu və parolunu gizli saxla.
Debug APK imzaları fərqli ola bilər. Köhnə tətbiqi və onun yerli
məlumatlarını qorunmadan silmə.

Bu layihədə bütün HTML/JS/CSS faylları app/src/main/assets/web
qovluğundadır, GitHub-a və Python serverinə ehtiyac yoxdur.
Canlı oyunlar və dünya futbol arxivi internet/backend bağlantısı tələb edir.
Paketin içindəki HTML proqram Android WebView pəncərəsində göstərilir.
"""

def copy_file(src,dst):
    if not src.is_file():
        raise FileNotFoundError(str(src))
    dst.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(src,dst)

def export():
    DIST.mkdir(exist_ok=True)
    if PROJECT.exists():
        shutil.rmtree(PROJECT)
    PROJECT.mkdir(parents=True)
    for name in ("build.gradle","settings.gradle","gradle.properties"):
        copy_file(NATIVE/name,PROJECT/name)
    script=(NATIVE/"app"/"build.gradle").read_text(encoding="utf-8")
    begin=script.index(" sourceSets {")
    end=script.index("\n}",begin)
    script=script[:begin]+script[end:]
    script=script[:script.index("// Bundle production HTML")].rstrip()+"\n"
    script=script.replace("versionCode 944","versionCode 945").replace(
        "versionName '0.9.44-android-app'","versionName '0.9.45-android-studio'")
    assert "versionCode 945" in script
    assert "generated/matchlab-assets" not in script
    assert "from('../../../')" not in script
    dest=PROJECT/"app"/"build.gradle"
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(script,encoding="utf-8")
    shutil.copytree(NATIVE/"app"/"src"/"main",PROJECT/"app"/"src"/"main")
    activity=PROJECT/"app"/"src"/"main"/"java"/"az"/"matchlab"/"mobile"/"MainActivity.java"
    activity.write_text(activity.read_text(encoding="utf-8").replace("0.9.44","0.9.45"),encoding="utf-8")
    assets=PROJECT/"app"/"src"/"main"/"assets"/"web"
    for name in PUBLIC:copy_file(ROOT/name,assets/name)
    for name in EXTRAS:copy_file(ROOT/"native"/"packed"/name,assets/name)
    (PROJECT/"README.txt").write_text(README,encoding="utf-8")
    (PROJECT/".gitignore").write_text(
        ".gradle/\n.idea/\nlocal.properties\n**/build/\n*.jks\n*.keystore\ncaptures/\n",encoding="utf-8")
    for name in ("app/src/main/AndroidManifest.xml",
        "app/src/main/java/az/matchlab/mobile/MainActivity.java",
        "app/src/main/assets/web/index.html",
        "app/src/main/assets/web/app.js",
        "app/src/main/res/mipmap-anydpi-v26/ic_launcher.xml",
        "app/build.gradle","settings.gradle"):
        assert (PROJECT/name).is_file(),name
    original=hashlib.sha256((ROOT/"app.js").read_bytes()).digest()
    exported=hashlib.sha256((assets/"app.js").read_bytes()).digest()
    assert original==exported
    print("PASS exported production HTML without modifications")
    print("Export folder:",PROJECT)

def pack():
    for name in ("gradlew","gradlew.bat","gradle/wrapper/gradle-wrapper.jar",
                 "gradle/wrapper/gradle-wrapper.properties"):
        assert (PROJECT/name).is_file(),name
    if ARCHIVE.exists():ARCHIVE.unlink()
    with ZipFile(ARCHIVE,"w",ZIP_DEFLATED,compresslevel=8) as z:
        for f in sorted(PROJECT.rglob("*")):
            if not f.is_file():continue
            relative=f.relative_to(PROJECT).as_posix()
            if relative.startswith((".gradle/",".idea/","app/build/")):continue
            if relative=="local.properties":continue
            z.write(f,arcname=PROJECT.name+"/"+relative)
    with ZipFile(ARCHIVE) as z:
        assert z.testzip() is None
        names=set(z.namelist())
        assert PROJECT.name+"/gradlew.bat" in names
        assert PROJECT.name+"/app/src/main/assets/web/app.js" in names
        print("PASS exported ZIP:",ARCHIVE,len(names),"files",ARCHIVE.stat().st_size,"bytes")

if __name__=="__main__":
    if len(sys.argv)!=2 or sys.argv[1] not in ("export","pack"):
        raise SystemExit("Usage: python tools/export_android_studio.py export|pack")
    {"export":export,"pack":pack}[sys.argv[1]]()
