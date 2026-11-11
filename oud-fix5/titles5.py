import numpy as np, cv2, subprocess, sys, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
FD='/tmp/claude-0/-home-user-canva21/d92bd60e-9f87-52c3-ac35-11b21dbe0949/scratchpad/fonts/fontsource-almarai-5.3.0/package/files/'
def FA(sz): return ImageFont.truetype('/home/user/canva21/oud-fix5/fonts/Almarai-ExtraBold.ttf',sz,layout_engine=ImageFont.Layout.RAQM)
def FL(sz): return ImageFont.truetype(FD+'almarai-latin-800-normal.woff',sz,layout_engine=ImageFont.Layout.RAQM)
F1=FA(80); F2=FA(84)
W,H,FPS=1080,1920,30
TD='/tmp/claude-0/-home-user-canva21/d92bd60e-9f87-52c3-ac35-11b21dbe0949/scratchpad/titles/'
RV='/home/user/canva21/oud-fix5/cards/'
SRC=sys.argv[1]; OUT=sys.argv[2]; AUDIO=sys.argv[3]
WHITE_T=(250,247,240); WHITE_B=(232,226,214)
GOLD_T=(246,222,168); GOLD_B=(206,160,92)
LAY={'top3':(300,420,540),'top':(335,447),'bot':(1490,1608),'s9':(205,313),'one':(335,None),'g1':(335,335),'big':(345,345),'mid':(860,972)}
G=[ # ad 5 (Beethoven majlis) -- line on-times measured on the delivered ad 5, shifted -0.55 s after 14.40 (silence cut)
 (0.23,2.55,'top',[('وش',0.23),('يقول',0.31),('اللي',0.39),('جرّب',0.47)],[('التايقر',1.17),('من',1.27),('بيتهوفن؟',1.35)]),
 (6.50,8.85,'top',[('والحين،',6.57)],[('جا',7.37),('دورك',7.45),('تجرّبه',7.53)]),
 (9.20,12.50,'top3',[('اطلب',9.20),('ثلاث',9.30),('أوقيّات',9.40)],[('من',10.53),('عود',10.61),('التايقر',10.69),('الفيتنامي',10.77)],[('درجة',11.90),('أولى',12.00)]),
 (12.93,14.36,'top',[('وخذ',12.93),('ثلاث',13.03),('أوقيّات',13.13)],[('هدية',13.87)]),
 (14.78,16.85,'top',[('ومع',14.78),('العرض،',14.88)],[('مبخرة',15.92),('خشبية',16.02)]),
 (17.22,18.32,'one',[('وأعواد',17.22),('موروكي',17.32)],[]),
 (18.58,19.75,'one',[('وهدية',18.58),('سرّية',18.68)],[]),
 (20.05,22.52,'top',[('وكلها',20.05),('تجيك',20.12),('في',20.20)],[('كيس',21.05),('بيتهوفن',21.12),('الفاخر',21.20)]),
 (22.92,24.02,'one',[('والشحن',22.92),('مجانًا',23.02)],[]),
 (24.38,27.25,'top',[('والدفع',24.38),('متوفر',24.48)],[('عن',25.08),('طريق',25.15),('تابي',25.25),('وتمارا',25.35)]),
 (27.35,99,'top',[('والعرض',27.35),('ما',27.45),('راح',27.50),('يطوّل...',27.58)],[('الحقه',28.82),('واطلب',28.92),('الحين',29.02)]),
]
GIFT_T=999; GIFT_END=999
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
for gg in G:
    st,en,lay,l1,l2=gg[:5]; l3=gg[5] if len(gg)>5 else []
    c1,c2=LAY[lay][:2]; c3=LAY[lay][2] if len(LAY[lay])>2 else None
    items=[]; widths=[]
    for words,font,cy,ct,cb in ((l1,F1,c1,WHITE_T,WHITE_B),(l2,(FA(118) if lay=='big' else F2),c2,GOLD_T,GOLD_B),(l3,F2,c3,GOLD_T,GOLD_B)):
        if not words: continue
        lo,tot,font=layout(words,font,cy); widths.append(tot)
        for w,t,xl,by in lo:
            im,(ox,oy)=grad_text(w,font,ct,cb); items.append((t,im,int(round(xl-ox+ (ox- (ox))) ),int(round(by-oy)),ox))
    top=c1-55; bot=(c3 if c3 else (c2 if c2 else c1))+55
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
TABBY=cv2.resize(load_rgba(TD+'logo_tabby.png'),(372,145),interpolation=cv2.INTER_AREA); TAMARA=cv2.resize(load_rgba(TD+'logo_tamara.png'),(372,146),interpolation=cv2.INTER_AREA)
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
    la=cv2.imread(TD+'beet_alpha.png',0).astype(np.float32)/255; la[:30,:120]=0; la=np.clip((la-0.12)/0.5,0,1); la=cv2.dilate(la,np.ones((3,3),np.uint8))
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

