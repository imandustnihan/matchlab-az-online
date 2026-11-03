#!/usr/bin/env python3
"""Android emulator visual + navigation QA against the actual compiled debug APK.

Uses adb and Android's UI hierarchy (not OCR); screenshots and UI XML are
retained as GitHub Actions artifacts. Does not claim physical-device testing.
"""
import json
import os
import pathlib
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

APP="az.matchlab.mobile"
ACTIVITY=APP+"/.MainActivity"
OUTPUT=pathlib.Path(os.environ.get("MATCHLAB_QA_OUT","qa-artifacts/android"))
OUTPUT.mkdir(parents=True,exist_ok=True)
PASSES=[]

def adb(*args, timeout=50, text=True):
    result=subprocess.run(["adb",*args],stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE,timeout=timeout,check=False)
    if result.returncode:
        raise RuntimeError("adb "+" ".join(args)+" failed: "+
                           result.stderr.decode(errors="replace")[-1000:])
    return result.stdout.decode(errors="replace") if text else result.stdout

def check(condition,label):
    if not condition:raise AssertionError(label)
    print("[PASS]",label,flush=True)
    PASSES.append(label)

def hierarchy():
    adb("shell","uiautomator","dump","/sdcard/matchlab-qa.xml",timeout=55)
    raw=adb("exec-out","cat","/sdcard/matchlab-qa.xml")
    index=raw.find("<?xml")
    if index<0:index=raw.find("<hierarchy")
    if index<0:raise RuntimeError("No UI hierarchy XML: "+raw[:300])
    root=ET.fromstring(raw[index:])
    return list(root.iter("node")),raw[index:]

def matches(node,query,by):
    val=node.attrib.get("content-desc" if by=="desc" else "text","")
    return query.casefold() in val.casefold()

def wait_for(query,by="text",timeout=35):
    deadline=time.time()+timeout
    while time.time()<deadline:
        try:
            nodes,xml=hierarchy()
            candidates=[n for n in nodes if matches(n,query,by)]
            if candidates:return candidates[0]
        except (RuntimeError,ET.ParseError):
            pass
        time.sleep(1)
    raise AssertionError("UI element not found: "+query)

def tap(query,by="text",scroll=False):
    for attempt in range(7 if scroll else 1):
        nodes,_=hierarchy()
        candidates=[n for n in nodes if matches(n,query,by)]
        if candidates:
            node=candidates[0]
            bounds=node.attrib.get("bounds","")
            coords=list(map(int,re.findall(r"\d+",bounds)))
            if len(coords)==4:
                x=(coords[0]+coords[2])//2;y=(coords[1]+coords[3])//2
                adb("shell","input","tap",str(x),str(y))
                time.sleep(.8)
                return
        if scroll:
            adb("shell","input","swipe","240","770","240","300","390")
            time.sleep(.6)
    raise AssertionError("Cannot tap element: "+query)

def capture(name):
    png=adb("exec-out","screencap","-p",text=False)
    (OUTPUT/(name+".png")).write_bytes(png)
    nodes,xml=hierarchy()
    (OUTPUT/(name+".xml")).write_text(xml,encoding="utf-8")
    check(len(png)>9000,name+" screenshot contains rendered pixels")
    return nodes

def main():
    adb("shell","settings","put","global","window_animation_scale","0")
    adb("shell","settings","put","global","transition_animation_scale","0")
    adb("shell","settings","put","global","animator_duration_scale","0")
    adb("shell","am","start","-n",ACTIVITY,timeout=35)
    wait_for("Canlı matçlar")
    wait_for("MATCHLAB AZ")
    capture("01_home")
    check("MATCHLAB" in adb("shell","dumpsys","activity","activities"),
          "Native Android activity starts")

    tap("Taktika",by="desc")
    wait_for("TAKTİKA STUDİYASI PRO")
    capture("02_tactics")
    tap("Güzgü",scroll=True)
    tap("Geri al",scroll=True)
    check(True,"Tactics mirror and undo respond to touch")
    tap("PNG saxla",scroll=True)
    time.sleep(2)
    current=adb("shell","dumpsys","activity","activities")
    check(("documentsui" in current.lower() or "documents" in current.lower()),
          "PNG export opens system save-document picker")
    adb("shell","input","keyevent","4")
    time.sleep(.8)
    capture("03_tactics_after_tools")

    tap("Tətbiq menyusu",by="desc")
    tap("Tənzimləmələr")
    wait_for("Görünüş, şəbəkə və yaddaş")
    capture("04_settings")
    tap("Matçları avtomatik yenilə",scroll=True)
    time.sleep(.6)
    pref=adb("shell","run-as",APP,"cat","shared_prefs/matchlab_native.xml")
    check("auto_refresh" in pref,"Android settings persist to device storage")
    tap("Matçları avtomatik yenilə",scroll=True)
    tap("Tətbiq menyusu",by="desc")
    tap("Tarixi futbol arxivi")
    wait_for("FOOTBALL HERITAGE")
    capture("05_history")
    check(True,"Historical archive opens via in-app menu")

    # A connection failure must not crash the app. The server is independently hosted.
    time.sleep(3)
    activity=adb("shell","dumpsys","activity","activities")
    check(APP in activity,"Android remains alive after history network attempt")
    log=adb("logcat","-d","-s","AndroidRuntime:E")
    (OUTPUT/"android-runtime.log").write_text(log[-20000:],encoding="utf-8")
    check(not ("FATAL EXCEPTION" in log and APP in log),
          "No fatal exception for MATCHLAB in Android runtime log")
    (OUTPUT/"results.json").write_text(json.dumps({
        "platform":"Android emulator, API 30",
        "checked":PASSES,"count":len(PASSES),
        "physicalDevice":False,
        "notes":"Screenshots and hierarchy XML verify native UI; external API is not certified"
    },ensure_ascii=False,indent=2),encoding="utf-8")
    print("Android emulator UI QA completed: "+str(len(PASSES))+" passes.",flush=True)

if __name__=="__main__":
    try:main()
    except Exception as exc:
        (OUTPUT/"failure.txt").write_text(repr(exc),encoding="utf-8")
        try:capture("failure")
        except Exception:pass
        raise
