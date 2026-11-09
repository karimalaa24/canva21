"""Paste the original static props (wooden burner, sticks, tube) into an already-animated clip:
still K (with props) -> clip frame 0 via homography; then the floor plane is tracked frame to frame
(LK on marble texture around the props) and the prop layer is warped with it."""
import cv2,numpy as np,subprocess,sys,json
n,clip,out=sys.argv[1],sys.argv[2],sys.argv[3]
P={'2':[[1085,1790],[1170,1775],[1480,1940],[1490,2060],[1400,2110],[1215,2045],[1110,1940]],
   '4':[[0,2045],[1150,2040],[1330,2170],[1330,2330],[0,2335]],
   '5':[[580,2060],[1230,1880],[1330,1950],[1450,2250],[1250,2420],[720,2550],[600,2480],[560,2380]],
   '6':[[120,2110],[1250,1985],[1360,2060],[1400,2300],[1250,2430],[800,2480],[200,2490],[90,2400]]}[n]
K=cv2.imread(f'K_{n}.png'); J=cv2.imread(f'../J_{n}.png')
cap=cv2.VideoCapture(clip); fps=cap.get(5); fr=[]
while True:
    ok,im=cap.read()
    if not ok: break
    fr.append(im)
h,w=fr[0].shape[:2]
# still (J, no props) -> frame0
def H_between(a,b,mask=None):
    ga=cv2.cvtColor(a,cv2.COLOR_BGR2GRAY); gb=cv2.cvtColor(b,cv2.COLOR_BGR2GRAY)
    orb=cv2.ORB_create(8000); ka,da=orb.detectAndCompute(ga,mask); kb,db=orb.detectAndCompute(gb,None)
    m=sorted(cv2.BFMatcher(cv2.NORM_HAMMING,crossCheck=True).match(da,db),key=lambda x:x.distance)[:2500]
    pa=np.float32([ka[x.queryIdx].pt for x in m]); pb=np.float32([kb[x.trainIdx].pt for x in m])
    Hh,inl=cv2.findHomography(pa,pb,cv2.RANSAC,2.5); return Hh,int(inl.sum())
poly=np.array(P,np.float32)
# local mask around props (band) for still->frame0 fit: floor near props
band=np.zeros(J.shape[:2],np.uint8); cv2.fillPoly(band,[poly.astype(np.int32)],255); band=cv2.dilate(band,np.ones((301,301),np.uint8))
H0,ni=H_between(J,fr[0],band); print('still->f0 inliers',ni)
alpha=np.zeros(J.shape[:2],np.float32); cv2.fillPoly(alpha,[poly.astype(np.int32)],1.0); alpha=cv2.GaussianBlur(alpha,(0,0),7)
# track floor near props in the clip
p0poly=cv2.perspectiveTransform(poly[None],H0)[0]
m0=np.zeros((h,w),np.uint8); cv2.fillPoly(m0,[p0poly.astype(np.int32)],255)
ring=cv2.dilate(m0,np.ones((161,161),np.uint8))
g0=cv2.cvtColor(fr[0],cv2.COLOR_BGR2GRAY); pts0=cv2.goodFeaturesToTrack(g0,1500,0.003,5,mask=ring)
Hs=[np.eye(3)]; prev=g0; pts=pts0.copy(); base=pts0.copy()
for k in range(1,len(fr)):
    g=cv2.cvtColor(fr[k],cv2.COLOR_BGR2GRAY)
    p1,st,_=cv2.calcOpticalFlowPyrLK(prev,g,pts,None,winSize=(31,31),maxLevel=4); ok=st.ravel()==1
    Hk,inl=cv2.findHomography(base[ok],p1[ok],cv2.RANSAC,1.5); Hs.append(Hk); base=base[ok]; pts=p1[ok]; prev=g
# smooth homographies (temporal, on corner positions of the polygon)
C=np.array([cv2.perspectiveTransform(p0poly[None],Hh)[0] for Hh in Hs])
Cs=np.array([C[max(0,i-3):i+4].mean(0) for i in range(len(C))])
vw=cv2.VideoWriter(out,cv2.VideoWriter_fourcc(*'mp4v'),fps,(w,h))
for k,f in enumerate(fr):
    Hk=cv2.getPerspectiveTransform(p0poly[:4].astype(np.float32),Cs[k][:4].astype(np.float32)) if len(poly)==4 else cv2.findHomography(p0poly,Cs[k])[0]
    M=Hk@H0
    lay=cv2.warpPerspective(K,M,(w,h),flags=cv2.INTER_LANCZOS4); a=cv2.warpPerspective(alpha,M,(w,h))[...,None]
    o=f*(1-a)+lay*a
    vw.write(np.clip(o,0,255).astype(np.uint8))
vw.release(); print('frames',len(fr),'tracked pts',len(base))
