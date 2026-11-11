"""Ad 5 clean base: original Kling clips (no captions), real frames only (24->30 by frame picking),
free local zoom on the hook and the burner scene, product lift grade. usage: base5.py out.mp4 [sample]"""
import cv2,numpy as np,subprocess,sys
SRC='/tmp/claude-0/-home-user-canva21/d92bd60e-9f87-52c3-ac35-11b21dbe0949/scratchpad/v5/src/'
W,H,FPS=1080,1920,30
def ss(x): x=min(max(x,0),1); return x*x*(3-2*x)
def eo(x): x=min(max(x,0),1); return 1-(1-x)**3
# name, clip, src_from, src_to (24fps frame idx), out_start(s), out_end(s), zoom(t_rel,dur)->(scale,cx,cy), lift mode
S=[
 ('hook','ksMJTn216B',13.6,83.0,0.00,2.90, lambda u,d:(1+0.50*(1-eo(u/1.30)),540,1560),'full'),
 ('reviews','ksMJTn216B',83.0,162.0,2.90,6.20,None,'full'),
 ('close','rgpyM0zxtc',10,81,6.20,9.17,None,'full'),
 ('three','0elmD32TfW',20,159,9.17,14.40,None,'bottom'),
 ('burner','aFZ133pfSh',37,120,14.40,17.88, lambda u,d:(1.0+0.22*ss(u/d),520,1430),'bottom'),
 ('arrange','gO83YtRSXO',10,57,17.88,19.85,None,'bottom'),
 ('bag','XmyQ_fixed',12,88,19.85,22.75,None,'bottom'),
 ('hero','IfNq46OtvE',19,127,22.75,27.05,None,'bottom'),
 ('end','s7B6wZel8e',7,120,27.05,31.40,None,'bottom'),
]
def lift(f,mode,strength=1.0):
    x=f.astype(np.float32)/255
    L=0.299*x[...,2]+0.587*x[...,1]+0.114*x[...,0]+1e-4
    gain=np.clip(np.power(L,0.78)/L,1,1.55)
    if mode=='bottom':
        m=np.clip((np.arange(H)/H-0.36)/0.24,0,1); m=m*m*(3-2*m); gain=1+(gain-1)*m[:,None]
    gain=1+(gain-1)*strength
    y=x*gain[...,None]
    # gentle overall warmth / saturation +6%
    g=y.mean(2,keepdims=True); y=g+(y-g)*1.06
    return np.clip(y*255,0,255).astype(np.uint8)
def load(name):
    c=cv2.VideoCapture(SRC+name+'.mp4'); fr=[]
    while True:
        ok,im=c.read()
        if not ok: break
        fr.append(im)
    return fr
def cover(im):
    h,w=im.shape[:2]; s=max(W/w,H/h); im=cv2.resize(im,(int(round(w*s)),int(round(h*s))),interpolation=cv2.INTER_LANCZOS4 if s>1 else cv2.INTER_AREA)
    y0=(im.shape[0]-H)//2; x0=(im.shape[1]-W)//2; return im[y0:y0+H,x0:x0+W]
def zoom(im,s,cx,cy):
    M=np.float32([[s,0,cx-s*cx],[0,s,cy-s*cy]]); return cv2.warpAffine(im,M,(W,H),flags=cv2.INTER_LANCZOS4,borderMode=cv2.BORDER_REFLECT)
out=sys.argv[1]; sample=len(sys.argv)>2
enc=None if sample else subprocess.Popen(['ffmpeg','-nostdin','-v','error','-y','-f','rawvideo','-pix_fmt','bgr24','-s',f'{W}x{H}','-r','30','-i','-','-c:v','libx264','-crf','12','-preset','slow','-pix_fmt','yuv420p',out],stdin=subprocess.PIPE)
cache={}; N=int(round(S[-1][5]*FPS)); samples=[]
for n in range(N):
    t=n/FPS
    sc=[s for s in S if s[4]<=t+1e-6<s[5]+1e-6][0]
    name,clip,a,b,t0,t1,zf,mode=sc
    if clip not in cache: cache={clip:[cover(f) for f in load(clip)]}
    fr=cache[clip]; nf=int(round((t1-t0)*FPS))
    k=int(round(a+(b-a)*min((t-t0)*FPS/max(nf-1,1),1))); k=min(k,len(fr)-1)
    im=fr[k]
    if zf: s,cx,cy=zf(t-t0,t1-t0); im=zoom(im,s,cx,cy) if abs(s-1)>1e-3 else im
    im=lift(im,mode)
    if sample:
        if n in sample_set if (sample_set:=set(int(round(v*FPS)) for v in [0.05,1.5,4.0,7.5,11.5,15.0,17.5,19.0,21.5,25.0,29.5,31.3])) else False:
            samples.append((t,im,cache[clip][k]))
    else: enc.stdin.write(im.tobytes())
if sample:
    rows=[np.hstack([cv2.resize(o,(270,480)),cv2.resize(lift(o*0+o,'none',0) if False else o,(270,480)) ,cv2.resize(i,(270,480))]) for t,i,o in samples]
    tiles=[np.hstack([cv2.resize(o,(270,480)),cv2.resize(i,(270,480))]) for t,i,o in samples]
    rows=[np.hstack(tiles[j:j+3]) for j in range(0,len(tiles),3)]
    cv2.imwrite(out,np.vstack(rows))
else: enc.stdin.close(); enc.wait()
print('frames',N)
