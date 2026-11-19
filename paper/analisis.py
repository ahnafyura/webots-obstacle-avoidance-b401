import os
REPO=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import sys, json, math
sys.path.insert(0,REPO+'/controllers/humanoid_avoidance')
import numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import gait as G
MD=REPO+'/controllers/humanoid_avoidance/motions/'
plt.rcParams.update({'font.size':8,'font.family':'serif','axes.grid':True,'grid.alpha':.3,'lines.linewidth':1.0,'figure.dpi':200})
L1,L2,HIP=0.1,0.1029,(0.05,-0.085)
VLIM={'HipYawPitch':4.16174,'HipRoll':4.16174,'HipPitch':6.40239,'KneePitch':6.40239,'AnklePitch':6.40239,'AnkleRoll':4.16174}
R={}
fw=MD+'Forwards50.motion'
joints,frames=G.load_motion(fw)
loop=G.Clip(*G.load_motion(fw,G.LOOP_START,G.LOOP_END+1))
T=loop.duration; N=len(loop.frames)-1; dt=0.04
A=np.array([v for t,v in loop.frames]); names=loop.joints
R['T_cycle']=T; R['frames']=N
R['closure_max_rad']=float(np.abs(A[0]-A[-1]).max())
leg=[n for n in names if n[0] in 'LR' and any(k in n for k in VLIM)]
# velocity/accel/jerk (finite diff, periodic)
Ap=A[:-1]
v=(np.roll(Ap,-1,0)-Ap)/dt
a=(np.roll(v,-1,0)-v)/dt
j=(np.roll(a,-1,0)-a)/dt
tab={}
for n in leg:
    i=names.index(n); key=n[1:]
    tab[n]=dict(rom=float(Ap[:,i].max()-Ap[:,i].min()),vmax=float(np.abs(v[:,i]).max()),amax=float(np.abs(a[:,i]).max()),jmax=float(np.abs(j[:,i]).max()),vlim=VLIM[key],util=float(np.abs(v[:,i]).max()/VLIM[key]))
R['joint']=tab
# Fourier harmonics (periodic, fundamental f0=1/T)
F={}
for n in ['LHipPitch','LKneePitch','LAnklePitch','LHipRoll','LAnkleRoll']:
    i=names.index(n); X=np.fft.rfft(Ap[:,i])/len(Ap); amp=2*np.abs(X); amp[0]=np.abs(X[0])
    ac=amp[1:]; 
    F[n]=dict(harm=[float(x) for x in ac[:6]],frac3=float((ac[:3]**2).sum()/(ac**2).sum()),frac5=float((ac[:5]**2).sum()/(ac**2).sum()))
R['fourier']=F; R['f0']=1/T
# servo first-order lag bound e<=tau*vmax
R['lag']={str(int(tau*1000)):{n:float(tau*tab[n]['vmax']) for n in ['LHipPitch','LKneePitch','LAnklePitch']} for tau in (0.02,0.04,0.08)}
# FK sagittal
def fk(th,thk,tha):
    p1=-th; p2=p1-thk; p3=p2-tha
    x=L1*math.sin(p1)+L2*math.sin(p2); z=-(L1*math.cos(p1)+L2*math.cos(p2))
    return x,z,p3
ready=G.READY
x0,z0,p0=fk(ready['LHipPitch'],ready['LKneePitch'],ready['LAnklePitch'])
R['ready']=dict(x=x0,z=z0,foot_angle=p0,hip_height_to_sole=-z0+0.04519)
XL=[];ZL=[];XR=[];ZR=[];PL=[];PR=[]
for row in Ap:
    d=dict(zip(names,row))
    x,z,p=fk(d['LHipPitch'],d['LKneePitch'],d['LAnklePitch']);XL.append(x);ZL.append(z);PL.append(p)
    x,z,p=fk(d['RHipPitch'],d['RKneePitch'],d['RAnklePitch']);XR.append(x);ZR.append(z);PR.append(p)
XL,ZL,XR,ZR,PL,PR=map(np.array,(XL,ZL,XR,ZR,PL,PR))
R['fk']=dict(xL_range=float(XL.max()-XL.min()),xR_range=float(XR.max()-XR.min()),zL_range=float(ZL.max()-ZL.min()),zR_range=float(ZR.max()-ZR.min()),hip_z_mean=float(-(ZL.mean())),flat_err_deg_max=float(np.degrees(np.abs(np.concatenate([PL,PR])).max())))
# stance estimate: foot lowest z (stance) => hip travel = dx of foot rel hip over frames where z within 2mm of min
def stance(X,Z):
    m=Z<=Z.min()+0.002; idx=np.where(m)[0]; return int(m.sum()), float(X[m].max()-X[m].min())
