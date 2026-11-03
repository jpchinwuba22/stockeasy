import sys, numpy as np
sys.path.insert(0,"labelfix"); sys.path.insert(0,"v2x")
import labelpatch as lp, fixclip3 as f3, edges
from fixclip2 import read_frames
from PIL import Image, ImageDraw
specs=[("fix/C2.mp4","citrus",2.5,(330,680,780,1000)),("fix/C1B.mp4","citrus",1.0,(330,700,760,1100)),("fix/C2r.mp4","citrus",8.5,(300,640,820,1000)),
       ("fix/C3.mp4","citrus",1.6,(300,780,780,1100)),("fix/C4.mp4","molecular",2.5,(340,860,740,1100)),("fix/C5.mp4","molecular",1.5,(330,860,720,1100)),
       ("fix/C7_card.mp4","citrus",0.1,(150,880,560,1150))]
ims=[]
for clip,name,t,roi in specs:
    fr=read_frames("v2x/"+clip)[min(int(t*24),222)]
    f3.use_mask(name); lbl=lp.Label(*f3.LABELS[name]); asp=(lbl.banner[2]-lbl.banner[0])/(lbl.banner[3]-lbl.banner[1])
    b=lp.find_banner(fr,roi,aspect=asp*0.9,close=6,min_fill=0.6); e=edges.measure(fr,b,name)
    im=Image.fromarray(fr); d=ImageDraw.Draw(im)
    for s in "LR":
        if e[s]:
            _,k,m,_=e[s]
            for y0,y1 in ((300,1800),):
                d.line((k*y0+m,y0,k*y1+m,y1),fill=(255,0,255),width=3)
    x0,y0,x1,y1=b[:4]
    im=im.crop((max(0,int(x0-250)),int(y0-500),min(1080,int(x1+250)),int(y1+700))).resize((300,int(300*(1200+(y1-y0))/(x1-x0+500))))
    ims.append(im)
h=max(i.height for i in ims); s=Image.new("RGB",(300*len(ims),h))
for k,i in enumerate(ims): s.paste(i,(300*k,0))
s.save("v2x/qa/edgeviz.jpg",quality=85)
