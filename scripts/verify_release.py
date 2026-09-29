"""Independent release read-back: local native parity and anonymous Pages bytes."""
import hashlib,json,sys,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE='https://bambssquad.github.io/jetis-digital-twin-luna/'
def sha(data): return hashlib.sha256(data).hexdigest()
def read(path): return (ROOT/path).read_bytes()
scene=json.loads(read('web/dist/assets/scene.json'))
native=json.loads(read('verification/native-reopened.json'))
checks={
 'native_reopen_passed':native['passed'],
 'native_scene_count':native['actual']==len(scene['elements']),
 'native_download_identical':sha(read('outputs/model.skp'))==sha(read('web/dist/downloads/model.skp'))==native['sha256'],
 'source_unchanged':sha(read('source/input.dwg'))=='ae5a91924b7a508a76e258c8141cf21c816b6378734217fa413e759cd0848072',
}
receipt={'checks':checks,'scene_sha256':sha(read('web/dist/assets/scene.json')),'native_sha256':native['sha256']}
if '--live' in sys.argv:
 receipt['url']=BASE
 for path in ['index.html','project.json','assets/scene.json','app.js','experience.js','navigation.js','downloads/model.skp']:
  req=urllib.request.Request(BASE+path,headers={'User-Agent':'Jetis-release-verifier'})
  with urllib.request.urlopen(req,timeout=60) as r: body=r.read()
  checks['live_'+path]=sha(body)==sha(read('web/dist/'+path))
receipt['passed']=all(checks.values())
(ROOT/'verification/release-live.json' if '--live' in sys.argv else ROOT/'verification/release-local.json').write_text(json.dumps(receipt,indent=2))
print(json.dumps({'passed':receipt['passed'],'checks':len(checks),'failed':[k for k,v in checks.items() if not v]}))
raise SystemExit(0 if receipt['passed'] else 1)