# ---- review cards (real customer screenshots, taken sharp from the delivered ad), one at a time above the box
def card_rgba(p,scale=1.28):
    x=cv2.imread(p,cv2.IMREAD_UNCHANGED); x=cv2.cvtColor(x,cv2.COLOR_BGRA2RGBA)
    x=cv2.resize(x,None,fx=scale,fy=scale,interpolation=cv2.INTER_CUBIC)
    rgb=x[...,:3].astype(np.float32); bl=cv2.GaussianBlur(rgb,(0,0),1.2); x[...,:3]=np.clip(rgb+0.6*(rgb-bl),0,255).astype(np.uint8)
    h,w=x.shape[:2]; P=40; out=np.zeros((h+2*P,w+2*P,4),np.uint8)
    sh=np.zeros((h+2*P,w+2*P),np.float32); sh[P+10:P+h+10,P:P+w]=x[...,3]/255.; sh=cv2.GaussianBlur(sh,(0,0),14)*0.55
    out[...,3]=(sh*255).astype(np.uint8)
    o=out.astype(np.float32); a=x[...,3:].astype(np.float32)/255
    reg=o[P:P+h,P:P+w]; reg[...,:3]=reg[...,:3]*(1-a)+x[...,:3]*a; reg[...,3:]=np.maximum(reg[...,3:],a*255)
    return o.astype(np.uint8)
# pile like the delivered ad (client preferred it), cards x1.2, strong reviews first / middle / last
ORDER=['c2','c5','c1','c6','c3','c4']   # السهلي, نايف, أم مطلق, محمد (شحن), نورة, ياسر
POP0,POPDT,REV_END=2.70,0.50,6.20
def levels(im):
    out=[]
    for d in range(6):
        x=im.astype(np.float32)
        if d:
            sg=min(2.0*d,7.0); x[...,:3]=cv2.GaussianBlur(x[...,:3],(0,0),sg); x[...,3]=cv2.GaussianBlur(x[...,3],(0,0),sg*0.6)
            L=x[...,:3].mean(2,keepdims=True); w=min(0.30*d,0.65); x[...,:3]=(x[...,:3]*(1-w)+L*0.92*w)*(1-min(0.07*d,0.30))
        out.append(x)
    return out
PILE=[]; ytop=34
for i,k in enumerate(ORDER):
    im=card_rgba(RV+k+'.png',1.20); h,w=im.shape[:2]
    x=(1080-25-(w-80)-40) if i%2==0 else (25-40)
    PILE.append(dict(lv=levels(im),t0=POP0+POPDT*i,x=int(x),y=int(ytop-40))); ytop+=0.765*(h-80)