R['stance']={'L':stance(XL,ZL),'R':stance(XR,ZR)}
# blend profiles
u=np.linspace(0,1,501)
sm=u*u*(3-2*u); smv=6*u*(1-u); sma=6-12*u
q=10*u**3-15*u**4+6*u**5; qv=30*u**2-60*u**3+30*u**4; qa=60*u-180*u**2+120*u**3
R['blend']=dict(smooth_v=1.5,smooth_a=6.0,quintic_v=float(qv.max()),quintic_a=float(np.abs(qa).max()),linear_v=1.0)
# blend worst-case delta: READY -> first pose of each clip
Tb=0.4; wb={}
for name,(p) in {'Forwards50':fw,'TurnLeft40':MD+'TurnLeft40.motion','TurnRight40':MD+'TurnRight40.motion','TurnLeft180':MD+'TurnLeft180.motion','Backwards':MD+'Backwards.motion','Forwards':MD+'Forwards.motion'}.items():
    jn,fr=G.load_motion(p); first=fr[0][1]
    dm=0;jj=None
    for n,val in zip(jn,first):
        d=abs(val-ready.get(n,val))
        if d>dm: dm,jj=d,n
    key=jj[1:] if jj and jj[0] in 'LR' else jj
    wb[name]=dict(joint=jj,delta=dm,vpeak=1.5*dm/Tb,apeak=6*dm/Tb**2,vlim=VLIM.get(key,None))
R['blend_worst']=wb
# turn pulse
amp=G.TURN_AMP; Tp=13*dt
R['turn']=dict(amp=amp,rise_s=Tp,vpeak=1.5*amp/Tp,apeak=6*amp/Tp**2,util=1.5*amp/Tp/VLIM['HipYawPitch'],deg=math.degrees(amp))
json.dump(R,open('hasil.json','w'),indent=1)
# ---- figures
tt=np.array([t for t,_ in loop.frames])
fig,ax=plt.subplots(1,2,figsize=(3.45,1.9))
for n,ls in [('LHipPitch','-'),('LKneePitch','--'),('LAnklePitch',':')]:
    ax[0].plot(tt,A[:,names.index(n)],ls,color='k',label=n[1:])
ax[0].set_xlabel('t (s)');ax[0].set_ylabel('rad');ax[0].legend(fontsize=5,loc='lower left')
ax[1].plot(tt[:-1],np.abs(v[:,names.index('LKneePitch')]),'k');ax[1].axhline(6.40239,color='gray',ls='--');ax[1].set_xlabel('t (s)');ax[1].set_ylabel('|velocity| rad/s');ax[1].text(0.05,6.0,'URDF limit',fontsize=5,va='top')
plt.tight_layout();plt.savefig('fig/f_siklus.pdf');plt.close()
fig,ax=plt.subplots(1,3,figsize=(3.45,1.5))
for k,(y1,y2,y3,t) in enumerate([(u,sm,q,'position'),(np.ones_like(u),smv,qv,'velocity'),(np.zeros_like(u),sma,qa,'acceleration')]):
    ax[k].plot(u,y1,color='gray',ls=':',label='lin');ax[k].plot(u,y2,'k',label='smoothstep');ax[k].plot(u,y3,'k--',label='quintic');ax[k].set_title(t,fontsize=6);ax[k].set_xlabel('u')
ax[0].legend(fontsize=4.5);plt.tight_layout();plt.savefig('fig/f_blend.pdf');plt.close()
fig,ax=plt.subplots(figsize=(3.45,1.7))
w=0.25
for k,n in enumerate(['LHipPitch','LKneePitch','LAnklePitch']):
    ax.bar(np.arange(1,7)+(k-1)*w,F[n]['harm'],w,color=['k','gray','lightgray'][k],edgecolor='k',label=n[1:])
ax.set_xlabel('harmonic k (f = k/%.2f Hz)'%T);ax.set_ylabel('amplitude (rad)');ax.set_yscale('log');ax.legend(fontsize=5)
plt.tight_layout();plt.savefig('fig/f_fourier.pdf');plt.close()
fig,ax=plt.subplots(figsize=(3.45,1.7))
ax.plot(tt[:-1],XL*1000,'k',label='left foot x');ax.plot(tt[:-1],XR*1000,'k--',label='right foot x')
ax.set_xlabel('t (s)');ax.set_ylabel('x rel. hip (mm)');ax.legend(fontsize=5)
plt.tight_layout();plt.savefig('fig/f_fk.pdf');plt.close()
print(json.dumps({k:R[k] for k in ['T_cycle','closure_max_rad','ready','fk','stance','blend','blend_worst','turn','lag']},indent=1))
print({n:(round(tab[n]['vmax'],2),round(tab[n]['util'],2),round(tab[n]['amax'],1),round(tab[n]['rom'],2)) for n in tab})
print({n:(round(F[n]['frac3'],4),round(F[n]['frac5'],4),[round(x,3) for x in F[n]['harm'][:4]]) for n in F})
