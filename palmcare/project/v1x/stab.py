import sys, cv2, numpy as np, subprocess
f=sys.argv[1]; x0,y0,x1,y1=[int(v) for v in sys.argv[2].split(",")]
p=subprocess.run(["ffmpeg","-v","error","-i",f,"-f","rawvideo","-pix_fmt","gray","-"],capture_output=True).stdout
fr=np.frombuffer(p,np.uint8).reshape(-1,1280,720)
k=fr[0][y0:y1,x0:x1].astype(np.float32)
for i in range(0,len(fr),12):
    (dx,dy),r=cv2.phaseCorrelate(k,fr[i][y0:y1,x0:x1].astype(np.float32))
    print(f"{i/24:5.2f}s dx {dx:+5.1f} dy {dy:+5.1f} r {r:.2f}")
