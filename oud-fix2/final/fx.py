import cv2,numpy as np,subprocess,json,sys
SRC='ad2_clean.mp4'; OUT='ad2_clean_fx.mp4'; W,H,FPS=1080,1920,30
CARD=np.float32([(324,756),(438,768),(424,976),(300,956)])
BOXES=[np.float32([(0,812),(355,800),(380,1110),(560,1290),(558,1415),(95,1500),(0,1450)]),
       np.float32([(385,885),(700,870),(770,950),(770,1095),(552,1095),(552,1060),(385,1060)]),
       np.float32([(552,1095),(905,1095),(975,1180),(975,1345),(552,1345)])]
S5=(542,683); S6=(683,797)
CARD_T=21.67; LINE_T0=23.37; LINE_T1=24.6
GOLD=np.array([120,205,255],np.float32)   # BGR warm gold
orb=cv2.ORB_create(3000); bf=cv2.BFMatcher(cv2.NORM_HAMMING,crossCheck=True)
def tracker(ref):
    g=cv2.cvtColor(ref,cv2.COLOR_BGR2GRAY); m=np.zeros(g.shape,np.uint8); m[700:1600]=255
    k0,d0=orb.detectAndCompute(g,m)
    def f(img):
        g=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY); k,d=orb.detectAndCompute(g,m)
        mm=sorted(bf.match(d0,d),key=lambda x:x.distance)[:500]
        A,_=cv2.estimateAffinePartial2D(np.float32([k0[x.queryIdx].pt for x in mm]),np.float32([k[x.trainIdx].pt for x in mm]),method=cv2.RANSAC,ransacReprojThreshold=2)
        return A
    return f
def tf(P,A): return (np.c_[P,np.ones(len(P))]@A.T).astype(np.float32)
def smooth_As(As,k=7):
    a=np.array([A.ravel() for A in As]); out=[]
    for i in range(len(a)): out.append(a[max(0,i-k):i+k+1].mean(0).reshape(2,3))
    return out
def ss(x): x=min(max(x,0),1); return x*x*(3-2*x)
dec=subprocess.Popen(['ffmpeg','-nostdin','-v','error','-i',SRC,'-f','rawvideo','-pix_fmt','bgr24','-'],stdout=subprocess.PIPE)
frames=[]
while True:
    b=dec.stdout.read(W*H*3)
    if len(b)<W*H*3: break
    frames.append(np.frombuffer(b,np.uint8).reshape(H,W,3).copy())
print('frames',len(frames))
# tracking
tr5=tracker(frames[S5[0]]); A5=smooth_As([tr5(frames[i]) for i in range(*S5)])
tr6=tracker(frames[S6[0]]); A6=smooth_As([tr6(frames[i]) for i in range(*S6)])
rng=np.random.default_rng(3); prev_add=None
def resample(P,n):
    P=np.vstack([P,P[:1]]); seg=np.linalg.norm(np.diff(P,axis=0),axis=1); L=np.r_[0,np.cumsum(seg)]
    t=np.linspace(0,L[-1],n,endpoint=False); x=np.interp(t,L,P[:,0]); y=np.interp(t,L,P[:,1]); return np.c_[x,y],L[-1]
for i in range(len(frames)):
    t=i/FPS; img=frames[i].astype(np.float32)
    if S5[0]<=i<S5[1] and t>=CARD_T:
        a=ss((t-CARD_T)/0.6)*(0.85+0.15*np.sin((t-CARD_T)*4))
        A=A5[i-S5[0]]; P=tf(CARD,A).astype(np.int32)
        card=np.zeros((H,W),np.uint8); cv2.fillPoly(card,[P],255)
        ring=cv2.dilate(card,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(9,9)))-card
        halo=cv2.GaussianBlur(cv2.dilate(card,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(31,31))).astype(np.float32)/255,(0,0),28)
        halo*= (1-card/255.)                       # never over the card (logo stays clean)
        rim=cv2.GaussianBlur(ring.astype(np.float32)/255,(0,0),2.5)
        img=img+ (halo*0.9+rim*0.8)[...,None]*GOLD*a
        # soft warm lift of the lining around the card only
    if S6[0]<=i<S6[1] and t>=LINE_T0:
        A=A6[i-S6[0]]; prog=ss((t-LINE_T0)/(LINE_T1-LINE_T0)); pulse=0.9+0.1*np.sin((t-LINE_T1)*5)
        line=np.zeros((H,W),np.float32); spark=np.zeros((H,W),np.float32)
        for bi,Bp in enumerate(json.load(open('boxes6.json'))):
            pts,L=resample(tf(np.float32(Bp),A),500); nn=max(2,int(500*prog))
            cv2.polylines(line,[pts[:nn].astype(np.int32)],prog>=0.999,1.0,2,cv2.LINE_AA)
            for kk in range(3):
                ph=((t*0.35+kk/3+bi*0.17)%1.0)
                if ph<=prog:
                    x,y=pts[int(ph*499)]; cv2.circle(spark,(int(x),int(y)),3,1.0,-1,cv2.LINE_AA)
        glow=cv2.GaussianBlur(line,(0,0),3)*1.2+cv2.GaussianBlur(line,(0,0),10)*1.6+cv2.GaussianBlur(line,(0,0),24)*1.2
        sp=cv2.GaussianBlur(spark,(0,0),2)*2+cv2.GaussianBlur(spark,(0,0),9)*3
        core=line*1.0
        add=(glow*pulse+sp)[...,None]*GOLD+core[...,None]*np.array([200,240,255],np.float32)*0.9
        if 'prev_add' in globals() and prev_add is not None: add=0.6*add+0.4*prev_add
        prev_add=add
        img=img+add
    frames[i]=np.clip(img,0,255).astype(np.uint8)
enc=subprocess.Popen(['ffmpeg','-nostdin','-v','error','-y','-f','rawvideo','-pix_fmt','bgr24','-s',f'{W}x{H}','-r','30','-i','-','-i',SRC,'-map','0:v','-map','1:a','-c:v','libx264','-crf','15','-preset','slow','-pix_fmt','yuv420p','-c:a','copy','-movflags','+faststart',OUT],stdin=subprocess.PIPE)
for f in frames: enc.stdin.write(f.tobytes())
enc.stdin.close(); enc.wait(); print('done')
