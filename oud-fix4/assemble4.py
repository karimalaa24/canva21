import cv2,numpy as np,subprocess
C=[0,89,238,386,562,651,719,805,947,1128]; W,H=1080,1920; D=4   # half dissolve (frames); cut 1->2 is hard
clips=[]
for n in range(1,10):
    p=subprocess.run(['ffmpeg','-v','error','-i',f'k/k{n}.mp4','-vf','minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:vsbmc=1,scale=1080:1920,deflicker=size=9:mode=pm','-f','rawvideo','-pix_fmt','bgr24','-'],capture_output=True,check=True)
    a=np.frombuffer(p.stdout,np.uint8).reshape(-1,H,W,3); clips.append(a); print(n,len(a),'need',C[n]-C[n-1]+2*D)
enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','bgr24','-s',f'{W}x{H}','-r','30','-i','-','-i','dl/ad4.mp4','-map','0:v','-map','1:a','-c:v','libx264','-crf','15','-preset','slow','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-shortest','-movflags','+faststart','ed/clean4.mp4'],stdin=subprocess.PIPE)
def get(i,t):  # frame of scene i at global frame t; scene i shown from C[i]-D (offset D into its clip)
    k=t-C[i]+D; a=clips[i]; return a[min(max(k,0),len(a)-1)].astype(np.float32)
for t in range(C[-1]):
    i=max(j for j in range(9) if C[j]<=t)
    f=get(i,t)
    if i+1<9 and i+1!=1 and t>=C[i+1]-D:      # dissolve into next
        a=(t-(C[i+1]-D)+1)/(2*D+1); f=f*(1-a)+get(i+1,t)*a
    if i>0 and i!=1 and t<C[i]+D:              # still finishing dissolve from previous
        a=(t-(C[i]-D)+1)/(2*D+1); f=get(i-1,t)*(1-a)+f*a
    enc.stdin.write(np.clip(f,0,255).astype(np.uint8).tobytes())
enc.stdin.close(); enc.wait(); print('done')
