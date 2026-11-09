import cv2,numpy as np,glob,sys
S='/tmp/claude-0/-home-user-canva21/d92bd60e-9f87-52c3-ac35-11b21dbe0949/scratchpad'
F=sorted(glob.glob(S+'/cap2/df_n_09/*.png'))[:int(sys.argv[1])]
fr=[cv2.imread(f) for f in F]; h,w=fr[0].shape[:2]
K=cv2.imread('hero_props.png').astype(np.float32)
P=np.array([(340,1560),(560,1495),(980,1440),(1010,1460),(1015,1560),(1010,1700),(1000,1745),(700,1790),(430,1815),(390,1790),(340,1700)],np.float32)
al=np.zeros((h,w),np.float32); cv2.fillPoly(al,[P.astype(np.int32)],1.0); al=cv2.GaussianBlur(al,(0,0),6)
# H0: still -> frame0
g0=cv2.cvtColor(fr[0],cv2.COLOR_BGR2GRAY); gs=cv2.cvtColor(K.astype(np.uint8),cv2.COLOR_BGR2GRAY)
band=np.zeros((h,w),np.uint8); cv2.fillPoly(band,[P.astype(np.int32)],255); ring=cv2.dilate(band,np.ones((241,241),np.uint8)); ring[band>0]=0
orb=cv2.ORB_create(6000); ka,da=orb.detectAndCompute(gs,None); kb,db=orb.detectAndCompute(g0,None)
m=sorted(cv2.BFMatcher(cv2.NORM_HAMMING,crossCheck=True).match(da,db),key=lambda x:x.distance)[:1500]
H0,inl=cv2.findHomography(np.float32([ka[x.queryIdx].pt for x in m]),np.float32([kb[x.trainIdx].pt for x in m]),cv2.RANSAC,2); print('H0 inliers',inl.sum(),np.round(H0,3).tolist())
# track ring (marble + box bottom) through the clip
pts0=cv2.goodFeaturesToTrack(g0,1500,0.003,5,mask=cv2.warpPerspective(ring,H0,(w,h)))
Hs=[np.eye(3)]; prev=g0; pts=pts0.copy(); base=pts0.copy()
for k in range(1,len(fr)):
    g=cv2.cvtColor(fr[k],cv2.COLOR_BGR2GRAY)
    p1,st,_=cv2.calcOpticalFlowPyrLK(prev,g,pts,None,winSize=(31,31),maxLevel=4); ok=st.ravel()==1
    Hk,_=cv2.findHomography(base[ok],p1[ok],cv2.RANSAC,1.5); Hs.append(Hk); base=base[ok]; pts=p1[ok]; prev=g
C0=cv2.perspectiveTransform(P[None],H0)[0]
C=np.array([cv2.perspectiveTransform(C0[None],Hh)[0] for Hh in Hs]); Cs=np.array([C[max(0,i-3):i+4].mean(0) for i in range(len(C))])
vw=cv2.VideoWriter('hero_props.mp4',cv2.VideoWriter_fourcc(*'mp4v'),30,(w,h))
for k,f in enumerate(fr):
    Hk=cv2.findHomography(C0,Cs[k])[0]; M=Hk@H0
    lay=cv2.warpPerspective(K,M,(w,h),flags=cv2.INTER_LANCZOS4); a=cv2.warpPerspective(al,M,(w,h))[...,None]
    vw.write(np.clip(f*(1-a)+lay*a,0,255).astype(np.uint8))
vw.release(); print('frames',len(fr),'pts',len(base))
