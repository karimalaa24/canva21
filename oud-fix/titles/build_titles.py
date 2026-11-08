import numpy as np, cv2, subprocess, sys, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
FD='/tmp/claude-0/-home-user-canva21/d92bd60e-9f87-52c3-ac35-11b21dbe0949/scratchpad/fonts/fontsource-almarai-5.3.0/package/files/'
def FA(sz): return ImageFont.truetype(FD+'almarai-arabic-800-normal.woff',sz,layout_engine=ImageFont.Layout.RAQM)
def FL(sz): return ImageFont.truetype(FD+'almarai-latin-800-normal.woff',sz,layout_engine=ImageFont.Layout.RAQM)
F1=FA(80); F2=FA(84)
W,H,FPS=1080,1920,30
SRC=sys.argv[1]; OUT=sys.argv[2]; AUDIO=sys.argv[3]
WHITE_T=(250,247,240); WHITE_B=(232,226,214)
GOLD_T=(246,222,168); GOLD_B=(206,160,92)
LAY={'top':(335,447),'bot':(1490,1608),'s9':(205,313),'one':(335,None)}
G=[ # start,end,layout,[line1 words],[line2 words]
 (0.45,1.85,'top',[('هذي',0.45),('مو',0.52),('قطعة',0.60)],[('عود',1.0),('عادية...',1.4)]),
 (2.0,4.4,'top',[('تايقر',2.0),('فيتنامي',2.8)],[('درجة',3.6),('أولى',4.0)]),
 (4.55,6.3,'top',[('مفرز',4.6)],[('قطعة',5.6),('قطعة',5.8)]),
 (6.4,8.1,'bot',[('تجيك',6.4),('في',7.2)],[('علبة',7.4),('جلدية',7.8)]),
 (8.2,11.1,'bot',[('تحفظها',8.2),('مثل',9.4)],[('ما',9.8),('تحفظ',10.0),('ساعتك',10.4)]),
 (11.2,12.7,'one',[('والعرض',11.2),('جبار!',12.0)],[]),
 (12.8,14.95,'top',[('الحين',12.8),('اطلب',13.6)],[('٣',14.0),('أوقيات',14.4)]),
 (15.1,17.6,'top',[('يجيك',15.1),('٣',16.0),('أوقيات',16.2)],[('مجاناً',16.8)]),
 (17.8,20.83,'bot',[('وفوقهم',17.8),('بيجيك',18.8)],[('هدية',19.2),('سرية',19.6),('وقت',20.0),('الطلب',20.4)]),
 (21.0,22.77,'bot',[('والشحن',21.0)],[('مجاناً',21.8)]),
 (22.85,99,'s9',[('ومتوفر',22.85),('الدفع',23.6)],[('عن',24.0),('طريق',24.2),('تابي',24.6),('وتمارا',24.8)]),
]
GIFT_T=19.62; GIFT_END=20.83
PUN='!.…'
def split_p(word):
    core=word.rstrip(PUN); return core,word[len(core):]
def wlen(word,font):
    core,p=split_p(word); fl=FL(font.size)
    return font.getlength(core,direction='rtl')+(fl.getlength(p)+font.size*0.04 if p else 0)
def grad_text(word,font,ct,cb):
    core,p=split_p(word); fl=FL(font.size)
    l,t,r,b=font.getbbox(core,direction='rtl',anchor='ls'); pad=24
    pw=(fl.getlength(p)+font.size*0.04) if p else 0
    w,h=int(r-l+pw)+2*pad,b-t+2*pad
    mask=Image.new('L',(w,h),0); dd=ImageDraw.Draw(mask)
    dd.text((pad-l+pw,pad-t),core,font=font,fill=255,direction='rtl',anchor='ls')
    if p: dd.text((pad,pad-t),p,font=fl,fill=255,anchor='ls')
    l=l-pw
    g=np.linspace(0,1,h)[:,None,None]; col=(np.array(ct)*(1-g)+np.array(cb)*g)*np.ones((h,w,1))
    rgba=np.dstack([col,np.array(mask)]).astype(np.uint8); img=Image.fromarray(rgba,'RGBA')
    sh=Image.new('RGBA',(w,h),(0,0,0,0)); sa=mask.filter(ImageFilter.GaussianBlur(6)).point(lambda v:int(v*0.6))
    sh.putalpha(sa); base=Image.new('RGBA',(w,h),(0,0,0,0)); base.alpha_composite(sh,(0,3)); base.alpha_composite(img)
    return base,(-l+pad,-t+pad)   # offset of baseline origin inside the image
def layout(words,font,cy):
    sp=font.getlength(' ')*1.0
    ws=[wlen(w,font) for w,_ in words]; tot=sum(ws)+sp*(len(ws)-1)
    if tot>950:
        font=FA(int(font.size*950/tot)); return layout(words,font,cy)
    x=W/2+tot/2; out=[]
    asc,desc=font.getmetrics(); base=cy+ (asc-desc)/2*0.62
    for (w,t),wl in zip(words,ws):
        out.append((w,t,x-font.getlength(split_p(w)[0],direction='rtl'),base)); x-=wl+sp     # x_left, baseline y
    return out,tot,font
