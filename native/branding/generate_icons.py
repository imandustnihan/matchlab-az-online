"""Build a compact native launcher icon from the MATCHLAB AZ green/black M-ball design.
Requires Pillow. This vector-like icon is optimized for small launcher sizes.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"native"/"branding"
OUT.mkdir(parents=True,exist_ok=True)
N=1024
im=Image.new("RGBA",(N,N),(0,0,0,0))
d=ImageDraw.Draw(im)
d.rounded_rectangle((20,20,1004,1004),radius=235,fill="#071019",outline="#68F42C",width=26)
d.rounded_rectangle((48,48,976,976),radius=211,outline="#113D26",width=5)
# strong stylized M, visible at launcher size
d.polygon([(218,620),(326,293),(418,293),(514,450),(612,293),(712,293),(814,620),(691,620),(655,469),(550,619),(478,619),(374,466),(338,620)],fill="#F4FAFC")
# lime diagonal motion mark
d.polygon([(464,616),(774,411),(728,495),(510,660)],fill="#72F72E")
d.polygon([(624,636),(722,636),(758,552),(660,568)],fill="#72F72E")
# ball in upper right
cx,cy,r=757,289,112
d.ellipse((cx-r,cy-r,cx+r,cy+r),fill="#F6FBFE",outline="#08131C",width=12)
def poly(points,fill): d.polygon(points,fill=fill)
poly([(cx,cy-47),(cx+49,cy-16),(cx+31,cy+40),(cx-30,cy+40),(cx-49,cy-16)],"#0C1822")
for angle in (18,90,162,234,306):
    a=math.radians(angle)
    px=cx+81*math.cos(a);py=cy+81*math.sin(a)
    pts=[(px+27*math.cos(math.radians(k*72)+a),py+27*math.sin(math.radians(k*72)+a)) for k in range(5)]
    poly(pts,"#0C1822")
# Wordmark for splash-like launcher asset, using installed fonts when available
font_candidates=[
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]
font=None
for path in font_candidates:
    if Path(path).exists():
        font=ImageFont.truetype(path,83)
        break
if font is None:font=ImageFont.load_default()
left="MATCHLAB";right=" AZ"
lbox=d.textbbox((0,0),left,font=font,stroke_width=0)
rbox=d.textbbox((0,0),right,font=font,stroke_width=0)
total=(lbox[2]-lbox[0])+(rbox[2]-rbox[0])
x=(N-total)/2
d.text((x,721),left,font=font,fill="#F4FAFC")
d.text((x+lbox[2]-lbox[0],721),right,font=font,fill="#74F52C")
# compact analysis glyph
d.rounded_rectangle((460,858,480,886),radius=3,fill="#F4FAFC")
d.rounded_rectangle((492,839,512,886),radius=3,fill="#F4FAFC")
d.rounded_rectangle((524,817,544,886),radius=3,fill="#F4FAFC")
im.save(OUT/"matchlab_icon.png")
im.save(OUT/"matchlab_icon.ico",sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
android=ROOT/"native"/"android"/"app"/"src"/"main"/"res"
for density,size in [("mdpi",48),("hdpi",72),("xhdpi",96),("xxhdpi",144),("xxxhdpi",192)]:
    dest=android/("mipmap-"+density)
    dest.mkdir(parents=True,exist_ok=True)
    im.resize((size,size),Image.Resampling.LANCZOS).save(dest/"ic_launcher.png")
print("Generated Windows ICO and Android launcher icons.")

# Installable PWA icons (generated on Render and in CI before publication).
pwa_dir=ROOT/"assets"
pwa_dir.mkdir(parents=True,exist_ok=True)
for size in (192,512):
    im.resize((size,size),Image.Resampling.LANCZOS).convert("RGB").save(pwa_dir/f"pwa-{size}.png",optimize=True)
# Keep the important central glyph within Android maskable icon safe area.
mask=Image.new("RGB",(1024,1024),"#071019")
inset=100
mask.paste(im.resize((1024-2*inset,1024-2*inset),Image.Resampling.LANCZOS),(inset,inset),im.resize((1024-2*inset,1024-2*inset),Image.Resampling.LANCZOS))
mask.resize((512,512),Image.Resampling.LANCZOS).save(pwa_dir/"pwa-512-maskable.png",optimize=True)
print("Generated installable PWA icons: 192, 512, 512 maskable")
