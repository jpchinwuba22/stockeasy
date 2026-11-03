import cv2,numpy as np
r=cv2.imread('../remo/public/p/molecular_cut.png',cv2.IMREAD_UNCHANGED)
f=cv2.imread('frm/0373.png')
gr=cv2.cvtColor(r[...,:3],cv2.COLOR_BGR2GRAY); gf=cv2.cvtColor(f,cv2.COLOR_BGR2GRAY)
print(r.shape)
a=r[...,3]; g=cv2.cvtColor(r[...,:3],cv2.COLOR_BGR2GRAY)
d=((g<170)&(a>200)).sum(1)
rows=[];s=None
for i,x in enumerate(d):
  if x>3 and s is None:s=i
  if x<=3 and s is not None: rows.append((s,i));s=None
print('real rows',rows)
d2=(gf<150)[:, 200:900].sum(1); rows=[];s=None
for i,x in enumerate(d2):
  if x>3 and s is None:s=i
  if x<=3 and s is not None: rows.append((s,i));s=None
print('flow rows',rows)