groups=[]
for st,en,lay,l1,l2 in G:
    c1,c2=LAY[lay]
    items=[]; widths=[]
    for words,font,cy,ct,cb in ((l1,F1,c1,WHITE_T,WHITE_B),(l2,F2,c2,GOLD_T,GOLD_B)):
        if not words: continue
        lo,tot,font=layout(words,font,cy); widths.append(tot)
        for w,t,xl,by in lo:
            im,(ox,oy)=grad_text(w,font,ct,cb); items.append((t,im,int(round(xl-ox+ (ox- (ox))) ),int(round(by-oy)),ox))
    top=c1-55; bot=(c2 if c2 else c1)+55
    groups.append(dict(st=st,en=en,items=items,top=top,bot=bot,wmax=max(widths)))
# backdrop & divider assets
def backdrop(g):
    h=g['bot']-g['top']+160; w=min(1080,int(g['wmax']+340))
    m=Image.new('L',(w,h),0); ImageDraw.Draw(m).rounded_rectangle((100,60,w-100,h-60),radius=60,fill=255)
    m=m.filter(ImageFilter.GaussianBlur(45)); a=np.array(m).astype(np.float32)*0.50
    return np.dstack([np.zeros((h,w,3)),a]).astype(np.uint8),(int(W/2-w/2),g['top']-80)
for g in groups: g['bd']=backdrop(g)
def divider():
    w,h=240,5; x=np.linspace(-1,1,w); a=np.clip(1-np.abs(x)**2,0,1)
    col=np.array([150,205,235])[None,None,::-1]*np.ones((h,w,1))   # BGR->RGB later
    arr=np.zeros((h,w,4)); arr[...,0]=232; arr[...,1]=196; arr[...,2]=130; arr[...,3]=(a*np.array([0.4,0.9,1,0.9,0.4])[:,None])*255
    return arr.astype(np.uint8)
DIV=divider()
# logos
def load_rgba(p):
    x=cv2.imread(p,cv2.IMREAD_UNCHANGED); x=cv2.cvtColor(x,cv2.COLOR_BGRA2RGBA)
    a=x[...,3].astype(np.float32); a=cv2.erode(a,np.ones((5,5),np.uint8)); x[...,3]=cv2.GaussianBlur(a,(3,3),0).astype(np.uint8); return x
TABBY=load_rgba('logo_tabby.png'); TAMARA=load_rgba('logo_tamara.png')
# gift badge
def gift_badge():
    bw,bh=470,165; S=3
    img=Image.new('RGBA',(bw*S,bh*S),(0,0,0,0)); d=ImageDraw.Draw(img)
    g=np.linspace(0,1,bh*S)[:,None]
    top=np.array([128,26,42]); bot=np.array([66,10,20])
    col=(top[None,None,:]*(1-g[:,:,None])+bot[None,None,:]*g[:,:,None])*np.ones((1,bw*S,1))
    m=Image.new('L',(bw*S,bh*S),0); ImageDraw.Draw(m).rounded_rectangle((0,0,bw*S-1,bh*S-1),radius=26*S,fill=255)
    card=Image.fromarray(np.dstack([col,np.array(m)]).astype(np.uint8),'RGBA'); img.alpha_composite(card)
    d=ImageDraw.Draw(img); d.rounded_rectangle((3*S,3*S,bw*S-4*S,bh*S-4*S),radius=23*S,outline=(226,188,118,255),width=3*S)
    # gift icon (left)
    gx,gy,gw=44*S,34*S,96*S; gold=(232,196,126,255); gold2=(196,150,78,255)
    d.rounded_rectangle((gx,gy+30*S,gx+gw,gy+gw),radius=6*S,fill=gold2)              # box body
    d.rounded_rectangle((gx-6*S,gy+16*S,gx+gw+6*S,gy+38*S),radius=6*S,fill=gold)      # lid
    d.rectangle((gx+gw/2-8*S,gy+16*S,gx+gw/2+8*S,gy+gw),fill=(128,26,42,255))         # ribbon
    d.ellipse((gx+gw/2-36*S,gy-6*S,gx+gw/2-2*S,gy+20*S),outline=gold,width=8*S)       # bow L
    d.ellipse((gx+gw/2+2*S,gy-6*S,gx+gw/2+36*S,gy+20*S),outline=gold,width=8*S)       # bow R
    d.ellipse((gx+gw/2-9*S,gy+4*S,gx+gw/2+9*S,gy+22*S),fill=gold)
    # separator
    d.line((168*S,28*S,168*S,bh*S-28*S),fill=(226,188,118,150),width=2*S)
    # Beethoven logo (right)
    la=cv2.imread('beet_alpha.png',0).astype(np.float32)/255; la[:30,:120]=0; la=np.clip((la-0.12)/0.5,0,1); la=cv2.dilate(la,np.ones((3,3),np.uint8))
    th=int(138*S); tw=int(la.shape[1]*th/la.shape[0]); la=cv2.resize(la,(tw,th),interpolation=cv2.INTER_AREA)
    gg=np.linspace(0,1,th)[:,None,None]; lc=np.array([246,222,168])*(1-gg)+np.array([212,168,98])*gg
    logo=Image.fromarray(np.dstack([lc*np.ones((th,tw,1)),la*255]).astype(np.uint8),'RGBA')
    img.alpha_composite(logo,(int(168*S+(bw*S-168*S-tw)/2),int((bh*S-th)/2)))
    img=img.resize((bw,bh),Image.LANCZOS)
    out=Image.new('RGBA',(bw+60,bh+60),(0,0,0,0)); sh=Image.new('L',(bw+60,bh+60),0)
    ImageDraw.Draw(sh).rounded_rectangle((30,36,30+bw,36+bh),radius=26,fill=150); sh=sh.filter(ImageFilter.GaussianBlur(12))
    shimg=Image.new('RGBA',(bw+60,bh+60),(0,0,0,255)); shimg.putalpha(sh); out.alpha_composite(shimg); out.alpha_composite(img,(30,30))
    return np.array(out)
