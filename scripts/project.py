"""Initialize, configure and check a DWG twin project. No CAD inference is implied."""
import argparse, hashlib, json, math, re, shutil
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p, value):
    p=Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def vector(v,n=3): return isinstance(v,list) and len(v)==n and all(isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x) for x in v)
def require(condition, message):
    if not condition: raise ValueError(message)
def configure(root, spec):
    require(spec.get('units')=='metres','Scene units must be metres')
    require(spec.get('source_unit_to_m',0)>0,'Resolve source units before configuration')
    require(len(spec.get('unit_evidence',[]))>=2,'Two independent dimension checks required')
    require(vector(spec.get('source_origin')),'source_origin required')
    lo,hi=spec['bounds']['min'],spec['bounds']['max']
    require(vector(lo) and vector(hi) and all(b>a for a,b in zip(lo,hi)),'Invalid 3D bounds')
    require(vector(spec.get('spawn')),'Spawn must be in source XYZ metres')
    b=spec.get('walk_bounds'); require(vector(b,4) and b[0]<b[1] and b[2]<b[3],'Invalid walk bounds [xmin,xmax,ymin,ymax]')
    x,y,z=spec['spawn'];require(b[0]<=x<=b[1] and b[2]<=y<=b[3],'Spawn outside walk bounds')
    c=[(a+b)/2 for a,b in zip(lo,hi)]; span=max(b-a for a,b in zip(lo,hi))
    views={'overview':{'eye':[c[0]+span,c[1]+span,c[2]+span*.8],'target':c,'title':'Keseluruhan tapak','detail':'Model berdasarkan DWG proyek'},'top':{'eye':[c[0],c[1]+.01,hi[2]+span*1.5],'target':c,'title':'Denah tapak','detail':'Susunan bangunan'}}
    views.update(spec.get('views',{}))
    for v in views.values(): require(vector(v.get('eye')) and vector(v.get('target')) and v['eye']!=v['target'],'Invalid view')
    cfg=read(root/'web/dist/project.json');cfg.update(spec);cfg.update(views=views,center=c,span=span,status='configured')
    write(root/'analysis/spec.json',spec);write(root/'web/dist/project.json',cfg)

def init(source,root,name):
    source=source.resolve(); root=root.resolve()
    require(source.is_file() and source.suffix.lower()=='.dwg','A readable DWG is required')
    require(not root.exists(),'Output must be a NEW directory; existing work is preserved')
    slug=re.sub(r'[^a-z0-9]+','-',name.lower()).strip('-')
    require(bool(slug),'Use a project name containing letters or numbers')
    root.mkdir(parents=True)
    for d in ['source','analysis','scripts','outputs','verification']: (root/d).mkdir()
    shutil.copy2(source,root/'source/input.dwg')
    shutil.copytree(SKILL/'assets/viewer',root/'web/dist')
    (root/'web/dist/downloads').mkdir(exist_ok=True)
    for n in ['build_native.rb','audit_native.rb']: shutil.copy2(SKILL/'assets'/n,root/'scripts'/n)
    shutil.copytree(SKILL/'assets/github',root/'.github')
    manifest={'name':name,'slug':slug,'source_filename':source.name,'source_sha256':digest(source),'publication':'new-public-github-repository-and-pages','status':'awaiting-drawing-analysis'}
    write(root/'project-manifest.json',manifest)
    write(root/'web/dist/project.json',dict(manifest,download='downloads/model.skp'))
    write(root/'web/dist/assets/scene.json',{'units':'metres','materials':{},'elements':[],'motions':[],'labels':[],'lights':[],'footprints':[],'assumptions':[]})
    (root/'STATE.md').write_text('# '+name+'\n\n- Source copied and SHA-256 recorded; original unchanged.\n- Awaiting unit/dimension analysis; no building geometry generated.\n- Full exterior, interior and site; missing design details may be inferred and logged.\n- New public repository and GitHub Pages authorized by Bam, 2026-09-29.\n- Native SKP and live web verification pending.\n',encoding='utf-8')
    (root/'.gitignore').write_text('.env\n.env.*\n!.env.example\nnode_modules/\n__pycache__/\n*.log\nverification/\n',encoding='utf-8')
    require(digest(source)==manifest['source_sha256'],'Source changed while copying')
    require(digest(root/'source/input.dwg')==manifest['source_sha256'],'Copy hash mismatch')

