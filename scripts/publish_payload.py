"""Parent coordinator utility: bounded payloads for authenticated GitHub connector."""
import base64,hashlib,json,sys,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
INDEX=ROOT/'verification/publish-index.json'
if sys.argv[1]=='index':
    files=[]
    for folder in ['web/dist','source','scripts','.github','outputs','analysis','tests','docs','verification']:
        for p in (ROOT/folder).rglob('*'):
            if not p.is_file() or '__pycache__' in p.parts or p.suffix in ['.log','.pyc','.skb']:continue
            if folder=='analysis' and p.name not in ['spec.json','summary.json','overview.png','drawing-evidence.json']:continue
            if folder=='outputs' and p.suffix.lower() not in ['.png','.md']:continue
            if folder=='verification' and p.name not in ['browser-local.json','browser-live.json','door-render.json','contract.json','source-scene-checks.json','native-build.json','native-reopened.json','native-dimensions.json','navigation.json','release-local.json','release-live.json','loop-status.json','loop-status.md']:continue
            files.append(p)
    files += [ROOT/p for p in ['README.md','STATE.md','project-manifest.json','.gitignore'] if (ROOT/p).is_file()]
    rows=[]
    for p in sorted(set(files)):
        data=p.read_bytes(); path=p.relative_to(ROOT).as_posix()
        assert not any(x in path for x in ['.env','.openai','credential'])
        if p.suffix in ['.py','.js','.json','.yml','.md','.html','.rb']:
            text=data.decode('utf-8-sig')
            assert not re.search(r'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|sk-[A-Za-z0-9]{30,})',text), 'Possible secret in '+path
        rows.append({'path':path,'bytes':len(data),'sha':hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()})
    INDEX.write_text(json.dumps(rows),encoding='utf-8');print(json.dumps(rows))
elif sys.argv[1]=='chunk':
    rows=json.loads(INDEX.read_text()); row=rows[int(sys.argv[2])]; p=ROOT/row['path'];offset=int(sys.argv[3]);length=int(sys.argv[4])
    with p.open('rb') as f:f.seek(offset);data=f.read(length)
    print(base64.b64encode(data).decode('ascii'))
