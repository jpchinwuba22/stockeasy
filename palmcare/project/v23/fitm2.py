import cv2,numpy as np
r=cv2.imread('../remo/public/p/molecular_cut.png',cv2.IMREAD_UNCHANGED)
f=cv2.imread('frm/0373.png')
gr=cv2.cvtColor(r[...,:3],cv2.COLOR_BGR2GRAY); gf=cv2.cvtColor(f,cv2.COLOR_BGR2GRAY)
mr=np.zeros_like(gr); mr[400:500]=255; mr[r[...,3]<200]=0
mf=np.zeros_like(gf); mf[680:820,280:700]=255
s=cv2.SIFT_create(4000)
k1,d1=s.detectAndCompute(gr,mr); k2,d2=s.detectAndCompute(gf,mf)
m=cv2.BFMatcher().knnMatch(d1,d2,k=2); g=[a for a,b in m if a.distance<0.75*b.distance]
p1=np.float32([k1[a.queryIdx].pt for a in g]); p2=np.float32([k2[a.trainIdx].pt for a in g])
A,inl=cv2.estimateAffinePartial2D(p1,p2,method=cv2.RANSAC,ransacReprojThreshold=2.0); print(len(g),inl.sum()); print(A)
H=np.vstack([A,[0,0,1]]); np.save('Hm_ref.npy',H)
print('real500 top ->', H@[235,1263,1], ' real face edges at 1000:', np.where(r[1000,:,3]>200)[0][[0,-1]])
w=cv2.warpPerspective(r,H,(1080,1920)); a=w[...,3:]/255.
o=(f*(1-a*0.5)+w[...,:3]*a*0.5).astype(np.uint8); cv2.imwrite('qa/fitm.jpg',cv2.resize(o[650:1750,200:800],(300,550)))
