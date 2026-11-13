import sys,numpy as np
# rim quad "BL BR FR FL" -> quad lowered toward the box floor: front corners down kf*L, back corners down kb*L (L = front edge length)
q=np.array([[float(v) for v in p.split(',')] for p in sys.argv[1].split()]); kf,kb=float(sys.argv[2]),float(sys.argv[3])
L=np.linalg.norm(q[2]-q[3]); d=np.array([kb,kb,kf,kf])*L
q[:,1]+=d; print(' '.join(f'{x:.0f},{y:.0f}' for x,y in q))
