import os
import zipfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
EXCLUDE_DIRS = {'.git', 'dist', 'build', 'SpriteStitcher-Release', '__pycache__', 'venv', '.venv'}

def should_exclude(path):
    parts = set(path.split(os.sep))
    if parts & EXCLUDE_DIRS:
        return True
    if path.endswith('.zip'):
        return True
    return False

def make_source_zip():
    out = os.path.join(ROOT, 'SourceCode.zip')
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for foldername, subfolders, filenames in os.walk(ROOT):
            # skip excluded folders
            rel = os.path.relpath(foldername, ROOT)
            if rel == '.':
                rel = ''
            if should_exclude(rel):
                # don't descend into these dirs
                subfolders[:] = []
                continue
            for fn in filenames:
                filepath = os.path.join(foldername, fn)
                if should_exclude(os.path.relpath(filepath, ROOT)):
                    continue
                arcname = os.path.relpath(filepath, ROOT)
                z.write(filepath, arcname)
    print('Created', out)
    return out


def make_exe_zip():
    exe_path = os.path.join(ROOT, 'dist', 'SpriteStitcher.exe')
    out = os.path.join(ROOT, 'SpriteStitcher-Exe.zip')
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        if os.path.exists(exe_path):
            z.write(exe_path, os.path.join('dist', 'SpriteStitcher.exe'))
        # include README for users
        readme = os.path.join(ROOT, 'README.md')
        if os.path.exists(readme):
            z.write(readme, 'README.md')
    print('Created', out)
    return out

if __name__ == '__main__':
    make_source_zip()
    make_exe_zip()
