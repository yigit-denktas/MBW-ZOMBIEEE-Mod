#!/usr/bin/env python3
"""Publish the reviewed tracker snapshot to a gh-pages worktree.

Copies only the public tracker files plus generated publish metadata. Never
copies README/CHANGELOG (they contain relative links that 404 on Pages).
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from publish_tracker_meta import main as generate_meta


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--gh-pages', type=Path, required=True)
    parser.add_argument('--source-sha')
    parser.add_argument('--commit', action='store_true')
    args = parser.parse_args()

    root = args.root
    pages = args.gh_pages
    sha = args.source_sha or subprocess.check_output(
        ['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
    import sys
    sys.argv = ['publish_tracker_meta.py', '--root', str(root), '--source-sha', sha]
    generate_meta()

    for rel in ('site/index.html', 'progress/ledger.json',
                'progress/live-status.json', 'progress/publish-meta.json'):
        target = pages / (Path(rel).name if rel.startswith('site/') else rel)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / rel, target)

    if args.commit:
        subprocess.check_call(['git', '-C', str(pages), 'add', '-A'])
        subprocess.check_call([
            'git', '-C', str(pages), '-c', 'user.name=yigit-denktas',
            '-c', 'user.email=yigitdenktas@gmail.com', 'commit', '-m',
            'publish: tracker snapshot ' + sha[:7]])
    print(json.dumps({'source_sha': sha, 'gh_pages': str(pages)}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
