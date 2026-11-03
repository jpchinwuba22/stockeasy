import sys, subprocess
from PIL import Image, ImageDraw
clip,t,x0,y0,x1,y1,out=sys.argv[1],sys.argv[2],*[int(v) for v in sys.argv[3:7]],sys.argv[7]
raw=subprocess.run(["ffmpeg","-v","error","-ss",t,"-i",clip,"-frames:v","1","-vf","scale=1080:1920","-f","rawvideo","-pix_fmt","rgb24","-"],capture_output=True).stdout
im=Image.frombytes("RGB",(1080,1920),raw).crop((x0,y0,x1,y1)); d=ImageDraw.Draw(im)
for x in range((x0//20+1)*20,x1,20): d.line((x-x0,0,x-x0,y1-y0),fill=(255,0,255) if x%100==0 else (0,200,255),width=1); 
for x in range((x0//100+1)*100,x1,100): d.text((x-x0+2,2),str(x),fill=(255,0,255))
for y in range((y0//100+1)*100,y1,100): d.line((0,y-y0,x1-x0,y-y0),fill=(255,255,0),width=1); d.text((2,y-y0+2),str(y),fill=(255,255,0))
im.save(out,quality=90)
