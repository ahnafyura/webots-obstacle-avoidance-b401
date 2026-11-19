import os
REPO=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import sys, math, json
sys.path.insert(0,REPO+'/controllers/humanoid_avoidance')
import numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import xml.etree.ElementTree as ET
import gait as G
MD=REPO+'/controllers/humanoid_avoidance/motions/'
U=ET.parse(REPO+'/rviz/humanoid_b401.urdf').getroot()
J={}
for j in U.findall('joint'):
    o=j.find('origin'); a=j.find('axis'); l=j.find('limit')
    J[j.get('name')]=dict(type=j.get('type'),parent=j.find('parent').get('link'),child=j.find('child').get('link'),xyz=np.array([float(x) for x in o.get('xyz').split()]),axis=np.array([float(x) for x in a.get('xyz').split()]) if a is not None else None,lim={k:float(v) for k,v in l.attrib.items()} if l is not None else None)
N=G.JOINTS  # order n=1..22
def rot(axis,q):
    a=axis/np.linalg.norm(axis); K=np.array([[0,-a[2],a[1]],[a[2],0,-a[0]],[-a[1],a[0],0]])
    return np.eye(3)+math.sin(q)*K+(1-math.cos(q))*K@K
def chain(side):
    return {'L':['LHipYawPitch','LHipRoll','LHipPitch','LKneePitch','LAnklePitch','LAnkleRoll'],'R':['RHipYawPitch','RHipRoll','RHipPitch','RKneePitch','RAnklePitch','RAnkleRoll']}[side]
CH=dict(Lleg=chain('L'),Rleg=chain('R'),Larm=['LShoulderPitch','LShoulderRoll','LElbowYaw','LElbowRoll'],Rarm=['RShoulderPitch','RShoulderRoll','RElbowYaw','RElbowRoll'],head=['HeadYaw','HeadPitch'])
def fk(q):
    """returns dict joint -> (origin point, rotation of joint frame after q), plus chain endpoints"""
    out={};ends={}
    for cn,js in CH.items():
        R=np.eye(3);p=np.zeros(3);pts=[p.copy()]
        for jn in js:
            p=p+R@J[jn]['xyz']; R=R@rot(J[jn]['axis'],q[jn]); out[jn]=(p.copy(),R.copy(),R@(J[jn]['axis']/np.linalg.norm(J[jn]['axis']))); pts.append(p.copy())
        if cn.endswith('leg'):
            sole=p+R@np.array([0.02,0.007,-0.041]) if cn=='Lleg' else p+R@np.array([0.02,-0.007,-0.041]); pts.append(sole)
        ends[cn]=np.array(pts)
    return out,ends
READY=dict(G.READY)
loop=G.Clip(*G.load_motion(MD+'Forwards50.motion',G.LOOP_START,G.LOOP_END+1)); lj=loop.joints
def pose(k):
    q=dict(READY); row=loop.frames[k][1]
    for n,v in zip(lj,row): q[n]=v
    return q
ROLE={'Roll':'#c0392b','Pitch':'#1e8449','Yaw':'#1f4e9c'}
def role(n): return 'Roll' if 'Roll' in n else ('Yaw' if 'Yaw' in n else 'Pitch')
plt.rcParams.update({'font.size':7,'font.family':'serif'})
def draw(ax,q,title,state=True):
    out,ends=fk(q)
    # world frame
    for v,c,l in [((0.06,0,0),'k','x'),((0,0.06,0),'k','y'),((0,0,0.06),'k','z')]:
        ax.plot([0,v[0]],[0,v[1]],[0,v[2]],color='k',lw=1.2); ax.text(v[0]*1.25,v[1]*1.25,v[2]*1.25,l,fontsize=7,fontweight='bold')
    # torso
    tx=[-0.05,0.05];ty=[-0.075,0.075];tz=[-0.085,0.13]
    for a in tx:
        for b in ty: ax.plot([a,a],[b,b],tz,color='lightgray',lw=.8)
    for c in tz:
        for a,b in [(tx[0],ty[0]),(tx[0],ty[1]),(tx[1],ty[1]),(tx[1],ty[0]),(tx[0],ty[0])]: pass
    for c in tz:
        xs=[tx[0],tx[1],tx[1],tx[0],tx[0]];ys=[ty[0],ty[0],ty[1],ty[1],ty[0]];ax.plot(xs,ys,[c]*5,color='lightgray',lw=.8)
    for cn,pts in ends.items():
        ax.plot(pts[:,0],pts[:,1],pts[:,2],color='#444',lw=2.2)
    # shoulders / hips to torso link visual
    for cn,pts in ends.items(): ax.scatter(*pts[0],color='#444',s=4)
    for jn,(p,R,ax_w) in out.items():
        n=N.index(jn)+1; c=ROLE[role(jn)]
        ax.scatter(*p,color=c,s=16,zorder=5,depthshade=False)
        ax.quiver(*p,*(ax_w*0.045),color=c,lw=1.6,arrow_length_ratio=.35)
        lab=f'{n}'
        ax.text(p[0]+0.012,p[1]+0.012,p[2]+0.008,lab,fontsize=6.5,color=c,fontweight='bold')
    ax.set_xlim(-0.12,0.18);ax.set_ylim(-0.13,0.13);ax.set_zlim(-0.27,0.18)
    ax.set_box_aspect((0.3,0.26,0.45)); ax.view_init(elev=14,azim=-52)
    ax.set_xlabel('x (m)',labelpad=-6,fontsize=6);ax.set_ylabel('y (m)',labelpad=-6,fontsize=6);ax.set_zlabel('z (m)',labelpad=-6,fontsize=6)
    ax.tick_params(labelsize=5,pad=-3);ax.set_title(title,fontsize=7,pad=-4)
