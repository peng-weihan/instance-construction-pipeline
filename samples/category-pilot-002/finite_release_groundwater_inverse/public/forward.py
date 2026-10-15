"""Original task generator: finite-duration rectangular source in infinite 3-D ADE.
No MODFLOW binary is invoked. Units: m, day, g/m^3. Public numerical forward model.
"""
from math import erf, sqrt, exp
def concentration(p, x, y, z, t, steps=128):
    end=min(t,p['t_start']+p['duration'])
    if end<=p['t_start']: return 0.0
    dt=(end-p['t_start'])/steps
    total=0.0
    for i in range(steps):
        tau=t-(p['t_start']+(i+.5)*dt)
        factors=[]
        for q,c,h,D,v in [(x,p['cx'],p['hx'],p['Dx'],p['vx']),
                           (y,p['cy'],p['hy'],p['Dy'],0.0),
                           (z,p['cz'],p['hz'],p['Dz'],0.0)]:
            s=sqrt(4*D*tau); q=q-v*tau
            factors.append(.5*(erf((q-c+h)/s)-erf((q-c-h)/s)))
        total+=factors[0]*factors[1]*factors[2]*exp(-p['decay']*tau)
    return p['rate']*dt*total/(8*p['hx']*p['hy']*p['hz'])
