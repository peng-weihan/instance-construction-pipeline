"""Independent explicit-stencil label generator for the dual-domain task."""
import numpy as np

def states(scene,p,days,experiment='contaminant'):
    shape=scene['grid']['shape_xyz'];dx,dy,dz=scene['grid']['spacing_m'];dt=scene['time_step_days']
    axes=[scene['grid']['origin_m'][i]+(np.arange(n)+.5)*scene['grid']['spacing_m'][i] for i,n in enumerate(shape)]
    velocity=np.zeros(shape[2])
    for layer in scene['layers']:
        m=(axes[2]>=layer.get('z_min',-np.inf))&(axes[2]<layer.get('z_max',np.inf));velocity[m]=layer['vx']*p['velocity_scale']
    sources=[scene['calibration_source']] if experiment=='calibration' else [{k:p[f's{i}_{k}'] for k in ['cx','cy','cz','hx','hy','hz','t_start','duration','rate0','rate1','rate2']} for i in [1,2]]
    spatial=[]
    for s in sources:
        f=[np.maximum(0,np.minimum(a+width/2,s['c'+key]+s['h'+key])-np.maximum(a-width/2,s['c'+key]-s['h'+key]))/width for a,width,key in zip(axes,[dx,dy,dz],'xyz')]
        spatial.append(f[0][:,None,None]*f[1][None,:,None]*f[2][None,None,:]/(8*s['hx']*s['hy']*s['hz']*scene['porosity']))
    cm=np.zeros(shape);ci=np.zeros(shape);stored=np.zeros(shape);snapshots={};wanted={round(float(d)/dt):d for d in days}
    Dx,Dy,Dz=np.array(scene['D_xyz'])*p['diffusion_scale']
    for step in range(1,max(wanted)+1):
        px=np.pad(cm,((1,1),(0,0),(0,0)),mode='edge');px[0]=0
        py=np.pad(cm,((0,0),(1,1),(0,0)),mode='edge');pz=np.pad(cm,((0,0),(0,0),(1,1)),mode='edge')
        flux=Dx*(px[2:]-2*cm+px[:-2])/dx**2+Dy*(py[:,2:]-2*cm+py[:,:-2])/dy**2+Dz*(pz[:,:,2:]-2*cm+pz[:,:,:-2])/dz**2
        flux-=velocity[None,None,:]*(cm-px[:-2])/dx
        source=np.zeros(shape)
        for s,distribution in zip(sources,spatial):
            for j in range(3):
                l=s['t_start']+j*s['duration']/3;r=s['t_start']+(j+1)*s['duration']/3
                fraction=max(0,min(step*dt,r)-max((step-1)*dt,l))/dt
                source+=distribution*s['rate'+str(j)]*fraction
        exchange=p['exchange']*(cm-ci)
        stored+=dt*(flux-p['decay']*cm-exchange+source)
        ci+=dt*(exchange/p['immobile_ratio']-p['decay']*ci)
        if stored.min()<-1e-12 or ci.min()<-1e-12:raise ValueError('negative generator state')
        stored=np.maximum(stored,0);ci=np.maximum(ci,0)
        a=1+p['affinity']*p['capacity']-p['affinity']*stored
        disc=np.sqrt(a*a+4*p['affinity']*stored)
        cm=np.where(a>=0,2*stored/(a+disc),(disc-a)/(2*p['affinity']))
        if step in wanted:snapshots[wanted[step]]=cm.copy()
    return snapshots