import matplotlib.patches as mp
def fmt(v): 
    t=[('0' if abs(x)<1e-6 else ('%.2f'%x).rstrip('0').rstrip('.')) for x in v]; return '('+','.join(t)+')'
def chain_diagram(ax):
    ax.set_xlim(0,10);ax.set_ylim(0,len(rows_)+1.2);ax.axis('off')
    hdr=['n','joint','role','local axis','q k=0','q k=13','limit (rad)']
    xs=[0.1,0.65,3.2,4.1,6.0,7.1,8.2]
    y=len(rows_)+0.55
    for x,h in zip(xs,hdr): ax.text(x,y,h,fontsize=6,fontweight='bold',va='center')
    ax.plot([0,10],[y-0.35,y-0.35],color='k',lw=.6)
    for r,row in enumerate(rows_):
        yy=len(rows_)-r-0.1
        if row=='gap': 
            ax.plot([0,10],[yy+0.45,yy+0.45],color='lightgray',lw=.5,ls=':'); continue
        n,jn=row; c=ROLE[role(jn)]
        ax.add_patch(mp.Circle((xs[0]+0.1,yy),0.28,color=c,zorder=3));ax.text(xs[0]+0.1,yy,str(n),color='w',fontsize=5.5,ha='center',va='center',fontweight='bold',zorder=4)
        ax.text(xs[1],yy,jn,fontsize=6.2,va='center');ax.text(xs[2],yy,role(jn),fontsize=6,va='center',color=c)
        ax.text(xs[3],yy,fmt(J[jn]['axis']),fontsize=5.6,va='center')
        ax.text(xs[4],yy,'%+.2f'%READY[jn],fontsize=6,va='center');ax.text(xs[5],yy,'%+.2f'%pose(13)[jn],fontsize=6,va='center')
        L=J[jn]['lim'];ax.text(xs[6],yy,'%+.2f to %+.2f'%(L['lower'],L['upper']),fontsize=5.2,va='center')
rows_=[(N.index(j)+1,j) for j in CH['Lleg']]+['gap']+[(N.index(j)+1,j) for j in CH['Larm']]+['gap']+[(N.index(j)+1,j) for j in CH['head']]
def side_overlay(ax):
    for q,col,lw,lab in [(pose(0),'#aaaaaa',3.0,'ready (k=0)'),(pose(13),'#222',2.0,'swing peak (k=13)')]:
        out,ends=fk(q); pts=ends['Lleg']
        ax.plot(pts[:,0],pts[:,2],color=col,lw=lw,label=lab,zorder=2,solid_capstyle='round')
        if col=='#222':
            for jn,(p,R,axw) in out.items():
                if jn[0]!='L' or 'Leg' in jn: pass
            for jn in CH['Lleg']:
                p=out[jn][0];n=N.index(jn)+1;c=ROLE[role(jn)]
                ax.scatter(p[0],p[2],color=c,s=26,zorder=5)
    # labels
    out,_=fk(pose(13))
    ax.text(-0.062,-0.080,'n = 1, 2, 3\nhip yaw, roll, pitch',fontsize=5.8,va='center',ha='right')
    p=out['LKneePitch'][0];ax.annotate('n = 4  knee pitch\n$q_4$ = %+.2f rad'%pose(13)['LKneePitch'],xy=(p[0],p[2]),xytext=(p[0]+0.045,p[2]+0.045),fontsize=5.8,arrowprops=dict(arrowstyle='-',lw=.5))
    p=out['LAnklePitch'][0];ax.annotate('n = 5, 6  ankle pitch, roll\n$q_5$ = %+.2f rad'%pose(13)['LAnklePitch'],xy=(p[0],p[2]),xytext=(p[0]+0.05,p[2]+0.03),fontsize=5.8,arrowprops=dict(arrowstyle='-',lw=.5))
    p=out['LHipPitch'][0];ax.annotate('$q_3$ = %+.2f rad'%pose(13)['LHipPitch'],xy=(p[0],p[2]),xytext=(p[0]+0.045,p[2]-0.0),fontsize=5.8,arrowprops=dict(arrowstyle='-',lw=.5))
    o=(-0.095,-0.285);ax.annotate('',xy=(o[0]+0.035,o[1]),xytext=o,arrowprops=dict(arrowstyle='->',lw=1));ax.annotate('',xy=(o[0],o[1]+0.035),xytext=o,arrowprops=dict(arrowstyle='->',lw=1))
    ax.text(o[0]+0.038,o[1]-0.007,'x',fontsize=7,fontweight='bold');ax.text(o[0]-0.006,o[1]+0.038,'z',fontsize=7,fontweight='bold')
    ax.set_xlim(-0.12,0.15);ax.set_ylim(-0.30,0.0);ax.set_aspect('equal');ax.grid(alpha=.25);ax.legend(fontsize=5.5,loc='upper right',frameon=False)
    ax.set_xlabel('x (m), forward',fontsize=6.5);ax.set_ylabel('z (m), up',fontsize=6.5);ax.tick_params(labelsize=5.5);ax.set_title('(b) left leg, side view, base frame',fontsize=7)
