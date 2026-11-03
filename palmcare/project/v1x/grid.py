import sys, subprocess
from PIL import Image, ImageDraw
f,t,box,out=sys.argv[1],sys.argv[2],[int(v) for v in sys.argv[3].split(",")],sys.argv[4]
subprocess.run(["ffmpeg","-v","error","-y","-ss",t,"-i",f,"-frames:v","1","-vf","scale=1080:1920","/tmp/claude-0/-home-user-stockeasy/ae1b3550-c976-5b71-9f6e-2d57965fb3f7/scratchpad/v1x/_g.png"])
im=Image.open("/tmp/claude-0/-home-user-stockeasy/ae1b3550-c976-5b71-9f6e-2d57965fb3f7/scratchpad/v1x/_g.png").crop(box); d=ImageDraw.Draw(im)
x0,y0=box[:2]
for y in range((y0//25+1)*25,box[3],25): d.line((0,y-y0,im.width,y-y0),fill=(255,0,0) if y%100==0 else (0,255,0),width=1); d.text((2,y-y0),str(y),fill=(255,0,0))
for x in range((x0//50+1)*50,box[2],50): d.line((x-x0,0,x-x0,im.height),fill=(0,160,255),width=1); d.text((x-x0+2,im.height-14),str(x),fill=(0,0,255))
im.save(out)
