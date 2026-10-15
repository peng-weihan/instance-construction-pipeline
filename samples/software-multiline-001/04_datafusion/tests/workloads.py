"""Independent deterministic row semantics; Python comparison is oracle, not candidate sorting."""
import functools,json
MASK=(1<<64)-1
BASE={'rows':8193,'partitions':3,'batch_size':257,'payload_width':17,'seed':7291,'null_every':17,'tag_null_every':19,'descending':False,'nulls_first':False,'ordered_prefix':False,'k':65}
def spec(name,**updates):return {'id':name,**BASE,**updates}
CORRECTNESS=[spec('nullable-asc'),spec('nullable-desc',descending=True,nulls_first=True),spec('null-first',nulls_first=True),spec('desc-null-last',descending=True),spec('k-one',k=1),spec('k-above-n',rows=313,k=500),spec('full-sort',rows=4099,k=None),spec('batch-boundary',rows=16391,batch_size=31,k=513),spec('wide-row',payload_width=513,partitions=5),spec('prefix-early-exit',rows=65539,ordered_prefix=True,null_every=0,tag_null_every=0,k=129),spec('single-partition',partitions=1,batch_size=1031),spec('all-null-primary',null_every=1)]
PERFORMANCE=[spec('small-k-narrow',rows=250003,k=32,payload_width=8,partitions=4,batch_size=8192),spec('small-k-wide',rows=250003,k=64,payload_width=256,partitions=4,batch_size=8192),spec('medium-k-wide',rows=500009,k=2048,payload_width=128,partitions=4,batch_size=8192),spec('prefix-scan',rows=1000003,k=256,payload_width=64,partitions=4,batch_size=8192,ordered_prefix=True,null_every=0,tag_null_every=0),spec('null-heavy',rows=500009,k=128,payload_width=32,partitions=4,batch_size=4096,null_every=2,tag_null_every=3),spec('reverse-order',rows=500009,k=512,payload_width=64,partitions=4,batch_size=8192,descending=True,nulls_first=True)]
def row(i,s):
 x=(i*6364136223846793005+s['seed'])&MASK
 key=None if s['null_every'] and i%s['null_every']==0 else (i//512 if s['ordered_prefix'] else ((x>>17)%97)-48)
 tag=None if s['tag_null_every'] and i%s['tag_null_every']==0 else f't{x%1009:04}-'+('中' if x%3==0 else 'z')
 return [i,key,tag,f'p{i:016x}:'+'z'*s['payload_width']]
def compare_values(a,b,descending,nulls_first):
 if a is None or b is None:
  return 0 if a is b else (-1 if (a is None)==nulls_first else 1)
 c=(a>b)-(a<b)
 return -c if descending else c
def comparator(s):
 def cmp(a,b):
  return compare_values(a[1],b[1],s['descending'],s['nulls_first']) or compare_values(a[2],b[2],not s['descending'],not s['nulls_first']) or ((a[0]>b[0])-(a[0]<b[0]))
 return cmp
def expected(s):
 # nlargest would depend on another custom heap; full independent sorting is clearer.
 values=[row(i,s) for i in range(s['rows'])]
 values.sort(key=functools.cmp_to_key(comparator(s)))
 return values if s['k'] is None else values[:s['k']]
if __name__=='__main__':print(json.dumps({'correctness':CORRECTNESS,'performance':PERFORMANCE},indent=2))