fig=plt.figure(figsize=(7.2,3.3))
g=fig.add_gridspec(1,2,width_ratios=[1.35,1],wspace=0.26)
a1=fig.add_subplot(g[0]);chain_diagram(a1);a1.set_title('(a) joint index n, role, local axis, and joint state q',fontsize=7)
a2=fig.add_subplot(g[1]);side_overlay(a2)
fig.legend(handles=[Line2D([0],[0],marker='o',color=c,lw=0,ms=5,label=r+' joint') for r,c in ROLE.items()],loc='lower center',ncol=3,fontsize=6.5,frameon=False) if False else None
from matplotlib.lines import Line2D
fig.legend(handles=[Line2D([0],[0],marker='o',color=c,lw=0,ms=5,label=r+' joint') for r,c in ROLE.items()],loc='lower left',ncol=3,fontsize=6.5,frameon=False,bbox_to_anchor=(0.03,0.0))
plt.tight_layout(rect=(0,.05,1,1));plt.savefig('fig/f_kin3d.pdf',dpi=300);plt.close()
# state heatmap: dq_n(t)=q_n - q_ready
Q=np.array([[dict(zip(lj,fr[1])).get(n,READY[n]) for n in N] for fr in loop.frames[:-1]]).T  # 22 x 51
D=Q-np.array([READY[n] for n in N])[:,None]
tt=np.array([t for t,_ in loop.frames[:-1]])
fig,ax=plt.subplots(figsize=(3.45,3.0))
im=ax.imshow(D,aspect='auto',cmap='RdBu_r',vmin=-0.8,vmax=0.8,extent=[0,loop.duration,22.5,0.5],interpolation='nearest')
ax.set_yticks(range(1,23));ax.set_yticklabels([str(i) for i in range(1,23)],fontsize=5.5);ax.set_xlabel('t (s)');ax.set_ylabel('joint index n')
for b in (6.5,12.5,16.5,20.5): ax.axhline(b,color='k',lw=.6)
for y,l in [(3.5,'L leg'),(9.5,'R leg'),(14.5,'L arm'),(18.5,'R arm'),(21.5,'head')]: ax.text(loop.duration+0.04,y,l,fontsize=5.5,va='center')
cb=plt.colorbar(im,ax=ax,pad=0.12,fraction=.06);cb.set_label(r'$q_n(t)-q_n^{\,ready}$ (rad)',fontsize=6);cb.ax.tick_params(labelsize=5)
plt.tight_layout();plt.savefig('fig/f_tensor.pdf');plt.close()
# phase portraits
v=(np.roll(Q,-1,1)-Q)/0.04
fig,ax=plt.subplots(1,3,figsize=(3.45,1.55))
for a,(n,t) in zip(ax,[('LHipPitch','hip pitch (n=3)'),('LKneePitch','knee pitch (n=4)'),('LAnklePitch','ankle pitch (n=5)')]):
    i=N.index(n);q=np.append(Q[i],Q[i][0]);d=np.append(v[i],v[i][0]);a.plot(q,d,'k',lw=.9);a.scatter(q[0],d[0],s=8,color='#c0392b',zorder=5)
    vb=J[n]['lim']['velocity'];a.axhline(vb,color='gray',ls='--',lw=.8);a.axhline(-vb,color='gray',ls='--',lw=.8);a.set_ylim(-7.2,7.2)
    a.set_title(t,fontsize=5.5);a.set_xlabel(r'$q_n$ (rad)',fontsize=6);a.tick_params(labelsize=5)
ax[0].set_ylabel(r'$\dot q_n$ (rad/s)',fontsize=6)
plt.tight_layout(pad=.3);plt.savefig('fig/f_fase.pdf');plt.close()
# table data
rows=[]
for k,n in enumerate(N,1):
    L=J[n]['lim']; ax_=J[n]['axis']; rows.append(dict(n=k,name=n,role=role(n),axis=[round(float(x),3) for x in ax_],lo=L['lower'],hi=L['upper'],vmax=L['velocity'],ready=READY[n],k13=pose(13)[n]))
json.dump(rows,open('tabel_sendi.json','w'),indent=1)
print('ok')
