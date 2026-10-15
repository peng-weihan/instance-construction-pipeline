Equation: R(z) dC/dt = Dx C_xx + Dy C_yy + Dz C_zz - vx(z) C_x - lambda C + q(x,y,z,t)/porosity.
R, vx, porosity and D are public and fixed. Unknown source is a uniform rectangular region with centre c and half-widths h, active on [t_start,t_start+duration).
rate is TOTAL mass per day; q=rate/(8*hx*hy*hz) inside the region and zero outside. decay has units day^-1.
Use the public grid and boundary conventions. At interfaces C and normal diffusive flux are continuous; v is parallel to interfaces.
The inlet boundary's discrete ghost cell concentration is zero; the outlet and transverse ghost cells copy the adjacent cell. Public grid indices are zero-based.
Observations are cell averages; fractional source-cell overlap matters. A below_detection record means [0,detection_limit), not an exact zero observation.
The private generating discretization is first-order upwind advection and centred diffusion; agents may use a conservative equivalent or more accurate numerical approximation.
Useful public self-checks: zero source preserves zero; no source/decay/flux preserves total sum(porosity*R*C*cell_volume); diffusion of a pulse smooths without negative concentrations.

Numerical observation convention: the grid origin is the lower cell-face corner, so centre i is origin+(i+0.5)*spacing. Layer bounds use z_min <= centre_z < z_max. Start from C=0 at t=0. The data-generating time discretization is explicit forward Euler at the fixed time_step_days; all transport/decay terms use the previous state. For step k=1,2,..., enable the source when t_start <= (k-0.5)*dt < t_start+duration, then record the updated state at k*dt. Observation days are integer multiples of dt. Do not round source start/end to grid points before this midpoint test. Source contribution is fractional overlap volume times rate/source_volume/porosity, divided by the cell-layer retardation R along with all other terms. There are no hidden fitted transport coefficients.
