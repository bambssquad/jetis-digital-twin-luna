"""Check source dimensions, orientation, annotation retention and modeled modules."""
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=json.loads((ROOT/'analysis/spec.json').read_text(encoding='utf-8'))
flat=json.loads((ROOT/'analysis/flat.json').read_text(encoding='utf-8'))
scene=json.loads((ROOT/'web/dist/assets/scene.json').read_text(encoding='utf-8'))

def require(ok, message):
    if not ok: raise SystemExit('FAIL: '+message)

def near(a,b,tol=.002): return abs(a-b)<=tol

texts={e['handle'].upper():e.get('text','') for e in flat['texts']}
for handle,size in [('16595','30x78'),('16597','30x84'),('16599','30x36'),('165AD','30x36')]:
    require(handle in texts and re.search(re.escape(size),texts[handle],re.I),f'text handle {handle} must say {size}')
for handle,part in [('14635','1.00'),('14639','0.00'),('1464D','9.00'),('14651','13.50')]:
    require(handle in texts and part in texts[handle],f'elevation annotation {handle} missing')

arrow=next((e for e in flat['entities'] if e.get('source','').upper()=='/165A6'),None)
require(arrow is not None and len(arrow.get('vertices',[]))==5,'north arrow 165A6 missing')
verts=arrow['vertices'];tip=max(verts,key=lambda p:p[0])
require(tip[0]-max(p[0] for p in verts if p is not tip)>2,'north arrow must point +X')

dims=flat['dimensions']
require(len(dims)==631,'expected all 631 extracted dimensions')
require(any(near(float(d.get('measurement',0)),6,.001) for d in dims),'6 m grid dimension absent')
require(any(near(float(d.get('measurement',0)),78,.001) for d in dims),'78 m dimension absent')
require(len(scene.get('source_annotations',[]))==len(flat['texts']),'source texts not all retained')
require(len(scene.get('source_dimensions',[]))==len(dims),'source dimensions not all retained')

expected=[]
origin=spec['source_origin']
for f in spec['footprints_source']:
    x0,y0,x1,y1=f['bounds']
    expected.append((x0-origin[0],y0-origin[1],x1-origin[0],y1-origin[1]))
actual=[tuple(f['bounds']) for f in scene.get('footprints',[])]
require(len(expected)==len(actual)==6,'expected six warehouse modules')
left=list(actual)
for item in expected:
    found=next((v for v in left if all(near(a,b) for a,b in zip(item,v))),None)
    require(found is not None,f'source footprint not modeled: {item}')
    left.remove(found)
require(not left,'extra modeled warehouse footprint')
require(scene['units']=='metres','scene must use metres')
require(spec['orientation']['north']=='drawing +X','north direction not frozen from the source arrow')
require(spec['source_transform']['elevation_offset_m']==0.0,'source Z transform must be reversible and documented')
require(spec['levels_source']['finished_floor_1']['value_m']==1.0,'finished floor must match +1.00')

motions=scene.get('motions',[])
require(len(motions)==6,'expected six door controls')
for m in motions:
    require(m['kind']=='roll' and m.get('top',0)>0 and m.get('travel',0)>m['bounds'][5],
            'each inferred roller shutter must clear the opening vertically')
    leaves=[e for e in scene['elements'] if e.get('motion')==m['id']]
    require(len(leaves)==1 and leaves[0]['kind']=='box',f'roller shutter must have one moving panel: {m["id"]}')

result={'status':'passed','elements':len(scene['elements']),'footprints':len(actual),
        'motions':len(motions),'source_texts':len(flat['texts']),'source_dimensions':len(dims),
        'north':'drawing +X','grade_m':0.0,'finished_floor_m':1.0,'eave_m':9.0,'ridge_m':13.5}
out=ROOT/'verification/source-scene-checks.json'
out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result))
