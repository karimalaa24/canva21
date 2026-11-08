import cv2,numpy as np,subprocess,json,sys
SRC='ad2_clean.mp4'; OUT='ad2_clean_fx.mp4'; W,H,FPS=1080,1920,30
CARD=np.float32([(324,756),(438,768),(424,976),(300,956)])
BOXES=[np.float32([(0,812),(355,800),(380,1110),(560,1290),(558,1415),(95,1500),(0,1450)]),
       np.float32([(385,885),(700,870),(770,950),(770,1095),(552,1095),(552,1060),(385,1060)]),
       np.float32([(552,1095),(905,1095),(975,1180),(975,1345),(552,1345)])]
S5=(542,683); S6=(683,797)
CARD_T=21.67; LINE_T0=23.27; LINE_T1=25.17; L4=(233,541)
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
            pts,L=resample(tf(np.float32(Bp),A),600); N=600
            st0=int(np.argmin(pts[:,0]+pts[:,1])); pts=np.roll(pts,-st0,axis=0)
            half=int(N/2*prog)
            fw=pts[:half+1]; bw=pts[::-1][:half+1] if half>0 else pts[:1]
            if prog>=0.999: cv2.polylines(line,[pts.astype(np.int32)],True,1.0,3,cv2.LINE_AA)
            else:
                cv2.polylines(line,[fw.astype(np.int32)],False,1.0,3,cv2.LINE_AA)
                cv2.polylines(line,[np.vstack([pts[:1],pts[::-1][:half]]).astype(np.int32)],False,1.0,3,cv2.LINE_AA)
                for hp in (fw[-1],bw[-1]): cv2.circle(spark,(int(hp[0]),int(hp[1])),5,1.0,-1,cv2.LINE_AA)
        settle=ss((t-LINE_T1)/0.6)
        glow=cv2.GaussianBlur(line,(0,0),4)*1.3+cv2.GaussianBlur(line,(0,0),12)*(1.6+0.6*settle)+cv2.GaussianBlur(line,(0,0),30)*(1.0+0.8*settle)
        sp=cv2.GaussianBlur(spark,(0,0),2.5)*2.5+cv2.GaussianBlur(spark,(0,0),12)*4
        pulse=1.0+0.06*np.sin((t-LINE_T1)*3.0)*settle
        add=(glow*pulse+sp)[...,None]*GOLD+line[...,None]*np.array([215,245,255],np.float32)*0.95
        img=img+add
    if L4[0]<=i<L4[1]:
        j=i-L4[0]; tt=j/30; TT=(L4[1]-L4[0]-1)/30
        u=0 if tt<=2 else (tt-2)/(TT-2); e=u*u*(3-2*u)*0.5+u*0.5; zs=1+0.22*e
        Z=lambda x,y:(470+zs*(x-470),1150+zs*(y-1150))
        fr=frames[i]; g=cv2.cvtColor(fr,cv2.COLOR_BGR2GRAY).astype(np.float32)
        # 1) warm bloom on highlights (gold, lettering, lantern), breathing
        hi=np.clip((g-150)/80,0,1); bloom=cv2.GaussianBlur(hi,(0,0),18)*0.55+cv2.GaussianBlur(hi,(0,0),45)*0.35
        br=0.75+0.25*np.sin(tt*1.6)
        img=img+bloom[...,None]*np.array([60,150,235],np.float32)*br
        # 2) golden light sweeps across the products (two passes)
        prod=np.zeros((H,W),np.float32); P=np.array([Z(40,860),Z(1070,860),Z(1070,1430),Z(40,1430)],np.int32); cv2.fillPoly(prod,[P],1.0)
        prod=cv2.GaussianBlur(prod,(0,0),40)
        yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
        for (t0,t1) in ((2.4,4.6),(6.6,8.8)):
            if t0<=tt<=t1:
                v=(tt-t0)/(t1-t0); cx=-400+1900*v
                band=np.exp(-((xx*0.8+0.6*(yy-1150)-cx)/120)**2)*np.sin(np.pi*v)
                img=img*(1+(band*prod*0.38)[...,None]*np.array([0.45,0.8,1.0],np.float32))
        # 3) twinkling star glints on gold details
        G=[(555,970,0.6),(200,1080,1.9),(620,1140,3.2),(640,1255,4.4),(295,1355,5.5),(640,1365,6.3),(905,1080,7.2),(800,920,8.1),(1055,920,8.9),(625,1215,9.6)]
        star=np.zeros((H,W),np.float32)
        for gx,gy,gt in G:
            d=tt-gt
            if 0<=d<=0.9:
                a=np.sin(np.pi*d/0.9); x,y=Z(gx,gy); x,y=int(x),int(y); L=int(38*a*zs)
                cv2.line(star,(x-L,y),(x+L,y),a,2,cv2.LINE_AA); cv2.line(star,(x,y-L),(x,y+L),a,2,cv2.LINE_AA)
                l2=int(L*0.45); cv2.line(star,(x-l2,y-l2),(x+l2,y+l2),a*0.7,1,cv2.LINE_AA); cv2.line(star,(x-l2,y+l2),(x+l2,y-l2),a*0.7,1,cv2.LINE_AA)
                cv2.circle(star,(x,y),4,a,-1,cv2.LINE_AA)
        st=cv2.GaussianBlur(star,(0,0),1.2)*1.4+cv2.GaussianBlur(star,(0,0),7)*1.6
        img=img+st[...,None]*np.array([170,225,255],np.float32)
    frames[i]=np.clip(img,0,255).astype(np.uint8)
enc=subprocess.Popen(['ffmpeg','-nostdin','-v','error','-y','-f','rawvideo','-pix_fmt','bgr24','-s',f'{W}x{H}','-r','30','-i','-','-i',SRC,'-map','0:v','-map','1:a','-c:v','libx264','-crf','15','-preset','slow','-pix_fmt','yuv420p','-c:a','copy','-movflags','+faststart',OUT],stdin=subprocess.PIPE)
for f in frames: enc.stdin.write(f.tobytes())
enc.stdin.close(); enc.wait(); print('done')
