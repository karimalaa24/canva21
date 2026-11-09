import cv2,numpy as np,json,sys
P={'2':[[1085,1790],[1170,1775],[1480,1940],[1490,2060],[1400,2110],[1215,2045],[1110,1940]],
   '4':[[0,2045],[1150,2040],[1330,2170],[1330,2330],[0,2335]],
   '5':[[580,2060],[1230,1880],[1330,1950],[1450,2250],[1250,2420],[720,2550],[600,2480],[560,2380]],
   '6':[[120,2110],[1250,1985],[1360,2060],[1400,2300],[1250,2430],[800,2480],[200,2490],[90,2400]]}
out={}
for n,p in P.items():
    a=cv2.imread(f'A{n}.png').astype(np.float32); j=cv2.imread(f'../J_{n}.png').astype(np.float32)
    m=np.zeros(j.shape[:2],np.float32); cv2.fillPoly(m,[np.array(p,np.int32)],1.0); m=cv2.GaussianBlur(m,(0,0),7)[...,None]
    c=j*(1-m)+a*m; cv2.imwrite(f'K_{n}.png',np.clip(c,0,255).astype(np.uint8))
    v=c.copy(); cv2.polylines(v,[np.array(p,np.int32)],True,(0,255,255),3)
    out[n]=v
t=[cv2.resize(out[n][1300:2752],(420,398)) for n in '2456']
cv2.imwrite('kcheck.jpg',np.vstack([np.hstack(t[:2]),np.hstack(t[2:])]))
