"""Replace a wrong/garbled wordmark on a still with the correct one, free (no regeneration).
Source wordmark = the correct 'BeetHoven' script cut from s02 lid lining (gold on cream); or Arabic text rendered
with the full Almarai TTF. The old word is detected as pixels that differ from the local background inside the bbox,
inpainted, and the new word is composited with the target's own gold colour (sampled from the old word)."""
import cv2,numpy as np,sys,json
from PIL import Image,ImageDraw,ImageFont
IMG='/home/user/canva21/reel01/images/'
def src_word():
    s=cv2.imread(IMG+'s02_close_raw.png').astype(np.float32)
    x0,y0,x1,y1=862,1328,1084,1396; R=s[y0:y1,x0:x1]
    bg=cv2.medianBlur(cv2.imread(IMG+'s02_close_raw.png')[y0-40:y1+40,x0-40:x1+40],41)[40:-40,40:-40].astype(np.float32)
    d=(bg-R).mean(2); a=np.clip((d-6)/(np.percentile(d,99.5)-6),0,1)
    ys,xs=np.where(a>0.15); a=a[ys.min():ys.max()+1,xs.min():xs.max()+1]; return a
def ar_word(text,ttf='/home/user/canva21/oud-fix5/fonts/Almarai-ExtraBold.ttf'):
    f=ImageFont.truetype(ttf,240,layout_engine=ImageFont.Layout.RAQM); im=Image.new('L',(2400,700),0)
    ImageDraw.Draw(im).text((150,150),text,font=f,fill=255,direction='rtl'); a=np.array(im).astype(np.float32)/255
    ys,xs=np.where(a>0.05); return a[ys.min():ys.max()+1,xs.min():xs.max()+1]
def fix(img,bbox,word,width=None,angle=0.0,clip_x=None,thr=14,gold=None,erase_only=False,erase_bbox=None,cy=None):
    x0,y0,x1,y1=bbox; P=40
    pad=cv2.copyMakeBorder(img,P,P,P,P,cv2.BORDER_REFLECT); big=pad[y0:y1+2*P,x0:x1+2*P]; bg=cv2.medianBlur(big,31)[P:-P,P:-P].astype(np.float32)
    R=img[y0:y1,x0:x1].astype(np.float32); d=np.abs(R-bg).mean(2); m=(d>thr).astype(np.uint8)*255
    if gold is None:
        sel=R[d>np.percentile(d[d>thr],60)] if (d>thr).sum()>20 else R.reshape(-1,3); gold=np.median(sel,0)
    mask=np.zeros(img.shape[:2],np.uint8); mask[y0:y1,x0:x1]=cv2.dilate(m,np.ones((5,5),np.uint8))
    if erase_bbox is not None:
        ex0,ey0,ex1,ey1=erase_bbox; Re=img[ey0:ey1,ex0:ex1].astype(np.float32)
        bge=cv2.medianBlur(pad[ey0:ey1+2*P,ex0:ex1+2*P],31)[P:-P,P:-P].astype(np.float32)
        me=(np.abs(Re-bge).mean(2)>thr).astype(np.uint8)*255; mask[ey0:ey1,ex0:ex1]|=cv2.dilate(me,np.ones((5,5),np.uint8))
    out=cv2.inpaint(img,mask,7,cv2.INPAINT_TELEA).astype(np.float32)
    # restore fine texture inside the inpainted area
    tex=img.astype(np.float32)-cv2.GaussianBlur(img.astype(np.float32),(0,0),2.5); sh=np.roll(tex,(0,int((x1-x0)*1.1)),(0,1))
    mk=cv2.GaussianBlur(mask.astype(np.float32)/255,(0,0),1.2)[...,None]; out+=sh*mk*0.8
    if erase_only or word is None: return np.clip(out,0,255).astype(np.uint8),gold
    W=width or (x1-x0); a=cv2.resize(word,(int(W),int(W*word.shape[0]/word.shape[1])),interpolation=cv2.INTER_AREA)
    h,w=a.shape; cx=(x0+x1)/2; cy=cy if cy is not None else (y0+y1)/2
    M=cv2.getRotationMatrix2D((w/2,h/2),angle,1.0); M[0,2]+=cx-w/2; M[1,2]+=cy-h/2
    A=cv2.warpAffine(a,M,(img.shape[1],img.shape[0])); A=cv2.GaussianBlur(A,(0,0),0.5)
    if clip_x is not None: A[:,clip_x:]=0
    g=np.array(gold,np.float32)
    # slight vertical shading like foil
    out=out*(1-A[...,None])+g*A[...,None]
    return np.clip(out,0,255).astype(np.uint8),gold
