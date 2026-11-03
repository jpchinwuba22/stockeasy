import sys, subprocess
from PIL import Image, ImageDraw
f, ts, out = sys.argv[1], sys.argv[2].split(","), sys.argv[3]
ims = []
for t in ts:
    raw = subprocess.run(["ffmpeg","-v","error","-ss",t,"-i",f,"-frames:v","1","-vf","scale=1080:1920","-f","rawvideo","-pix_fmt","rgb24","-"],capture_output=True).stdout
    im = Image.frombytes("RGB",(1080,1920),raw); d = ImageDraw.Draw(im)
    for y in range(0,1920,100): d.line((0,y,1080,y),fill=(255,0,0) if y%500==0 else (0,255,0),width=2); d.text((4,y+2),str(y),fill=(255,255,0))
    for x in range(0,1080,100): d.line((x,0,x,1920),fill=(0,160,255),width=2); d.text((x+3,4),str(x),fill=(0,255,255))
    d.text((10,1890),t,fill=(255,255,255))
    ims.append(im.resize((432,768)))
s = Image.new("RGB",(432*len(ims),768))
for k,im in enumerate(ims): s.paste(im,(432*k,0))
s.save(out, quality=88)