def validate(root):
    cfg=read(root/'web/dist/project.json'); s=read(root/'web/dist/assets/scene.json')
    require(cfg.get('status')=='configured','Project awaits drawing analysis')
    require(s.get('units')=='metres' and len(s.get('elements',[]))>0,'Empty or non-metric scene')
    require(digest(root/'source/input.dwg')==read(root/'project-manifest.json')['source_sha256'],'Source copy changed')
    ids=set(); motions={}
    for m in s.get('motions',[]):
        require(m['id'] not in motions,'Duplicate motion ID');motions[m['id']]=m
        require(m.get('kind') in ['slide','splitSlide','roll'],'Unknown motion')
        require(vector(m.get('bounds'),6) and all(v>0 for v in m['bounds'][3:]) and vector(m.get('anchor')),'Invalid motion bounds/anchor')
        if m['kind']=='slide': require(vector(m.get('delta')),'Invalid slide delta')
        else: require(m.get('travel',0)>0,'Invalid travel')
        if m['kind']=='splitSlide': require(len(m.get('leaves',[]))==2 and all(vector(b,6) and all(v>0 for v in b[3:]) for b in m['leaves']),'Two leaf bounds required')
        if m['kind']=='roll': require(isinstance(m.get('top'),(int,float)),'Roll top required')
    for e in s['elements']:
        require(e.get('id') and e['id'] not in ids,'Missing/duplicate element ID');ids.add(e['id'])
        require(e.get('mat') in s['materials'] and e.get('group') and e.get('name'),'Missing material/group/name')
        k=e.get('kind');require(k in ['box','beam','wf','cnp','cylinder','wheel','sphere','prism'],'Unsupported primitive')
        if k in ['box','sphere']: require(vector(e.get('p')) and vector(e.get('s')) and all(v>0 for v in e['s']),'Invalid box/sphere')
        if k in ['cylinder','wheel']: require(vector(e.get('p')) and e.get('r',0)>0 and e.get('h' if k=='cylinder' else 'd',0)>0,'Invalid round solid')
        if k in ['beam','wf','cnp']:
            require(vector(e.get('a')) and vector(e.get('b')) and e['a']!=e['b'] and e.get('w',0)>0 and e.get('h',0)>0,'Invalid beam')
            if k!='beam': require(0<e.get('tw',0)<e['w'] and 0<e.get('tf',0)<e['h']/2,'Invalid steel thickness')
        if k=='prism': require(len(e.get('points',[]))>=3 and all(vector(p) for p in e['points']) and e.get('th',0)>0 and not e.get('motion'),'Invalid or moving prism')
        if e.get('motion'):
            require(e['motion'] in motions,'Missing motion definition')
            if motions[e['motion']]['kind']=='splitSlide': require(e.get('slideSide') in [-1,1],'Missing slide side')
            if motions[e['motion']]['kind']=='roll': require(k=='box','Rolling parts must be boxes')
        require(e.get('collision') in [None,'floor','wall','none'],'Invalid collision role')
    for mat in s['materials'].values():
        if mat.get('texture'):
            require(re.fullmatch(r'[A-Za-z0-9_-]+',mat['texture']) is not None,'Unsafe texture ID')
            for folder in ['textures','textures-1k']:
                for channel in ['Color','NormalGL','Roughness']: require((root/'web/dist/assets'/folder/(mat['texture']+'_'+channel+'.jpg')).is_file(),'Missing texture map')
    return {'status':'passed','elements':len(ids),'motions':len(motions),'scope':'Scene contract only; drawing, native SKP and browser checks remain required'}

def main():
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest='cmd',required=True)
    a=sub.add_parser('init');a.add_argument('--dwg',required=True,type=Path);a.add_argument('--out',required=True,type=Path);a.add_argument('--name',required=True)
    a=sub.add_parser('configure');a.add_argument('--project',required=True,type=Path);a.add_argument('--spec',required=True,type=Path)
    a=sub.add_parser('validate');a.add_argument('--project',required=True,type=Path)
    args=p.parse_args()
    try:
        if args.cmd=='init': init(args.dwg,args.out,args.name); print('Initialized new project; CAD analysis pending.')
        elif args.cmd=='configure': configure(args.project,read(args.spec)); print('Project configuration saved.')
        else:
            report=validate(args.project);write(args.project/'verification/contract.json',report);print(report['scope']+' PASS')
    except (ValueError,KeyError,OSError) as ex: p.exit(1,'CHECK FAILED: '+str(ex)+'\n')
if __name__=='__main__': main()
