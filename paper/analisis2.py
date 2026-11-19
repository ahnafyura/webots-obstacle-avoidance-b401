import os
REPO=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import sys, json, math
sys.path.insert(0,REPO+'/controllers/humanoid_avoidance')
import numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
import gait as G
plt.rcParams.update({'font.size':8,'font.family':'serif','axes.grid':True,'grid.alpha':.3,'lines.linewidth':1.0})
MD=REPO+'/controllers/humanoid_avoidance/motions/'
loop=G.Clip(*G.load_motion(MD+'Forwards50.motion',G.LOOP_START,G.LOOP_END+1))
A=np.array([v for t,v in loop.frames])[:-1]; names=loop.joints; T=loop.duration; h=0.04
out={}
# C1 defect at the cycle boundary (periodic)
v=(np.roll(A,-1,0)-A)/h
out['v_jump']={n:float(abs(v[0,names.index(n)]-v[-1,names.index(n)])) for n in ['LHipPitch','LKneePitch','LAnklePitch']}
a=(np.roll(v,-1,0)-v)/h
out['interp_err_bound_deg']={n:float(math.degrees(h*h/8*np.abs(a[:,names.index(n)]).max())) for n in ['LHipPitch','LKneePitch','LAnklePitch']}
# 2nd order critically damped closed loop: tracking error amplitude per harmonic
def err_rms(wn,zeta,i):
    X=np.fft.rfft(A[:,i])/len(A); amp=2*np.abs(X[1:]); tot=0
    for k,ak in enumerate(amp,1):
        w=2*math.pi*k/T; s=1j*w
        H=wn**2/(s**2+2*zeta*wn*s+wn**2); tot+=0.5*(abs(1-H)*ak)**2
    return math.sqrt(tot)
out['err_rms_deg']={}
for wn in (10,20,40,80):
    out['err_rms_deg'][wn]={n:float(math.degrees(err_rms(wn,1.0,names.index(n)))) for n in ['LHipPitch','LKneePitch','LAnklePitch']}
# ideal servo with rate limit (6.40 rad/s) sampled at 20 ms, command = gait.at(t)
dtc=0.02; vl=6.40239
res={}
for n in ['LKneePitch','RKneePitch','LHipPitch']:
    i=names.index(n); th=loop.at(0.0)[i]; devmax=0; tt=np.arange(0,2*T,dtc)
    for t in tt:
        c=loop.at(t%T)[i]; step=np.clip(c-th,-vl*dtc,vl*dtc); th+=step; devmax=max(devmax,abs(c-th))
    res[n]=float(math.degrees(devmax))
out['ratelimit_dev_deg']=res
# stress totals
S=json.load(open(REPO+'/docs/stress_results.json'))
tot=dict(runs=0,t=0.0,col=0,fall=0,dist=0.0)
for mode,d in S.items():
    if not isinstance(d,dict) or 'runs' not in d: continue
    for r in d['runs']:
        tot['runs']+=1;tot['t']+=r['waktu_s'];tot['col']+=r['tabrakan'];tot['fall']+=r['jatuh'];tot['dist']+=r['jarak_tempuh_m']
out['stress']=tot; out['stress_modes']=list(S.keys())
# servo figure: error vs wn
fig,ax=plt.subplots(figsize=(3.45,1.7))
w=np.logspace(0.8,2,40)
for n,ls in [('LHipPitch','-'),('LKneePitch','--'),('LAnklePitch',':')]:
    ax.semilogx(w,[math.degrees(err_rms(x,1.0,names.index(n))) for x in w],ls,color='k',label=n[1:])
ax.set_xlabel(r'servo bandwidth $\omega_n$ (rad/s)');ax.set_ylabel('RMS error (deg)');ax.legend(fontsize=5)
plt.tight_layout();plt.savefig('fig/f_servo.pdf')
json.dump(out,open('hasil2.json','w'),indent=1); print(json.dumps(out,indent=1))
