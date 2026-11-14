import sys,subprocess,os
from PIL import Image
# multigrid.py img out "x0,y0,x1,y1" ... -> stacked fine grids (step 5)
img,out=sys.argv[1],sys.argv[2]; parts=[]
for i,r in enumerate(sys.argv[3:]):
    x0,y0,x1,y1=r.split(','); t=f'/tmp/claude-0/-home-user-canva21/5eb1c6a6-e413-5964-b40d-255f9884d5dc/scratchpad/_mg{i}.jpg'
    subprocess.run(['python3',os.path.join(os.path.dirname(__file__),'grid.py'),img,x0,y0,x1,y1,t,'5'],check=True); parts.append(Image.open(t))
H=sum(p.height+6 for p in parts); s=Image.new('RGB',(1000,H),'white'); y=0
for p in parts: s.paste(p,(0,y)); y+=p.height+6
s.save(out)
