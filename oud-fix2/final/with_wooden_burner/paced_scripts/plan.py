import json
# (insert at time, extra seconds) - sentence boundaries in the voice; small breath inside long sentences
INS=[(5.45,0.35),(7.76,0.35),(9.16,0.30),(11.40,0.35),(13.32,0.35),(15.26,0.30),(16.95,0.35),(18.44,0.20),(19.92,0.40),(21.19,0.30),(23.31,0.30),(24.68,0.35),(27.02,0.20)]
def f(t,side='after'):
    s=0
    for ti,d in INS:
        if ti<t or (side=='after' and ti==t): s+=d
    return t+s
cuts=[0,98,166,234,600,741,855]
new=[round(f(c/30,'before' if 0<c<855 else 'after')*30) for c in cuts]
new[-1]=round(f(28.5)*30)
print('total s',f(28.5),'new cuts',new,'lens',[new[i+1]-new[i] for i in range(6)],'old',[cuts[i+1]-cuts[i] for i in range(6)])
json.dump({'INS':INS,'cuts':new},open('pz/plan.json','w'))
