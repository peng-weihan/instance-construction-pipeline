"""Private authoring generator for an original layered ADE scene; synthetic data only.
Cell-centred finite volume, first-order upwind advection, centred diffusion.
Not supplied to the solving agent. No inverse solver or candidate grading here.
"""
import numpy as np
def states(scene, source, sample_days):
    nx,ny,nz=scene['grid']['shape_xyz']; dx,dy,dz=scene['grid']['spacing_m']
    x0,y0,z0=scene['grid']['origin_m']; dt=scene['time_step_days']
    x=x0+(np.arange(nx)+.5)*dx;y=y0+(np.arange(ny)+.5)*dy;z=z0+(np.arange(nz)+.5)*dz
    v=np.array([.07 if zz<-.5 else (.12 if zz<1.5 else .17) for zz in z])[None,None,:]
    R=np.array([1.5 if zz<-.5 else (1.2 if zz<1.5 else 1.) for zz in z])[None,None,:]
    overlaps=[]
    for a,h,centres,spacing in [(source['cx'],source['hx'],x,dx),(source['cy'],source['hy'],y,dy),(source['cz'],source['hz'],z,dz)]:
        overlaps.append(np.maximum(0,np.minimum(centres+spacing/2,a+h)-np.maximum(centres-spacing/2,a-h))/spacing)
    q=source['rate']*overlaps[0][:,None,None]*overlaps[1][None,:,None]*overlaps[2][None,None,:]/(8*source['hx']*source['hy']*source['hz']*scene['porosity'])
    C=np.zeros((nx,ny,nz)); snapshots={}; nsteps=round(max(sample_days)/dt); wanted=set(sample_days)
    for k in range(1,nsteps+1):
        mid=(k-.5)*dt
        # Incoming concentration is zero at x_min; outflow uses zero gradient at x_max.
        px=np.pad(C,((1,1),(0,0),(0,0)),mode='edge');px[0]=0
        py=np.pad(C,((0,0),(1,1),(0,0)),mode='edge')
        pz=np.pad(C,((0,0),(0,0),(1,1)),mode='edge')
        diff=scene['D_xyz'][0]*(px[2:]-2*C+px[:-2])/dx**2+scene['D_xyz'][1]*(py[:,2:]-2*C+py[:,:-2])/dy**2+scene['D_xyz'][2]*(pz[:,:,2:]-2*C+pz[:,:,:-2])/dz**2
        rhs=diff-v*(C-px[:-2])/dx-source['decay']*C
        if source['t_start']<=mid<source['t_start']+source['duration']:rhs=rhs+q
        C=C+dt*rhs/R
        day=k*dt
        if day in wanted:snapshots[day]=C.copy()
    return snapshots
