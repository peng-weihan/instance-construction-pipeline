"""Independent certificate validation from source polygons, not claimed output shapes."""
import collections,math
from shapely.geometry import Polygon
from shapely.ops import unary_union
from shapely import affinity

def item_geometry(item):
    shapes=item.get('shapes',[item]);parts=[]
    for s in shapes:
        if s['type']!='polygon':raise ValueError('unsupported input geometry')
        shell=[(v['x'],v['y']) for v in s['vertices']]
        holes=[[(v['x'],v['y']) for v in h['vertices']] for h in s.get('holes',[])]
        p=Polygon(shell,holes)
        if not p.is_valid or p.area<=0:raise ValueError('invalid source polygon')
        parts.append(p)
    return unary_union(parts)

def validate(instance,certificate,constants):
    if not isinstance(certificate,dict):raise ValueError('certificate must be a JSON object')
    bins=certificate.get('bins',[])
    if len(bins)!=1 or bins[0].get('id')!=0 or bins[0].get('copies',1)!=1:raise ValueError('one bin with one copy required')
    items=instance['item_types'];original=[item_geometry(i) for i in items];counts=collections.Counter();placed=[]
    W=instance['bin_types'][0]['width'];H=instance['bin_types'][0]['height'];tol=constants['boundary_tolerance_factor']*max(W,H,1)
    for entry in bins[0].get('items',[]):
        if not isinstance(entry,dict):raise ValueError('placement must be a JSON object')
        i=entry.get('id');angle=entry.get('angle',0);mirror=entry.get('mirror',False)
        if type(i)!=int or not 0<=i<len(items) or type(mirror)!=bool:raise ValueError('invalid item identity')
        if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in [angle,entry.get('x'),entry.get('y')]):raise ValueError('nonfinite placement')
        allowed=items[i].get('allowed_rotations',[{'start':0,'end':0}])
        ok=False
        for rot in allowed:
            mir=rot.get('mirror',False)
            if mirror!=mir and not (items[i].get('allow_mirroring',False) and mirror):continue
            a=angle%360;lo=rot['start'];hi=rot['end']
            angle_tol=constants['rotation_tolerance_degrees']
            if lo-angle_tol<=a<=hi+angle_tol or (a==0 and hi==360):ok=True
        if not ok:raise ValueError('forbidden rotation or mirror')
        p=original[i]
        if mirror:p=affinity.scale(p,xfact=-1,yfact=1,origin=(0,0))
        p=affinity.rotate(p,angle,origin=(0,0));p=affinity.translate(p,entry['x'],entry['y'])
        x0,y0,x1,y1=p.bounds
        if x0 < -tol or y0 < -tol or x1>W+tol or y1>H+tol:raise ValueError('outside strip')
        placed.append(p);counts[i]+=1
    if counts!=collections.Counter({i:it.get('copies',1) for i,it in enumerate(items)}):raise ValueError('missing or repeated pieces')
    for i,a in enumerate(placed):
        for b in placed[:i]:
            if a.intersects(b) and a.intersection(b).area>constants['intersection_area_tolerance_factor']*max(min(a.area,b.area),1):raise ValueError('overlap')
    length=max(p.bounds[2] for p in placed)
    return {'length':length,'area_lower_bound':sum(g.area*it.get('copies',1) for g,it in zip(original,items))/H,
            'pieces':sum(counts.values())}
