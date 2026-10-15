"""Public finite-volume Darcy solver for a spatially heterogeneous aquifer."""
import numpy as np
import json
from collections import OrderedDict
from scipy.ndimage import map_coordinates
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve

def conductivity(scene,p):
    shape=scene['conductivity_control_shape'];coef=np.array([p[f'logK_{i:03d}'] for i in range(int(np.prod(shape)))]).reshape(shape)
    xyz=np.meshgrid(*(np.linspace(0,shape[i]-1,n) for i,n in enumerate(scene['grid']['shape_xyz'])),indexing='ij')
    field=map_coordinates(coef,np.array(xyz),order=1,mode='nearest')
    return scene['base_conductivity_m_day']*np.exp(field)

def _solve_hydraulic_fields(scene,p,axis=0):
    K=conductivity(scene,p);shape=K.shape;ids=np.arange(K.size).reshape(shape);h=scene['grid']['spacing_m']
    rows=[];cols=[];values=[];diagonal=np.zeros(K.size);rhs=np.zeros(K.size)
    for ax in range(3):
        left=[slice(None)]*3;right=left.copy();left[ax]=slice(None,-1);right[ax]=slice(1,None);left=tuple(left);right=tuple(right)
        a=K[left];b=K[right];t=(2*a*b/(a+b)/h[ax]**2).ravel();i=ids[left].ravel();j=ids[right].ravel()
        np.add.at(diagonal,i,t);np.add.at(diagonal,j,t)
        rows.extend([i,j]);cols.extend([j,i]);values.extend([-t,-t])
    hi,lo=scene['hydraulic_heads_m'][str(axis)]
    for side,head in [(0,hi),(-1,lo)]:
        s=[slice(None)]*3;s[axis]=side;s=tuple(s);ix=ids[s].ravel();t=2*K[s].ravel()/h[axis]**2
        diagonal[ix]+=t;rhs[ix]+=t*head
    rows.append(np.arange(K.size));cols.append(np.arange(K.size));values.append(diagonal)
    A=coo_matrix((np.concatenate(values),(np.concatenate(rows),np.concatenate(cols))),shape=(K.size,K.size)).tocsr()
    pressure=spsolve(A,rhs).reshape(shape);fluxes=[]
    for ax in range(3):
        fs=list(shape);fs[ax]+=1;q=np.zeros(fs)
        l=[slice(None)]*3;r=l.copy();middle=l.copy();l[ax]=slice(None,-1);r[ax]=slice(1,None);middle[ax]=slice(1,-1)
        l,r,middle=tuple(l),tuple(r),tuple(middle)
        q[middle]=-2*K[l]*K[r]/(K[l]+K[r])*(pressure[r]-pressure[l])/h[ax]
        if ax==axis:
            first=[slice(None)]*3;first[ax]=0;last=first.copy();last[ax]=-1;first,last=tuple(first),tuple(last)
            q[first]=2*K[first]*(hi-pressure[first])/h[ax];q[last]=2*K[last]*(pressure[last]-lo)/h[ax]
        fluxes.append(q)
    s=[slice(None)]*3;s[axis]=0
    total=float(np.sum(fluxes[axis][tuple(s)])*np.prod([h[i] for i in range(3) if i!=axis]))
    return pressure,fluxes,total

def advection_operator(scene,velocities):
    shape=scene['grid']['shape_xyz'];ids=np.arange(np.prod(shape)).reshape(shape);h=scene['grid']['spacing_m']
    rows=[];cols=[];data=[];diagonal=np.zeros(int(np.prod(shape)))
    for ax,v in enumerate(velocities):
        l=[slice(None)]*3;r=l.copy();middle=l.copy();l[ax]=slice(None,-1);r[ax]=slice(1,None);middle[ax]=slice(1,-1)
        i=ids[tuple(l)].ravel();j=ids[tuple(r)].ravel();q=v[tuple(middle)].ravel()/h[ax]
        positive=np.maximum(q,0);negative=np.maximum(-q,0)
        np.add.at(diagonal,i,-positive);np.add.at(diagonal,j,-negative)
        rows.extend([j,i]);cols.extend([i,j]);data.extend([positive,negative])
        first=[slice(None)]*3;first[ax]=0;last=first.copy();last[ax]=-1
        # Inflow concentration is zero; outward boundary flux removes cell mass.
        diagonal[ids[tuple(first)].ravel()]-=np.maximum(-v[tuple(first)].ravel()/h[ax],0)
        diagonal[ids[tuple(last)].ravel()]-=np.maximum(v[tuple(last)].ravel()/h[ax],0)
    rows.append(np.arange(len(diagonal)));cols.append(np.arange(len(diagonal)));data.append(diagonal)
    return coo_matrix((np.concatenate(data),(np.concatenate(rows),np.concatenate(cols))),shape=(len(diagonal),len(diagonal))).tocsr()

def stable_step(scene,p,velocities):
    h=np.array(scene['grid']['spacing_m']);outgoing=np.zeros(scene['grid']['shape_xyz'])
    for ax,v in enumerate(velocities):
        lo=[slice(None)]*3;hi=lo.copy();lo[ax]=slice(None,-1);hi[ax]=slice(1,None)
        outgoing+=(np.maximum(v[tuple(hi)],0)+np.maximum(-v[tuple(lo)],0))/h[ax]
    rate=float(outgoing.max()+2*np.sum(np.array(scene['D_xyz'])*p['diffusion_scale']/h**2)+p['decay']+p['exchange'])
    rate=max(rate,p['exchange']/p['immobile_ratio']+p['decay'])
    subdivisions=max(1,int(np.ceil(scene['time_step_days']*rate/.8)))
    return scene['time_step_days']/subdivisions

_HYDRAULIC_CACHE=OrderedDict()
def hydraulic_fields(scene,p,axis=0):
    keys=sorted(k for k in p if k.startswith('logK_'))
    key=(json.dumps({k:scene[k] for k in ['grid','conductivity_control_shape','base_conductivity_m_day','hydraulic_heads_m']},sort_keys=True),tuple(p[k] for k in keys),axis)
    if key not in _HYDRAULIC_CACHE:
        _HYDRAULIC_CACHE[key]=_solve_hydraulic_fields(scene,p,axis)
        if len(_HYDRAULIC_CACHE)>4:_HYDRAULIC_CACHE.popitem(last=False)
    return _HYDRAULIC_CACHE[key]
