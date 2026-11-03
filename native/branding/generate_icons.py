"""Restore the original MATCHLAB AZ M-and-dot logo from assets/icon.svg.

Pillow output is shared by Windows ICO and optional Android raster resources.
Native Android uses a committed XML vector, so Android Studio works without this script.
"""
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "native" / "branding"
OUT.mkdir(parents=True, exist_ok=True)
N = 1024
S = N / 64
im = Image.new("RGBA", (N, N), (0, 0, 0, 0))
d = ImageDraw.Draw(im)
d.rounded_rectangle((0, 0, N - 1, N - 1), radius=round(16*S), fill="#B5F568")
points = [(int(x*S), int(y*S)) for x,y in
          [(10,40),(21,17),(32,33),(43,17),(54,40)]]
d.line(points, fill="#132C20", width=round(8*S), joint="curve")
r=4*S
for x,y in [(10,40),(21,17),(32,33),(43,17),(54,40)]:
    cx,cy=x*S,y*S
    d.ellipse((int(cx-r),int(cy-r),int(cx+r),int(cy+r)),fill="#132C20")
cx,cy,r=49*S,47*S,8*S
d.ellipse((round(cx-r),round(cy-r),round(cx+r),round(cy+r)),fill="#132C20")
im.save(OUT/"matchlab_icon.png")
im.save(OUT/"matchlab_icon.ico",sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
res=ROOT/"native"/"android"/"app"/"src"/"main"/"res"
for density,size in [("mdpi",48),("hdpi",72),("xhdpi",96),("xxhdpi",144),("xxxhdpi",192)]:
    dest=res/("mipmap-"+density)
    dest.mkdir(parents=True, exist_ok=True)
    im.resize((size,size),Image.Resampling.LANCZOS).save(dest/"ic_launcher.png")
print("Restored original MATCHLAB AZ logo for native Windows/Android.")
