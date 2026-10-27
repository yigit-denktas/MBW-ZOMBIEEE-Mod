#!/usr/bin/env python3
"""Generate progress/publish-meta.json for the read-only Pages tracker snapshot."""
from __future__ import annotations
import argparse, hashlib, json, subprocess
from datetime import datetime, timezone
from pathlib import Path

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument('--source-sha')
    a = p.parse_args()
    root = a.root
    ledger = root / 'progress' / 'ledger.json'
    data = json.loads(ledger.read_text(encoding='utf-8'))
    sha = a.source_sha or subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'], text=True).strip()
    meta = {
        'schema': 'zombieee.publish-meta.v1',
        'source_sha': sha,
        'source_short': sha[:7],
        'generated_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'ledger_sha256': hashlib.sha256(ledger.read_bytes().replace(b'\r\n', b'\n')).hexdigest(),
        'work_items': len(data.get('items', [])),
        'policy': 'read-only snapshot generated from reviewed main; not a live feed',
    }
    out = root / 'progress' / 'publish-meta.json'
    out.write_text(json.dumps(meta, indent=2) + '\n', encoding='utf-8')
    print(out)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
