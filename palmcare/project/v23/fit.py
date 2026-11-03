import cv2,numpy as np
r=cv2.imread('remo/public/p/dermalight_cut.png',cv2.IMREAD_UNCHANGED)
f=cv2.imread('v23/qa/d_14.3.png')
gr=cv2.cvtColor(r[...,:3],cv2.COLOR_BGR2GRAY); gf=cv2.cvtColor(f,cv2.COLOR_BGR2GRAY)
mr=np.zeros_like(gr); mr[400:520]=255; mr[1010:1250]=255; mr[r[...,3]<200]=0
mf=np.zeros_like(gf); mf[780:900,80:540]=255; mf[1420:1700,80:540]=255
s=cv2.SIFT_create(4000)
k1,d1=s.detectAndCompute(gr,mr); k2,d2=s.detectAndCompute(gf,mf)
m=cv2.BFMatcher().knnMatch(d1,d2,k=2); g=[a for a,b in m if a.distance<0.75*b.distance]
p1=np.float32([k1[a.queryIdx].pt for a in g]); p2=np.float32([k2[a.trainIdx].pt for a in g])
H,inl=cv2.findHomography(p1,p2,cv2.RANSAC,3.0); print(len(g),inl.sum()); print(H)
np.save('v23/H_ref.npy',H)
w=cv2.warpPerspective(r,H,(1080,1920))
a=w[...,3:]/255.; o=(f*(1-a*0.5)+w[...,:3]*a*0.5).astype(np.uint8)
cv2.imwrite('v23/qa/fit.jpg',cv2.resize(o[700:1800,0:600],(300,550)))
