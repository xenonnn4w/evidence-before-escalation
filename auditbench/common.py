import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, allow_nan=False).encode()).hexdigest()

def read(path):
    return json.loads(Path(path).read_text())

def write(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + '\n')
    tmp.replace(path)

def lines(path):
    path = Path(path)
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]

def append(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a') as f:
        f.write(json.dumps(obj, sort_keys=True, allow_nan=False) + '\n')
        f.flush()
        os.fsync(f.fileno())

def code_hash():
    paths = sorted((ROOT/'auditbench').glob('*.py')) + sorted((ROOT/'prompts').glob('*.md'))
    paths += sorted((ROOT/'scripts').glob('*.py')) + sorted((ROOT/'scripts').glob('*.sh'))
    paths += [ROOT/name for name in ['pyproject.toml','uv.lock','docs/PROTOCOL.md'] if (ROOT/name).exists()]
    return digest({str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})

def config():
    return read(ROOT/'configs/core.json')
