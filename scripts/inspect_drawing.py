import json, math, collections
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
ROOT=Path(__file__).resolve().parents[1]
d=json.loads((ROOT/'analysis/geometry.json').read_text(encoding='utf-8-sig'))
lines=[]; texts=[]; dims=[]; flat=[]
def pt(p,m):
    return (m @ np.array([p[0],p[1],p[2] if len(p)>2 else 0,1]))[:3].tolist()
def walk(entities,m=np.eye(4),parent='',depth=0):
    if depth>12:return
    for e in entities:
        t=e['type']; h=parent+'/'+e['handle']; layer=e['layer']; r=dict(e,source=h)
        if t=='AcDbBlockReference' and e['name'] in d['blocks']:
            b=d['blocks'][e['name']]; a=e['rotation']; c,s=math.cos(a),math.sin(a); sx,sy,sz=e['scale']; trans=np.eye(4); trans[:3,:3]=[[c*sx,-s*sy,0],[s*sx,c*sy,0],[0,0,sz]]; trans[:3,3]=e['position']; org=np.eye(4); org[:3,3]=-np.array(b.get('origin',[0,0,0])); walk(b['entities'],m@trans@org,h,depth+1)
        elif t=='AcDbLine':
            r['a']=pt(e['a'],m);r['b']=pt(e['b'],m); lines.append([r['a'][:2],r['b'][:2]]);flat.append(r)
        elif 'Polyline' in t and 'points' in e:
            stride=2 if t=='AcDbPolyline' else 3;p=e['points'];p=[pt(p[i:i+stride],m) for i in range(0,len(p),stride)];r['vertices']=p;flat.append(r)
            if e.get('closed'):p=p+[p[0]]
            lines.extend([[a[:2],b[:2]] for a,b in zip(p,p[1:])])
        elif t in ['AcDbCircle','AcDbArc']:
            a=e.get('start',0);b=e.get('end',2*math.pi)
            if b<a:b+=2*math.pi
            p=[pt([e['center'][0]+e['radius']*math.cos(v),e['center'][1]+e['radius']*math.sin(v),e['center'][2]],m) for v in np.linspace(a,b,25)];lines.extend([[a[:2],b[:2]] for a,b in zip(p,p[1:])]);r['center']=pt(e['center'],m);flat.append(r)
        elif t in ['AcDbText','AcDbMText']:
            r['position']=pt(e['position'],m);texts.append(r)
        elif 'Dimension' in t:
            if e.get('textPosition'):r['textPosition']=pt(e['textPosition'],m)
            dims.append(r)
walk(d['entities'])
(ROOT/'analysis/flat.json').write_text(json.dumps({'entities':flat,'texts':texts,'dimensions':dims}),encoding='utf-8')
summary={'entities':len(d['entities']),'blocks':len(d['blocks']),'warnings':dict(collections.Counter(w.split(':')[0].rsplit(' ',1)[0] for w in d['warnings'])),'types':dict(collections.Counter(e['type'] for e in d['entities'])),'layers':dict(collections.Counter(e['layer'] for e in flat)),'texts':len(texts),'dimensions':len(dims),'line_segments':len(lines)}
(ROOT/'analysis/summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
(ROOT/'analysis/texts.tsv').write_text('\n'.join(f"{e['source']}\t{e['position'][0]:.3f}\t{e['position'][1]:.3f}\t{e['text']}" for e in texts),encoding='utf-8')
fig,ax=plt.subplots(figsize=(20,14));ax.add_collection(LineCollection(lines,linewidths=.2,colors='#283d46'));ax.autoscale();ax.set_aspect('equal');ax.grid(alpha=.2);fig.savefig(ROOT/'analysis/overview.png',dpi=130);plt.close(fig)
print(json.dumps(summary,ensure_ascii=False));print('bounds',np.array(lines).reshape(-1,2).min(0),np.array(lines).reshape(-1,2).max(0))
