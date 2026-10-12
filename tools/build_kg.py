"""Build tri/kg.js: the Koppen-Geiger climate raster, country raster, borders and per-climate stats
for the Three crops app.

Usage: python3 tools/build_kg.py <srcdir> 12 tri/kg.js
<srcdir> must hold:
  x/kgcpy/kmz_int_reshape.png, x/kgcpy/kg_zoneNum.csv  (unpacked from `pip download kgcpy`, BSD-3)
  c50.json, c110.json   (npm world-atlas@2.0.2 countries-50m / countries-110m)
  codes.json            (npm i18n-iso-countries@7.11.0 codes.json)
The factor 12 resamples the 1/36 degree raster to 1/3 degree (1080 x 540) by majority vote.
"""
import json, sys, numpy as np
from PIL import Image, ImageDraw
Image.MAX_IMAGE_PIXELS=None
B=sys.argv[1]; F=int(sys.argv[2]); OUT=sys.argv[3]
src=np.array(Image.open(B+'/x/kgcpy/kmz_int_reshape.png'))
H0,W0=src.shape; H,W=H0//F,W0//F
blk=src.reshape(H,F,W,F).transpose(0,2,1,3).reshape(H,W,F*F)
counts=np.stack([(blk==k).sum(-1) for k in range(33)],-1)
ocean=counts[...,32]
land=counts.copy(); land[...,32]=0; land[...,0]=0
z=land.argmax(-1).astype(np.uint8)
z[ocean>0.55*F*F]=0
zones=[l.split(',')[1] for l in open(B+'/x/kgcpy/kg_zoneNum.csv').read().split('\n')[1:] if l]
# topojson
def decode(topo):
    sc,tr=topo['transform']['scale'],topo['transform']['translate']
    arcs=[]
    for a in topo['arcs']:
        x=y=0; pts=[]
        for dx,dy in a:
            x+=dx;y+=dy; pts.append((x*sc[0]+tr[0],y*sc[1]+tr[1]))
        arcs.append(pts)
    return arcs
def ring(arcs,idx):
    pts=[]
    for i in idx:
        a=arcs[i] if i>=0 else arcs[~i][::-1]
        pts.extend(a if not pts else a[1:])
    return pts
codes=json.load(open(B+'/codes.json')); num2a2={c[2]:c[0] for c in codes}
t50=json.load(open(B+'/c50.json')); arcs50=decode(t50)
cimg=Image.new('L',(W,H),0); d=ImageDraw.Draw(cimg)
clist=['']; 
def P(lon,lat): return ((lon+180)*W/360,(90-lat)*H/180)
for g in t50['objects']['countries']['geometries']:
    a2=num2a2.get(g.get('id'))
    if not a2:
        nm=g['properties'].get('name'); 
        a2={'Kosovo':'XK','N. Cyprus':'CY','Somaliland':'SO'}.get(nm)
        if not a2: continue
    if a2 not in clist: clist.append(a2)
    ci=clist.index(a2)
    polys=g['arcs'] if g['type']=='MultiPolygon' else [g['arcs']] if g['type']=='Polygon' else []
    for poly in polys:
        for k,r in enumerate(poly):
            pts=[P(*p) for p in ring(arcs50,r)]
            if len(pts)>2: d.polygon(pts,fill=(ci if k==0 else 0))
c=np.array(cimg)
# assign land cells with no country to nearest country (coastal raster mismatch) - simple dilation
for _ in range(3):
    m=(c==0)&(z>0)
    if not m.any(): break
    for dy,dx in ((0,1),(0,-1),(1,0),(-1,0)):
        s=np.roll(np.roll(c,dy,0),dx,1); f=m&(s>0)&(c==0); c[f]=s[f]
c[z==0]=0
def rle(a):
    out=[]; 
    flat=a.flatten().tolist(); prev=flat[0]; n=0
    for v in flat:
        if v==prev: n+=1
        else: out.append(f'{prev}' if n==1 else f'{prev}x{n}'); prev=v; n=1
    out.append(f'{prev}' if n==1 else f'{prev}x{n}')
    return ','.join(out)
# stats: area per zone and per country (cos lat)
lat=90-(np.arange(H)+.5)*180/H; wt=np.cos(np.radians(lat))[:,None]*np.ones((1,W))
tot=wt[z>0].sum(); stats={}
for k in range(1,32):
    m=z==k
    if not m.any(): continue
    a=wt[m].sum(); cc={}
    for ci in np.unique(c[m]):
        if ci==0: continue
        cc[clist[ci]]=float(wt[m&(c==ci)].sum())
    top=sorted(cc.items(),key=lambda x:-x[1])[:8]
    stats[zones[k-1]]={'land':round(float(a/tot)*100,2),'top':[t for t,_ in top]}
# borders 110m
t110=json.load(open(B+'/c110.json')); arcs110=decode(t110)
segs=[]
for a in arcs110:
    s=''; px=None
    for lon,lat in a:
        x,y=(lon+180)*2,(90-lat)*2
        if px is not None and abs(x-px)>300: s+=f'M{x:.1f} {y:.1f}'
        else: s+=('M' if not s else 'L')+f'{x:.1f} {y:.1f}'
        px=x
    segs.append(s)
data={'W':W,'H':H,'zones':zones[:31],'z':rle(z),'countries':clist,'c':rle(c),'stats':stats,'borders':''.join(segs)}
js='window.KG='+json.dumps(data,separators=(',',':'))+';\n'
open(OUT,'w').write(js); print(W,H,len(js), len(data['z']), len(data['c']), len(data['borders']), len(clist))
