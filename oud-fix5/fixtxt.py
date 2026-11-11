import cv2,numpy as np,sys
from PIL import Image,ImageDraw,ImageFont
s=cv2.imread('still.png'); S=s.astype(np.float32)
x0,y0,x1,y1=838,1606,962,1652
R=S[y0:y1,x0:x1]; bg=cv2.medianBlur(s[y0-30:y1+30,x0-30:x1+30],21)[30:-30,30:-30].astype(np.float32)
d=(R-bg).mean(2); txt=d>14
mask=np.zeros(s.shape[:2],np.uint8); mask[y0:y1,x0:x1][txt]=255; mask=cv2.dilate(mask,np.ones((5,5),np.uint8))
er=cv2.inpaint(s,mask,6,cv2.INPAINT_TELEA).astype(np.float32)
tex=S[y0:y1,x0-130:x1-130]-cv2.GaussianBlur(S[y0:y1,x0-130:x1-130],(0,0),3)
mk=cv2.GaussianBlur(mask[y0:y1,x0:x1].astype(np.float32)/255,(0,0),1.5)[...,None]
er[y0:y1,x0:x1]+=tex*mk
cv2.imwrite('erased.png',np.clip(er,0,255).astype(np.uint8))
def render(font,size=240,text='فخامة سمو'):
    f=ImageFont.truetype(font,size); im=Image.new('L',(2400,700),0); dr=ImageDraw.Draw(im)
    dr.text((150,150),text,font=f,fill=255,direction='rtl',language='ar')
    a=np.array(im); ys,xs=np.where(a>0); return a[ys.min():ys.max()+1,xs.min():xs.max()+1]
outs=[]
for font,name,tw in [('Almarai-Regular.ttf','alr',118),('Almarai-Bold.ttf','alb',118),('Tajawal-Medium.ttf','taj',112)]:
    a=render(font); sc=tw/a.shape[1]; a=cv2.resize(a.astype(np.float32)/255,None,fx=sc,fy=sc,interpolation=cv2.INTER_AREA)
    h,w=a.shape; print(name,w,h)
    out=er.copy(); cx,cy=899.5,1630
    ax,ay=int(round(cx-w/2)),int(round(cy-h/2))
    a=cv2.GaussianBlur(a,(0,0),0.45)
    g=np.linspace(1.12,0.86,h)[:,None,None]*np.array([64,113,170],np.float32)[None,None]
    out[ay:ay+h,ax:ax+w]=out[ay:ay+h,ax:ax+w]*(1-a[...,None])+g*a[...,None]
    o=np.clip(out,0,255).astype(np.uint8); cv2.imwrite(f'fixed_{name}.png',o)
    outs.append(cv2.resize(o[1480:1700,640:1060],None,fx=2.5,fy=2.5,interpolation=cv2.INTER_CUBIC))
outs.insert(0,cv2.resize(s[1480:1700,640:1060],None,fx=2.5,fy=2.5,interpolation=cv2.INTER_CUBIC))
cv2.imwrite('zoom_all.jpg',np.vstack(outs))
