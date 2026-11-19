import os
REPO=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import sys, json, math
sys.path.insert(0,REPO+'/controllers/humanoid_avoidance')
import numpy as np
from scipy.optimize import brentq
import gait as G
MD=REPO+'/controllers/humanoid_avoidance/motions/'
import xml.etree.ElementTree as ET
U=ET.parse(REPO+'/rviz/humanoid_b401.urdf').getroot()
LIM={j.get('name'):{k:float(v) for k,v in j.find('limit').attrib.items()} for j in U.findall('joint') if j.get('type')=='revolute'}
loop=G.Clip(*G.load_motion(MD+'Forwards50.motion',G.LOOP_START,G.LOOP_END+1)); names=loop.joints; T=loop.duration; h=0.04
A=np.array([v for t,v in loop.frames])[:-1]
R={}
# 1 speed-up bound
v=(np.roll(A,-1,0)-A)/h
util={n:float(np.abs(v[:,i]).max()/LIM[n]['velocity']) for i,n in enumerate(names) if np.abs(v[:,i]).max()>0}
R['util']=util; R['vui_max']=max(util.values()); R['lambda_max']=1/max(util.values()); R['argmax']=max(util,key=util.get)
# 2 minimal synchronized blend time (velocity limited smoothstep): T*=max 3|D|/(2 vbar)
ready=G.READY
def tstar(frm,to):
    best=0;arg=None
    for n in G.JOINTS:
        d=abs(to.get(n,frm[n])-frm[n]); t=1.5*d/LIM[n]['velocity']
        if t>best: best,arg=t,n
    return best,arg
zero={n:0.0 for n in G.JOINTS}
trans={}
trans['stand to ready']=(*tstar(zero,ready),1.2)
for nm,f in [('ready to walk start','Forwards50'),('ready to turn left 40','TurnLeft40'),('ready to turn around','TurnLeft180'),('ready to backward','Backwards'),('ready to small forward','Forwards')]:
    jn,fr=G.load_motion(MD+f+'.motion'); first=dict(zip(jn,fr[0][1])); to=dict(ready); to.update(first)
    trans[nm]=(*tstar(ready,to),0.4)
R['blend']={k:dict(T_star=a,joint=b,T_used=c,slack=c/a if a>0 else None) for k,(a,b,c) in trans.items()}
# 3 bandwidth budget
def err_rms(wn,i,zeta=1.0):
    X=np.fft.rfft(A[:,i])/len(A); amp=2*np.abs(X[1:]); tot=0
    for k,ak in enumerate(amp,1):
        s=1j*2*math.pi*k/T; H=wn**2/(s**2+2*zeta*wn*s+wn**2); tot+=0.5*(abs(1-H)*ak)**2
    return math.sqrt(tot)
bw={}
for n in ['LHipPitch','LKneePitch','LAnklePitch','LHipRoll','LAnkleRoll']:
    i=names.index(n); qd=v[:,i]; qrms=float(np.sqrt((qd**2).mean()))
    row={'qdot_rms':qrms}
    for eps in (1,2,3,5):
        e=math.radians(eps); exact=brentq(lambda w:err_rms(w,i)-e,1.0,2000); row[eps]=dict(exact=exact,approx=2*qrms/e)
    bw[n]=row
R['bw']=bw
R['fs']=2/T
json.dump(R,open('hasil3.json','w'),indent=1); print(json.dumps(R,indent=1))
