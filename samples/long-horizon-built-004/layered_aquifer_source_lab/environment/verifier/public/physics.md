Equation: R(z) dC/dt = Dx C_xx + Dy C_yy + Dz C_zz - vx(z) C_x - lambda C + q(x,y,z,t)/porosity.
R, vx, porosity and D are public and fixed. Unknown source is a uniform rectangular region with centre c and half-widths h, active on [t_start,t_start+duration).
rate is TOTAL mass per day; q=rate/(8*hx*hy*hz) inside the region and zero outside. decay has units day^-1.
Use the public grid and boundary conventions. At interfaces C and normal diffusive flux are continuous; v is parallel to interfaces.
The inlet boundary's discrete ghost cell concentration is zero; the outlet and transverse ghost cells copy the adjacent cell. Public grid indices are zero-based.
Observations are cell averages; fractional source-cell overlap matters. A below_detection record means [0,detection_limit), not an exact zero observation.
The private generating discretization is first-order upwind advection and centred diffusion; agents may use a conservative equivalent or more accurate numerical approximation.
Useful public self-checks: zero source preserves zero; no source/decay/flux preserves total sum(porosity*R*C*cell_volume); diffusion of a pulse smooths without negative concentrations.