GIFT=gift_badge(); Image.fromarray(GIFT).save('gift_badge.png')
def ease_back(t):
    c1=1.70158; c3=c1+1; t=min(max(t,0),1); return 1+c3*(t-1)**3+c1*(t-1)**2
def sstep(t): t=min(max(t,0),1); return t*t*(3-2*t)
def paste(canvas,rgba,x,y,alpha=1.0,scale=1.0):
    if alpha<=0.003: return
    im=rgba
    if abs(scale-1)>1e-3:
        h,w=im.shape[:2]; nw,nh=max(1,int(w*scale)),max(1,int(h*scale)); im=cv2.resize(im,(nw,nh),interpolation=cv2.INTER_LINEAR)
        x=int(round(x+(w-nw)/2)); y=int(round(y+(h-nh)/2))
    h,w=im.shape[:2]; x0,y0=max(0,x),max(0,y); x1,y1=min(W,x+w),min(H,y+h)
    if x1<=x0 or y1<=y0: return
    s=im[y0-y:y1-y,x0-x:x1-x].astype(np.float32); a=s[...,3:]/255.*alpha
    canvas[y0:y1,x0:x1]=canvas[y0:y1,x0:x1]*(1-a)+s[...,:3]*a
items_np=[[(t,np.array(im),x,y) for t,im,x,y,_ in g['items']] for g in groups]
dec=subprocess.Popen(['ffmpeg','-nostdin','-v','error','-i',SRC,'-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
enc=subprocess.Popen(['ffmpeg','-nostdin','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r','30','-i','-','-i',AUDIO,'-map','0:v','-map','1:a','-c:v','libx264','-crf','15','-preset','slow','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-shortest','-movflags','+faststart',OUT],stdin=subprocess.PIPE)
n=0
while True:
    buf=dec.stdout.read(W*H*3)
    if len(buf)<W*H*3: break
    fr=np.frombuffer(buf,np.uint8).reshape(H,W,3).astype(np.float32); t=n/FPS
    for gi,g in enumerate(groups):
        if not (g['st']-0.05<=t<=g['en']): continue
        ga=sstep((t-g['st'])/0.25)*(1-sstep((t-(g['en']-0.18))/0.18)) if g['en']<90 else sstep((t-g['st'])/0.25)
        bd,(bx,by)=g['bd']; paste(fr,bd,bx,by,ga)
        dv=sstep((t-g['st'])/0.35); dw=max(2,int(DIV.shape[1]*dv)); d=cv2.resize(DIV,(dw,DIV.shape[0])); paste(fr,d,int(W/2-dw/2),g['top']-18,ga)
        for (wt,im,x,y) in items_np[gi]:
            a=sstep((t-wt)/0.22)
            if a<=0: continue
            paste(fr,im,x,int(y+(1-a)*16),a*ga)
        if gi==8 and t>=GIFT_T:
            k=(t-GIFT_T)/0.42; s=0.25+0.75*ease_back(k); a=sstep(k*2.2)*ga
            gh,gw=GIFT.shape[:2]; paste(fr,GIFT,int(W/2-gw/2),1668,a,s)
        if gi==10:
            for lg,lt,(lx,ly) in ((TABBY,24.6,(184,378)),(TAMARA,24.8,(557,377))):
                if t>=lt:
                    k=(t-lt)/0.4; paste(fr,lg,lx,ly,sstep(k*2.2),0.3+0.7*ease_back(k))
    enc.stdin.write(np.clip(fr,0,255).astype(np.uint8).tobytes()); n+=1
enc.stdin.close(); enc.wait(); print('frames',n)
