import cv2, numpy as np
H,W=1920,1080
yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
rng=np.random.RandomState(7)
DUST=rng.rand(70,4)   # x,y,phase,size
def ss(x): x=np.clip(x,0,1); return x*x*(3-2*x)
def sun(img,tt,zs,TT):
    """soft warm sun shaft from the upper-left that drifts slowly across part of the scene and fades."""
    env=float(ss((tt-1.0)/1.8)*ss((TT-0.6-tt)/2.2))
    if env<=0.002: return img
    # scene coordinates (undo the camera zoom so the light belongs to the scene)
    X=470+(xx-470)/zs; Y=1150+(yy-1150)/zs
    S=np.array([-420.,-150.])
    v=ss(tt/TT)                                   # slow drift of where the beam lands
    T=np.array([330+520*v, 1030+90*v])
    d=T-S; L=np.linalg.norm(d); d/=L; n=np.array([-d[1],d[0]])
    along=(X-S[0])*d[0]+(Y-S[1])*d[1]; perp=(X-S[0])*n[0]+(Y-S[1])*n[1]
    w=60+0.16*np.maximum(along,0)
    beam=np.exp(-(perp/w)**2*1.6)
    ang=perp/np.maximum(along,1)
    streak=0.7+0.3*(0.5*np.sin(ang*95+tt*0.35)+0.5*np.sin(ang*41-tt*0.22+1.3))
    beam=beam*streak*ss((along-250)/700)
    beam=cv2.GaussianBlur(beam,(0,0),6)
    warm=np.array([0.55,0.82,1.0],np.float32)
    # light falling on surfaces: lifts what it touches (stronger on lit objects than on the black background)
    lum=cv2.cvtColor(np.clip(img,0,255).astype(np.uint8),cv2.COLOR_BGR2GRAY).astype(np.float32)/255
    surf=beam*(0.25+0.75*ss(lum*2.2))
    img=img*(1+(surf*0.75*env)[...,None]*warm)
    # light in the air (haze) - screen blend
    haze=(beam*0.16*env)[...,None]*warm
    img=255-(255-img)*(1-haze)
    # a few slow dust specks floating inside the shaft
    sp=np.zeros((H,W),np.float32)
    for px,py,ph,sz in DUST:
        x=60+px*900+18*np.sin(tt*0.4+ph*6); y=250+py*1200-tt*9+12*np.cos(tt*0.3+ph*5)
        sx=470+zs*(x-470); sy=1150+zs*(y-1150)
        bx,by=int(min(max(sx,0),W-1)),int(min(max(sy,0),H-1))
        a=beam[by,bx]*(0.5+0.5*np.sin(tt*1.3+ph*9))
        if a>0.05: cv2.circle(sp,(int(sx),int(sy)),int(1+2*sz),float(a),-1,cv2.LINE_AA)
    sp=cv2.GaussianBlur(sp,(0,0),1.3)
    img=img+(sp*110*env)[...,None]*warm
    return img
