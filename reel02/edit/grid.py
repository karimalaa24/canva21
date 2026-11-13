import sys,cv2
# grid.py img x0 y0 x1 y1 out [step]  -> crop with labelled grid in full-image coordinates
im=cv2.imread(sys.argv[1]); x0,y0,x1,y1=map(int,sys.argv[2:6]); st=int(sys.argv[7]) if len(sys.argv)>7 else 50
c=im[y0:y1,x0:x1].copy(); s=1000/max(c.shape[:2]); c=cv2.resize(c,None,fx=s,fy=s)
for x in range((x0//st+1)*st,x1,st):
    X=int((x-x0)*s); cv2.line(c,(X,0),(X,c.shape[0]),(0,255,255) if x%100==0 else (0,140,255),1)
    if x%100==0: cv2.putText(c,str(x),(X+2,12),0,0.4,(0,255,255),1)
for y in range((y0//st+1)*st,y1,st):
    Y=int((y-y0)*s); cv2.line(c,(0,Y),(c.shape[1],Y),(0,255,255) if y%100==0 else (0,140,255),1)
    if y%100==0: cv2.putText(c,str(y),(2,Y-2),0,0.4,(0,255,255),1)
cv2.imwrite(sys.argv[6],c)
