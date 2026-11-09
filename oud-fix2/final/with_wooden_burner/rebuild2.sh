set -e
cd /tmp/claude-0/-home-user-canva21/d92bd60e-9f87-52c3-ac35-11b21dbe0949/scratchpad/v2
K=/home/user/canva21/.claude/skills/product-ad-fidelity
# long scene: props pasted on the locked clip (static), then slowed to 12.2 s with motion interpolation (only smoke moves)
python3 - <<'PY'
import cv2,numpy as np
P=[[0,2045],[1150,2040],[1330,2170],[1330,2330],[0,2335]]
Kim=cv2.imread('addb/K_4.png'); J=cv2.imread('J_4.png')
cap=cv2.VideoCapture('k4s.mp4'); fps=cap.get(5); fr=[]
while True:
    ok,im=cap.read()
    if not ok: break
    fr.append(im)
h,w=fr[0].shape[:2]
ga=cv2.cvtColor(J,cv2.COLOR_BGR2GRAY); gb=cv2.cvtColor(fr[0],cv2.COLOR_BGR2GRAY)
band=np.zeros(ga.shape,np.uint8); cv2.fillPoly(band,[np.array(P,np.int32)],255); band=cv2.dilate(band,np.ones((301,301),np.uint8))
orb=cv2.ORB_create(8000); ka,da=orb.detectAndCompute(ga,band); kb,db=orb.detectAndCompute(gb,None)
m=sorted(cv2.BFMatcher(cv2.NORM_HAMMING,crossCheck=True).match(da,db),key=lambda x:x.distance)[:2500]
H0,inl=cv2.findHomography(np.float32([ka[x.queryIdx].pt for x in m]),np.float32([kb[x.trainIdx].pt for x in m]),cv2.RANSAC,2.5); print('inl',inl.sum())
al=np.zeros(ga.shape,np.float32); cv2.fillPoly(al,[np.array(P,np.int32)],1.0); al=cv2.GaussianBlur(al,(0,0),7)
lay=cv2.warpPerspective(Kim,H0,(w,h),flags=cv2.INTER_LANCZOS4).astype(np.float32); a=cv2.warpPerspective(al,H0,(w,h))[...,None]
vw=cv2.VideoWriter('addb/tp4.mp4',cv2.VideoWriter_fourcc(*'mp4v'),fps,(w,h))
for f in fr: vw.write(np.clip(f*(1-a)+lay*a,0,255).astype(np.uint8))
vw.release()
PY
ffmpeg -nostdin -v error -y -i addb/tp4.mp4 -vf "setpts=PTS*1.226,minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:vsbmc=1,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,deflicker=size=9:mode=pm" -frames:v 366 -c:v libx264 -crf 14 -preset slow -pix_fmt yuv420p addb/k4_slow.mp4
rm -rf kf && mkdir kf && ffmpeg -nostdin -v error -i addb/k4_slow.mp4 -frames:v 366 kf/%04d.png
ls kf | wc -l
rm -rf km2 && mkdir km2 && python3 - <<'PY'
import cv2,numpy as np,glob,subprocess
F=sorted(glob.glob('kf/*.png')); n=len(F); fps=30; hold=2.0; Z=1.22; cx,cy=470,1150
T=(n-1)/fps
for j,f in enumerate(F):
    t=j/fps; u=0 if t<=hold else (t-hold)/(T-hold)
    e=u*u*(3-2*u)*0.5+u*0.5
    s=1+(Z-1)*e
    M=np.float32([[s,0,cx-s*cx],[0,s,cy-s*cy]])
    cv2.imwrite(f'km2/{j+1:04d}.png',cv2.warpAffine(cv2.imread(f),M,(1080,1920),flags=cv2.INTER_LANCZOS4,borderMode=cv2.BORDER_REFLECT))
subprocess.run(['ffmpeg','-nostdin','-v','error','-y','-framerate','30','-i','km2/%04d.png','-c:v','libx264','-crf','14','-preset','slow','-pix_fmt','yuv420p','k4_hold_zoom.mp4'],check=True)
PY
bash $K/scripts/assemble.sh ad2.mp4 ad2_clean.mp4 src1.mp4:98:0.317:1:0 addb/tp2.mp4:68:0.3 src3.mp4:68:0.27:1:0 k4_hold_zoom.mp4:366:0:1:0 addb/tp5.mp4:141:0.15 addb/tp6.mp4:114:0.1
python3 - <<'PY'
import cv2,numpy as np,json,subprocess
B=[np.float32(p) for p in json.load(open('boxes6.json'))]; W,H=1080,1920
dec=subprocess.Popen(['ffmpeg','-nostdin','-v','error','-ss','24.70','-i','ad2_clean.mp4','-frames:v','114','-f','rawvideo','-pix_fmt','bgr24','-'],stdout=subprocess.PIPE)
fr=[]
while True:
    b=dec.stdout.read(W*H*3)
    if len(b)<W*H*3: break
    fr.append(np.frombuffer(b,np.uint8).reshape(H,W,3).copy())
g0=cv2.cvtColor(fr[0],cv2.COLOR_BGR2GRAY); tracks=[]
for bi,P in enumerate(B):
    m=np.zeros((H,W),np.uint8); cv2.fillPoly(m,[P.astype(np.int32)],255)
    if bi==1: q=np.zeros_like(m); cv2.fillPoly(q,[B[2].astype(np.int32)],255); m[q>0]=0
    m=cv2.erode(m,np.ones((15,15),np.uint8)); p0=cv2.goodFeaturesToTrack(g0,600,0.005,6,mask=m)
    As=[np.float32([[1,0,0],[0,1,0]])]; prev=g0; pts=p0
    for k in range(1,len(fr)):
        g=cv2.cvtColor(fr[k],cv2.COLOR_BGR2GRAY); p1,st,_=cv2.calcOpticalFlowPyrLK(prev,g,pts,None,winSize=(31,31),maxLevel=4); ok=st.ravel()==1
        A,_=cv2.estimateAffinePartial2D(p0[ok],p1[ok],method=cv2.RANSAC,ransacReprojThreshold=1.5); As.append(A); p0=p0[ok]; pts=p1[ok]; prev=g
    a=np.array([A.ravel() for A in As]); tracks.append([a[max(0,i-4):i+5].mean(0).reshape(2,3).tolist() for i in range(len(a))])
json.dump(tracks,open('box_tracks.json','w')); print('tracks',len(tracks[0]))
PY
python3 fx.py
python3 cap2.py ad2_clean_fx.mp4 ad2_final.mp4
echo ALLDONE
