import cv2,numpy as np,subprocess,sys
W={'1':[(668,1101,207,49)],'2':[(1131,1997,405,134)],'3':[(419,1205,168,39)],
 '4':[(239,1281,137,66),(663,1229,302,97),(774,1416,163,72),(1199,1541,163,101)],
 '6':[(590,1313,400,122),(81,1474,164,62),(865,1688,148,102)],
 '7':[(852,1161,388,132),(910,1413,284,121),(471,1727,252,163)],
 '8':[(667,1103,213,46)],
 '9':[(256,1085,311,93),(694,1312,165,67),(212,1341,204,93),(1096,1392,267,100)]}
SRC={'1':'final_st2/scene1.png','2':'final_st2/scene2.png','3':'final_st2/scene3.png','4':'final_st2/scene4.png','6':'bag_new.png','7':'final_st2/scene7.png','8':'final_st2/scene8.png','9':'final_st2/scene9.png'}
n,clip,out=sys.argv[1],sys.argv[2],sys.argv[3]
A=cv2.imread(SRC[n]); B=cv2.imread(f'txt/a{n}.png')
cap=cv2.VideoCapture(clip); fps=cap.get(5); fr=[]
while True:
    ok,im=cap.read()
    if not ok: break
    fr.append(im)
h,w=fr[0].shape[:2]
# still -> frame0
ga=cv2.cvtColor(A,cv2.COLOR_BGR2GRAY); g0=cv2.cvtColor(fr[0],cv2.COLOR_BGR2GRAY)
orb=cv2.ORB_create(8000); ka,da=orb.detectAndCompute(ga,None); kb,db=orb.detectAndCompute(g0,None)
m=sorted(cv2.BFMatcher(cv2.NORM_HAMMING,crossCheck=True).match(da,db),key=lambda x:x.distance)[:2500]
H0,inl=cv2.findHomography(np.float32([ka[x.queryIdx].pt for x in m]),np.float32([kb[x.trainIdx].pt for x in m]),cv2.RANSAC,2.5); print('H0 inl',int(inl.sum()))
G=[cv2.cvtColor(f,cv2.COLOR_BGR2GRAY) for f in fr]
words=[]
for (x,y,ww,hh) in W[n]:
    pad=14; q=np.float32([[x-pad,y-pad],[x+ww+pad,y-pad],[x+ww+pad,y+hh+pad],[x-pad,y+hh+pad]])
    alpha=np.zeros(A.shape[:2],np.float32); cv2.rectangle(alpha,(x-pad,y-pad),(x+ww+pad,y+hh+pad),1.0,-1); alpha=cv2.GaussianBlur(alpha,(0,0),5)
    q0=cv2.perspectiveTransform(q[None],H0)[0]
    # track a region around the word on the same surface
    c=q0.mean(0); sz=np.abs(q0-c).max(0)
    reg=np.zeros((h,w),np.uint8); x0,y0=(c-sz*2.2).astype(int); x1,y1=(c+sz*2.2).astype(int); cv2.rectangle(reg,(max(x0,0),max(y0,0)),(min(x1,w-1),min(y1,h-1)),255,-1)
    pts=cv2.goodFeaturesToTrack(G[0],400,0.003,4,mask=reg)
    Hs=[]
    prev=G[0]; p=pts.copy(); base=pts.copy(); Hacc=np.eye(3)
    for k in range(len(fr)):
        if k==0: Hs.append(np.eye(3)); continue
        p1,st,_=cv2.calcOpticalFlowPyrLK(prev,G[k],p,None,winSize=(25,25),maxLevel=4); ok=st.ravel()==1
        Hk,_=cv2.findHomography(base[ok],p1[ok],cv2.RANSAC,1.5); Hs.append(Hk if Hk is not None else Hs[-1]); base=base[ok]; p=p1[ok]; prev=G[k]
        if len(p)<30:   # refresh
            p=cv2.goodFeaturesToTrack(G[k],400,0.003,4,mask=cv2.warpPerspective(reg,Hs[-1],(w,h))); base=cv2.perspectiveTransform(p,np.linalg.inv(Hs[-1]))
    C=np.array([cv2.perspectiveTransform(q0[None],Hh)[0] for Hh in Hs]); Cs=np.array([C[max(0,i-3):i+4].mean(0) for i in range(len(C))])
    words.append((q0,Cs,alpha))
vw=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','bgr24','-s',f'{w}x{h}','-r',str(fps),'-i','-','-c:v','libx264','-crf','14','-preset','slow','-pix_fmt','yuv420p',out],stdin=subprocess.PIPE)
Bf=B.astype(np.float32)
for k,f in enumerate(fr):
    o=f.astype(np.float32)
    for q0,Cs,alpha in words:
        M=cv2.getPerspectiveTransform(q0,Cs[k].astype(np.float32))@H0
        lay=cv2.warpPerspective(Bf,M,(w,h),flags=cv2.INTER_LANCZOS4); a=cv2.warpPerspective(alpha,M,(w,h))[...,None]
        # match local brightness of this frame (lighting/zoom changes)
        o=o*(1-a)+lay*a
    vw.stdin.write(np.clip(o,0,255).astype(np.uint8).tobytes())
vw.stdin.close(); vw.wait(); print(n,'frames',len(fr))