def draw_reviews(fr,t):
    if not (POP0-0.1<=t<REV_END): return
    k=sstep((t-(POP0-0.08))/0.30)
    if k>0:   # dim + soften the background like the original
        bl=cv2.GaussianBlur(fr,(0,0),4.0); fr[:]=(fr*(1-0.6*k)+bl*0.6*k)*(1-0.42*k)
    for i,c in enumerate(PILE):
        if t<c['t0']: continue
        d=sum(sstep((t-o['t0'])/0.22) for o in PILE[i+1:])
        lo=min(int(d),5); hi=min(lo+1,5); f=d-int(d)
        im=c['lv'][lo]*(1-f)+c['lv'][hi]*f if hi!=lo else c['lv'][lo]
        q=(t-c['t0'])/0.18; a=sstep(q*1.6); s=0.62+0.38*ease_back(q)
        paste(fr,im.astype(np.uint8),c['x'],c['y'],a,s)
# ---- offer pills
def pill(text,fs=64):
    f=FA(fs); tw=f.getlength(text,direction='rtl'); bw,bh=int(tw+110),int(fs*1.75); S=3
    img=Image.new('RGBA',(bw*S,bh*S),(0,0,0,0))
    g=np.linspace(0,1,bh*S)[:,None,None]; col=np.array(GOLD_T)*(1-g)+np.array(GOLD_B)*g
    m=Image.new('L',(bw*S,bh*S),0); ImageDraw.Draw(m).rounded_rectangle((0,0,bw*S-1,bh*S-1),radius=bh*S//2,fill=255)
    img.alpha_composite(Image.fromarray(np.dstack([col*np.ones((1,bw*S,1)),np.array(m)]).astype(np.uint8),'RGBA'))
    d=ImageDraw.Draw(img); d.rounded_rectangle((3*S,3*S,bw*S-4*S,bh*S-4*S),radius=bh*S//2-3*S,outline=(255,240,205,200),width=2*S)
    f3=FA(fs*S); l,tp,r,b=f3.getbbox(text,direction='rtl')
    d.text(((bw*S-(r-l))/2-l,(bh*S-(b-tp))/2-tp),text,font=f3,fill=(58,30,14,255),direction='rtl')
    img=img.resize((bw,bh),Image.LANCZOS)
    out=Image.new('RGBA',(bw+60,bh+60),(0,0,0,0)); sh=Image.new('L',(bw+60,bh+60),0)
    ImageDraw.Draw(sh).rounded_rectangle((30,38,30+bw,38+bh),radius=bh//2,fill=150); sh=sh.filter(ImageFilter.GaussianBlur(12))
    shimg=Image.new('RGBA',(bw+60,bh+60),(0,0,0,255)); shimg.putalpha(sh); out.alpha_composite(shimg); out.alpha_composite(img,(30,30))
    return np.array(out)
PILLS=[(pill('٣ أوقيّات'),9.90,12.42),(pill('٣ + ٣ هدية'),13.87,14.36)]
def draw_pills(fr,t):
    for im,t0,t1 in PILLS:
        if not (t0<=t<=t1): continue
        k=(t-t0)/0.40; a=sstep(k*2.2)*(1-sstep((t-(t1-0.15))/0.15)); s=0.35+0.65*ease_back(k)
        h,w=im.shape[:2]; paste(fr,im,int(W/2-w/2),1500-h//2,a,s)
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
        if gi==6:
            k=(t-18.66)/0.42; s_=0.25+0.75*ease_back(k); a=sstep(k*2.2)*ga
            if k>0: gh,gw=GIFT.shape[:2]; paste(fr,GIFT,int(W/2-gw/2),505-gh//2,a,s_*0.80)
        if gi==9:
            for lg,lt,(lx,ly) in ((TABBY,25.85,(560,488)),(TAMARA,26.15,(148,488))):
                if t>=lt:
                    k=(t-lt)/0.4; paste(fr,lg,lx,ly,sstep(k*2.2)*ga,0.3+0.7*ease_back(k))
    draw_reviews(fr,t); draw_pills(fr,t)
    enc.stdin.write(np.clip(fr,0,255).astype(np.uint8).tobytes()); n+=1
enc.stdin.close(); enc.wait(); print('frames',n)
