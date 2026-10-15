"""Published conservative mobile/immobile transport with Langmuir storage.

Units are m, day, g/m3. Source rates are total g/day. The spatial operator is
independent of the private stencil used to construct the observation labels.
"""
import numpy as np
from scipy.sparse import diags, eye, kron
from hydrology import hydraulic_fields,advection_operator,stable_step

GLOBAL_KEYS = ['velocity_scale','diffusion_scale','capacity','affinity','immobile_ratio','exchange','decay']
SOURCE_KEYS = ['cx','cy','cz','hx','hy','hz','t_start','duration','rate0','rate1','rate2']

def sources(scene, p, experiment):
    if experiment == 'calibration':return [scene['calibration_source']]
    return [{k:p[f's{i}_{k}'] for k in SOURCE_KEYS} for i in [1,2]]

def concentration_from_storage(w,q,b):
    # Positive root of b*C^2 + (1+b*q-b*w)*C - w = 0.
    a=1+b*q-b*w;root=np.sqrt(a*a+4*b*w)
    return np.where(a>=0,2*w/(a+root),(root-a)/(2*b))

def simulate(scene,p,days,experiment='contaminant'):
    nx,ny,nz=scene['grid']['shape_xyz'];h=np.array(scene['grid']['spacing_m']);dt=scene['time_step_days']
    origin=np.array(scene['grid']['origin_m']);axes=[origin[i]+(np.arange(n)+.5)*h[i] for i,n in enumerate([nx,ny,nz])]
    def lap(n,spacing,inlet=False):
        d=np.full(n,-2.);d[-1]=-1
        if not inlet:d[0]=-1
        return diags([np.ones(n-1),d,np.ones(n-1)],[-1,0,1],format='csr')/spacing**2
    Ix,Iy,Iz=map(eye,[nx,ny,nz])
    _,water_fluxes,_=hydraulic_fields(scene,p,0)
    velocities=[q*p['velocity_scale']/scene['porosity'] for q in water_fluxes]
    dt=stable_step(scene,p,velocities)
    Dx,Dy,Dz=np.array(scene['D_xyz'])*p['diffusion_scale']
    op=Dx*kron(kron(lap(nx,h[0],True),Iy),Iz)+Dy*kron(kron(Ix,lap(ny,h[1])),Iz)
    op+=Dz*kron(kron(Ix,Iy),lap(nz,h[2]))+advection_operator(scene,velocities)
    terms=[]
    for s in sources(scene,p,experiment):
        fractions=[]
        for i,key in enumerate('xyz'):
            center=s['c'+key];half=s['h'+key]
            fractions.append(np.maximum(0,np.minimum(axes[i]+h[i]/2,center+half)-np.maximum(axes[i]-h[i]/2,center-half))/h[i])
        spatial=fractions[0][:,None,None]*fractions[1][None,:,None]*fractions[2][None,None,:]
        spatial=(spatial/(8*s['hx']*s['hy']*s['hz']*scene['porosity'])).ravel();terms.append((s,spatial))
    cm=np.zeros(nx*ny*nz);ci=cm.copy();w=cm.copy();snapshots={};wanted={round(float(d)/dt):d for d in days}
    for step in range(1,max(wanted)+1):
        begin=(step-1)*dt;end=step*dt;q=np.zeros_like(cm)
        for s,spatial in terms:
            for j in range(3):
                left=s['t_start']+j*s['duration']/3;right=s['t_start']+(j+1)*s['duration']/3
                fraction=max(0.,min(end,right)-max(begin,left))/dt
                if fraction:q+=spatial*s['rate'+str(j)]*fraction
        transfer=p['exchange']*(cm-ci)
        w=w+dt*(op@cm-p['decay']*cm-transfer+q)
        ci=ci+dt*(transfer/p['immobile_ratio']-p['decay']*ci)
        if np.min(w)<-1e-12 or np.min(ci)<-1e-12:raise ValueError('negative conserved state; discretization unstable')
        w=np.maximum(w,0);ci=np.maximum(ci,0);cm=concentration_from_storage(w,p['capacity'],p['affinity'])
        if step in wanted:snapshots[wanted[step]]=cm.reshape(nx,ny,nz).copy()
    return snapshots
