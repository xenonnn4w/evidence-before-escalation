"""Create a portable source/data archive, never model weights, secrets or environments."""
import hashlib
import tarfile
from pathlib import Path
root=Path(__file__).resolve().parent.parent
output=root.parent/'evidence-before-escalation-ready.tar.gz'
allowed_dirs=['auditbench','tests','scripts','configs','prompts','docs','reports','planning','data','verification']
files=[root/name for name in ['README.md','pyproject.toml','uv.lock','.gitignore']]
for name in allowed_dirs:
    files.extend(p for p in (root/name).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc')
with tarfile.open(output,'w:gz') as archive:
    for p in sorted(files):archive.add(p,arcname=str(Path(root.name)/p.relative_to(root)),recursive=False)
sha=hashlib.sha256(output.read_bytes()).hexdigest()
output.with_suffix(output.suffix+'.sha256').write_text(sha+'  '+output.name+'\n')
print(output);print('SHA256',sha);print('Bytes',output.stat().st_size)
