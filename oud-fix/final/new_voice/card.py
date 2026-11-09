import cv2,numpy as np,subprocess
W,H=1080,1920; S0,S1=639,799; KREF=21
SRC='ed/clean3b.mp4'; OUT='ed/clean3c.mp4'
ref=cv2.imread('ref_pkg.png').astype(np.float32)
# card in the link frame (inner quad), TL,TR,BR,BL
cq=np.float32([[395,722],[527,752],[497,990],[347,977]])
dq=np.float32([[121,668],[214,659],[209,838],[116,847]])   # in our frame KREF of the scene
cw,ch=140,260; flat=np.float32([[0,0],[cw,0],[cw,ch],[0,ch]])
card=cv2.warpPerspective(ref,cv2.getPerspectiveTransform(cq,flat),(cw,ch),flags=cv2.INTER_CUBIC)
cm=np.ones((ch,cw),np.float32); cm=cv2.erode(cm,np.ones((3,3),np.uint8))
dec=subprocess.Popen(['ffmpeg','-nostdin','-v','error','-i',SRC,'-f','rawvideo','-pix_fmt','bgr24','-'],stdout=subprocess.PIPE)
fr=[]
while True:
    b=dec.stdout.read(W*H*3)
    if len(b)<W*H*3: break
    fr.append(np.frombuffer(b,np.uint8).reshape(H,W,3).copy())
print('frames',len(fr))
# track lid lining (planar) through the scene, relative to frame S0+KREF
lid=np.zeros((H,W),np.uint8); cv2.fillPoly(lid,[np.int32([[100,460],[540,450],[545,820],[105,840]])],255)
G=[cv2.cvtColor(fr[i],cv2.COLOR_BGR2GRAY) for i in range(S0,S1)]
def Hto(k):
    a=G[KREF]; b=G[k]
    p=cv2.goodFeaturesToTrack(a,500,0.003,6,mask=lid)
    q,st,_=cv2.calcOpticalFlowPyrLK(a,b,p,None,winSize=(31,31),maxLevel=5); ok=st.ravel()==1
    Hh,_=cv2.findHomography(p[ok],q[ok],cv2.RANSAC,1.5); return Hh
Hs=[Hto(k) for k in range(len(G))]
C=np.array([cv2.perspectiveTransform(dq[None],Hh)[0] for Hh in Hs]); Cs=np.array([C[max(0,i-3):i+4].mean(0) for i in range(len(C))])
def ss(x): x=min(max(x,0),1); return x*x*(3-2*x)
GT0,GT1=23.10,25.08
for k in range(len(G)):
    i=S0+k; t=i/30; f=fr[i].astype(np.float32); q=Cs[k]
    M=cv2.getPerspectiveTransform(flat,q.astype(np.float32))
    lay=cv2.warpPerspective(card,M,(W,H),flags=cv2.INTER_CUBIC); a=cv2.warpPerspective(cm,M,(W,H))
    a=cv2.GaussianBlur(a,(0,0),0.8)
    # soft shadow of the card on the lining (light from upper right)
    sh=cv2.GaussianBlur(np.roll(np.roll(a,9,1),5,0),(0,0),9)*0.45*(1-a)
    f*=(1-sh)[...,None]
    # local light: lining brightness around the card -> card exposure
    f=f*(1-a[...,None])+lay*a[...,None]*1.0
    # gentle golden halo outside the card while "هدية سرية" is said (never over the card itself)
    g=ss((t-GT0)/0.5)*(1-ss((t-(GT1-0.5))/0.5))
    if g>0:
        halo=cv2.GaussianBlur(a,(0,0),18)*1.6+cv2.GaussianBlur(a,(0,0),45)*0.9
        halo=np.clip(halo,0,1)*(1-a)
        f=f+(halo*g*0.55)[...,None]*np.array([70,170,255],np.float32)
    fr[i]=np.clip(f,0,255).astype(np.uint8)
enc=subprocess.Popen(['ffmpeg','-nostdin','-v','error','-y','-f','rawvideo','-pix_fmt','bgr24','-s',f'{W}x{H}','-r','30','-i','-','-i',SRC,'-map','0:v','-map','1:a','-c:v','libx264','-crf','15','-preset','slow','-pix_fmt','yuv420p','-c:a','copy','-movflags','+faststart',OUT],stdin=subprocess.PIPE)
for f in fr: enc.stdin.write(f.tobytes())
enc.stdin.close(); enc.wait()
cv2.imwrite('card_chk.jpg',np.hstack([cv2.resize(fr[S0+k][350:1000,50:650],(450,488)) for k in (0,60,110,159)]))
