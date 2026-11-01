"""Build an explicit public-source ZIP and standalone semantic entry."""
import argparse
import hashlib
import json
import re
from pathlib import Path
import tomllib
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FILES = '''.gitattributes .gitignore .github/workflows/tests.yml AGENTS.md
ARCHITECTURE.md BOOT.md CHANGELOG.md COMPETENCES.md CONCEPTS.md KERNEL.md
LICENSE README.md README.it.md docs/VALIDATION.md lab.py pyproject.toml
src/lab_kernel/__init__.py src/lab_kernel/engine.py src/lab_kernel/cli.py
src/lab_kernel/kernel/AGENTS.md src/lab_kernel/kernel/BOOT.md
src/lab_kernel/kernel/KERNEL.md src/lab_kernel/kernel/CONCEPTS.md
src/lab_kernel/kernel/COMPETENCES.md tools/sync_kernel.py tools/build_release.py
tests/fixture_bridge.py tests/test_lab.py examples/system.json'''.split()
GUIDES = ('AGENTS.md','BOOT.md','KERNEL.md','CONCEPTS.md','COMPETENCES.md')


def sha(value):
    return hashlib.sha256(value).hexdigest()


def build(*, require_wheel=False):
    version = tomllib.loads((ROOT/'pyproject.toml').read_text(encoding='utf-8'))['project']['version']
    contents = {name:(ROOT/name).read_bytes() for name in FILES}
    for name in GUIDES:
        assert contents[name] == contents['src/lab_kernel/kernel/'+name], name
    for name,data in contents.items():
        if re.search(rb'(?:gh[pousr]_|github_pat_)[A-Za-z0-9_]{24,}',data):
            raise ValueError('credential-shaped content: '+name)
    manifest = {'schema':'dnd.lab.distribution.v1','name':'Lab','version':version,
                'status':'public_alpha_release','license':'MIT',
                'files':{name:{'bytes':len(data),'sha256':sha(data)} for name,data in sorted(contents.items())}}
    output=ROOT/'dist'
    wheel=output/('dnd_lab_kernel-'+version+'-py3-none-any.whl')
    if require_wheel and not wheel.is_file():
        raise ValueError('release_wheel_required')
    if wheel.is_file():
        with zipfile.ZipFile(wheel) as packaged:
            if packaged.testzip() is not None:
                raise ValueError('release_wheel_corrupt')
            for name,data in contents.items():
                if name.startswith('src/lab_kernel/'):
                    member=name.removeprefix('src/')
                    if member not in packaged.namelist() or packaged.read(member)!=data:
                        raise ValueError('wheel_source_mismatch: '+member)
    output.mkdir(exist_ok=True)
    manifest_bytes=(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    archive=output/('lab-kernel-'+version+'.zip')
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,data in sorted({**contents,'MANIFEST.json':manifest_bytes}.items()):
            info=zipfile.ZipInfo('lab-kernel/'+name,date_time=(2026,10,31,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
            z.writestr(info,data)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert len(z.namelist())==len(FILES)+1
        for name,row in manifest['files'].items():
            assert sha(z.read('lab-kernel/'+name))==row['sha256'],name
    single=output/('lab-kernel-'+version+'.md')
    single.write_text('# Lab — semantic kernel '+version+'\n\nMIT License.\n\n'+
                      '\n\n'.join(contents[name].decode('utf-8') for name in GUIDES),
                      encoding='utf-8',newline='\n')
    (output/('MANIFEST-'+version+'.json')).write_bytes(manifest_bytes)
    assets=[archive,single,output/('MANIFEST-'+version+'.json')]
    if wheel.is_file():
        assets.append(wheel)
    (output/('SHA256SUMS-'+version)).write_text(''.join(sha(p.read_bytes())+'  '+p.name+'\n' for p in assets),encoding='utf-8',newline='\n')
    print(json.dumps({'version':version,'license':'MIT','source_files':len(FILES),
                      'zip_sha256':sha(archive.read_bytes()),'zip_bytes':archive.stat().st_size},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--require-wheel',action='store_true',
                        help='Require a built, source-matching wheel for a complete release')
    build(require_wheel=parser.parse_args().require_wheel)
