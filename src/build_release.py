"""Build the mod's two .rpyc files using the installed game's Ren'Py engine."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from zipfile import ZipFile, ZIP_DEFLATED


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-root', type=Path, default=Path(r'C:\GOG Games\Lust Theory - Season 1'))
    args = parser.parse_args()
    source = Path(__file__).resolve().parent
    repo = source.parent
    engine = args.game_root.resolve()
    python = engine/'lib/py3-windows-x86_64/python.exe'
    bootstrap = engine/'LustTheoryS1.py'
    if not python.is_file() or not bootstrap.is_file():
        raise SystemExit('The installed 64-bit Ren\'Py game runtime was not found.')
    spec = importlib.util.spec_from_file_location('installer', source/'install_access.py')
    installer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(installer)
    version = installer.VERSION
    scripts = ('lt_access.rpy', 'lt_access_menu.rpy')
    release = repo/'rlease'/('LT_Access_'+version)
    release.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.build-', dir=source) as temporary:
        staging = Path(temporary).resolve()
        assert staging.is_relative_to(source)
        game = staging/'game'
        game.mkdir()
        for name in scripts:
            shutil.copy2(source/name, game/name)
        if (engine/'game/script_version.txt').is_file():
            shutil.copy2(engine/'game/script_version.txt', game/'script_version.txt')
        command = [str(python), str(bootstrap), str(staging), 'compile', '--savedir', str(staging/'saves')]
        result = subprocess.run(command, cwd=engine, text=True, capture_output=True)
        if result.returncode:
            details = (result.stdout+result.stderr)[-6000:]
            if (staging/'errors.txt').exists():
                details += (staging/'errors.txt').read_text(encoding='utf-8')[-6000:]
            raise SystemExit('Ren\'Py compilation failed:\n'+details)
        log = (staging/'log.txt').read_text(encoding='utf-8')
        if "Ren'Py 8.1.3." not in log:
            raise SystemExit('This release is validated against Ren\'Py 8.1.3; use that runtime.')
        for name in scripts:
            compiled = (game/name).with_suffix('.rpyc')
            if not compiled.is_file():
                raise SystemExit('Missing compiled script: '+compiled.name)
            shutil.copy2(compiled, release/compiled.name)
    for name in ('install_access.py', 'Install.cmd', 'Uninstall.cmd'):
        shutil.copy2(source/name, release/name)
    shutil.copy2(repo/'README.md', release/'README.md')
    shutil.copy2(repo/'LICENSE', release/'LICENSE.txt')
    files = [name.replace('.rpy', '.rpyc') for name in scripts] + [
        'install_access.py', 'Install.cmd', 'Uninstall.cmd', 'README.md', 'LICENSE.txt']
    info = {'version':version, 'engine':"Ren'Py 8.1.3.23091805", 'format':'Ren\'Py bytecode (.rpyc)',
            'files':{name:hashlib.sha256((release/name).read_bytes()).hexdigest() for name in files}}
    (release/'build-info.json').write_text(json.dumps(info,indent=2)+'\n',encoding='utf-8',newline='\n')
    files.append('build-info.json')
    archive = release.parent/(release.name+'.zip')
    with ZipFile(archive,'w',ZIP_DEFLATED) as bundle:
        for name in files:
            bundle.write(release/name, release.name+'/'+name)
    with ZipFile(archive) as bundle:
        assert bundle.testzip() is None
    archive.with_suffix('.zip.sha256').write_text(hashlib.sha256(archive.read_bytes()).hexdigest()+'  '+archive.name+'\n',encoding='ascii',newline='\n')
    print('Compiled both mod scripts and built '+str(archive))
    print('No game scripts, assets, archives, DLLs, or saves are included.')


if __name__ == '__main__':
    main()
