"""Independent loop assembly/CG pressure solution for constructing labels."""
import numpy as np
from scipy.interpolate import RegularGridInterpolator
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import cg

def hydraulic_fields(scene,p,axis=0):
    control=scene['conductivity_control_shape'];shape=scene['grid']['shape_xyz'];h=scene['grid']['spacing_m']
    coef=np.array([p[f'logK_{i:03d}'] for i in range(int(np.prod(control)))]).reshape(control)
    interpolation=RegularGridInterpolator(tuple(np.arange(n) for n in control),coef)
    positions=np.stack(np.meshgrid(*(np.linspace(0,control[i]-1,n) for i,n in enumerate(shape)),indexing='ij'),axis=-1)
    K=scene['base_conductivity_m_day']*np.exp(interpolation(positions));rows=[];cols=[];values=[];rhs=np.zeros(K.size)
    hi,lo=scene['hydraulic_heads_m'][str(axis)]
    for cell in np.ndindex(tuple(shape)):
        i=np.ravel_multi_index(cell,shape);diagonal=0.
        for ax in range(3):
            for direction in [-1,1]:
                neighbor=list(cell);neighbor[ax]+=direction
                if 0<=neighbor[ax]<shape[ax]:
                    neighbor=tuple(neighbor);t=2*K[cell]*K[neighbor]/(K[cell]+K[neighbor])/h[ax]**2
                    diagonal+=t;rows.append(i);cols.append(np.ravel_multi_index(neighbor,shape));values.append(-t)
                elif ax==axis:
                    t=2*K[cell]/h[ax]**2;diagonal+=t;rhs[i]+=t*(hi if direction==-1 else lo)
        rows.append(i);cols.append(i);values.append(diagonal)
    A=coo_matrix((values,(rows,cols)),shape=(K.size,K.size)).tocsr()
    head,flag=cg(A,rhs,rtol=1e-13,atol=1e-14,maxiter=20000)
    if flag:raise RuntimeError('independent pressure solver did not converge')
    head=head.reshape(shape);fluxes=[]
    for ax in range(3):
        fs=list(shape);fs[ax]+=1;flux=np.zeros(fs)
        for face in np.ndindex(tuple(fs)):
            if 0<face[ax]<shape[ax]:
                left=list(face);left[ax]-=1;left=tuple(left);right=face
                k=2*K[left]*K[right]/(K[left]+K[right]);flux[face]=-k*(head[right]-head[left])/h[ax]
            elif ax==axis:
                cell=list(face);cell[ax]=0 if face[ax]==0 else shape[ax]-1;cell=tuple(cell)
                flux[face]=2*K[cell]*(hi-head[cell])/h[ax] if face[ax]==0 else 2*K[cell]*(head[cell]-lo)/h[ax]
        fluxes.append(flux)
    s=[slice(None)]*3;s[axis]=0;total=float(fluxes[axis][tuple(s)].sum()*np.prod([h[i] for i in range(3) if i!=axis]))
    return head,fluxes,total
