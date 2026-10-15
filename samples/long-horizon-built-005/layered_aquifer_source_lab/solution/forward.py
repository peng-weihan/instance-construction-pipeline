"""Publicly specified cell-centred ADE, implemented as a sparse linear operator.
Independent implementation from the explicit-stencil authoring generator.
"""
import numpy as np
from scipy.sparse import diags,eye,kron

def simulate(scene,p,days):
    nx,ny,nz=scene['grid']['shape_xyz'];h=np.array(scene['grid']['spacing_m'])
    origin=np.array(scene['grid']['origin_m']);dt=scene['time_step_days']
    axes=[origin[i]+(np.arange(n)+.5)*h[i] for i,n in enumerate([nx,ny,nz])]
    z=axes[2];vx=np.zeros(nz);R=np.zeros(nz)
    for layer in scene['layers']:
        m=(z>=layer.get('z_min',-np.inf))&(z<layer.get('z_max',np.inf));vx[m]=layer['vx'];R[m]=layer['R']
    def lap(n,spacing,inlet=False):
        d=np.full(n,-2.);d[-1]=-1
        if not inlet:d[0]=-1
        return diags([np.ones(n-1),d,np.ones(n-1)],[-1,0,1],format='csr')/spacing**2
    Ix,Iy,Iz=map(eye,[nx,ny,nz]);invR=diags(1/R);V=diags(vx/R)
    Dx,Dy,Dz=scene['D_xyz']
    dxback=diags([-np.ones(nx-1),np.ones(nx)],[-1,0],format='csr')/h[0]
    op=Dx*kron(kron(lap(nx,h[0],True),Iy),invR)+Dy*kron(kron(Ix,lap(ny,h[1])),invR)
    op+=Dz*kron(kron(Ix,Iy),invR@lap(nz,h[2]))-kron(kron(dxback,Iy),V)
    op-=p['decay']*kron(kron(Ix,Iy),invR)
    fractions=[]
    for i,key in enumerate(['x','y','z']):
        c=p['c'+key];r=p['h'+key]
        fractions.append(np.maximum(0,np.minimum(axes[i]+h[i]/2,c+r)-np.maximum(axes[i]-h[i]/2,c-r))/h[i])
    q=fractions[0][:,None,None]*fractions[1][None,:,None]*fractions[2][None,None,:]
    q*=p['rate']/(8*p['hx']*p['hy']*p['hz']*scene['porosity'])
    q=(q/R[None,None,:]).ravel();c=np.zeros(nx*ny*nz);snapshots={}
    wanted={round(float(d)/dt):d for d in days}
    for k in range(1,max(wanted)+1):
        c=c+dt*(op@c)
        if p['t_start']<=(k-.5)*dt<p['t_start']+p['duration']:c=c+dt*q
        if k in wanted:snapshots[wanted[k]]=c.reshape(nx,ny,nz).copy()
    return snapshots
