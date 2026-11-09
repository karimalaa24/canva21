set -e
cd /tmp/claude-0/-home-user-canva21/d92bd60e-9f87-52c3-ac35-11b21dbe0949/scratchpad/v2
K=/home/user/canva21/.claude/skills/product-ad-fidelity
st(){ # src ss n_old N_new out deflicker
  r=$(python3 -c "print($4/$3)")
  df=""; [ "$6" = 1 ] && df=",deflicker=size=9:mode=pm"
  ffmpeg -nostdin -v error -y -ss $2 -i $1 -an -vf "fps=30,trim=end_frame=$(($3+4)),setpts=PTS*$r,minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:vsbmc=1,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920$df" -frames:v $4 -c:v libx264 -crf 14 -preset slow -pix_fmt yuv420p $5
  echo $5 $(ffprobe -v error -count_frames -select_streams v -show_entries stream=nb_read_frames -of csv=p=0 $5)
}
st src1.mp4 0.317 98 98 pz/s1.mp4 0
st addb/tp2.mp4 0.3 68 78 pz/s2.mp4 1
st src3.mp4 0.27 68 79 pz/s3.mp4 0
st addb/tp5.mp4 0.15 141 170 pz/s5.mp4 1
st addb/tp6.mp4 0.1 114 120 pz/s6.mp4 1
ffmpeg -nostdin -v error -y -i addb/tp4.mp4 -vf "setpts=PTS*1.46,minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:vsbmc=1,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,deflicker=size=9:mode=pm" -frames:v 433 -c:v libx264 -crf 14 -preset slow -pix_fmt yuv420p pz/k4slow.mp4
rm -rf pz/kf && mkdir pz/kf && ffmpeg -nostdin -v error -i pz/k4slow.mp4 -frames:v 433 pz/kf/%04d.png && ls pz/kf | wc -l
python3 - <<'PY'
import cv2,numpy as np,glob,subprocess,os
F=sorted(glob.glob('pz/kf/*.png')); n=len(F); fps=30; hold=2.0; Z=1.22; cx,cy=470,1150; T=(n-1)/fps
os.makedirs('pz/km',exist_ok=True)
for j,f in enumerate(F):
    t=j/fps; u=0 if t<=hold else (t-hold)/(T-hold); e=u*u*(3-2*u)*0.5+u*0.5; s=1+(Z-1)*e
    M=np.float32([[s,0,cx-s*cx],[0,s,cy-s*cy]])
    cv2.imwrite(f'pz/km/{j+1:04d}.png',cv2.warpAffine(cv2.imread(f),M,(1080,1920),flags=cv2.INTER_LANCZOS4,borderMode=cv2.BORDER_REFLECT))
subprocess.run(['ffmpeg','-nostdin','-v','error','-y','-framerate','30','-i','pz/km/%04d.png','-c:v','libx264','-crf','14','-preset','slow','-pix_fmt','yuv420p','pz/s4.mp4'],check=True)
PY
bash $K/scripts/assemble.sh pz/voice_paced.m4a pz/clean.mp4 pz/s1.mp4:98:0:1:0 pz/s2.mp4:78:0:1:0 pz/s3.mp4:79:0:1:0 pz/s4.mp4:433:0:1:0 pz/s5.mp4:170:0:1:0 pz/s6.mp4:120:0:1:0
python3 - <<'PY'
import cv2,numpy as np,json,subprocess
B=[np.float32(p) for p in json.load(open('boxes6.json'))]; W,H=1080,1920
dec=subprocess.Popen(['ffmpeg','-nostdin','-v','error','-ss','28.6','-i','pz/clean.mp4','-frames:v','120','-f','rawvideo','-pix_fmt','bgr24','-'],stdout=subprocess.PIPE)
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
json.dump(tracks,open('pz/box_tracks.json','w')); print('tracks',len(tracks[0]))
PY
python3 pz/fx.py
python3 pz/cap2.py pz/clean_fx.mp4 pz/final.mp4
echo ALLDONE
