#!/usr/bin/env python3
"""校验版本、发布白名单与 SHA-256，仅提取构建镜像必须的文件。"""
import argparse
import hashlib
import json
import re
import shutil
import stat
import tarfile
import zipfile
from pathlib import Path

NUMBER = r'(?:0|[1-9][0-9]*)'
TAG = re.compile(rf'v({NUMBER})\.({NUMBER})\.({NUMBER})-upstream\.({NUMBER})\.({NUMBER})\.({NUMBER})\Z')
PLATFORMS = ('darwin_amd64', 'darwin_arm64', 'linux_amd64', 'linux_arm64', 'windows_amd64')
PRICING = 'backend/resources/model-pricing/model_prices_and_context_window.json'
COMMON = {'LICENSE', 'README.md', 'deploy/docker-entrypoint.sh', PRICING}

def version(tag):
    match = TAG.fullmatch(tag)
    if not match:
        raise ValueError('Invalid combined release tag')
    return tuple(map(int, match.groups()))

def archive_names(tag):
    version(tag)
    return {f'sub2api_{tag[1:]}_{p}.{"zip" if p.startswith("windows") else "tar.gz"}' for p in PLATFORMS}

def digest(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()

def checksum_map(directory, tag):
    expected = archive_names(tag)
    checks = {}
    for line in (directory / 'checksums.txt').read_text().splitlines():
        match = re.fullmatch(r'([0-9a-f]{64})  (\S+)', line)
        if not match or match[2] not in expected or match[2] in checks:
            raise ValueError('Invalid or duplicate checksum entry')
        checks[match[2]] = match[1]
    if set(checks) != expected:
        raise ValueError('Incomplete checksum manifest')
    return checks

def validate_archive(path):
    binary = 'sub2api.exe' if path.suffix == '.zip' else 'sub2api'
    expected = COMMON | {binary}
    seen = set()
    total = 0
    if path.suffix == '.zip':
        with zipfile.ZipFile(path) as archive:
            entries = [(m.filename, m.file_size, not m.is_dir() and
                        stat.S_IFMT(m.external_attr >> 16) in (0, stat.S_IFREG))
                       for m in archive.infolist()]
    else:
        with tarfile.open(path) as archive:
            entries = [(m.name, m.size, m.isfile()) for m in archive.getmembers()]
    for name, size, regular in entries:
        if not regular or name not in expected or name in seen or size < 1:
            raise ValueError(f'Archive contains unexpected, duplicate or unsafe member: {name}')
        seen.add(name)
        total += size
    if seen != expected or total > 512 * 1024 * 1024:
        raise ValueError('Archive missing required members or exceeds size limit')

def validate(directory, tag):
    checks = checksum_map(directory, tag)
    for name, expected in checks.items():
        path = directory / name
        if path.is_symlink() or digest(path) != expected:
            raise ValueError(f'Archive checksum mismatch: {name}')
        validate_archive(path)
    return checks

def prepare(directory, tag, output):
    validate(directory, tag)
    for arch in ('amd64', 'arm64'):
        with tarfile.open(directory / f'sub2api_{tag[1:]}_linux_{arch}.tar.gz') as archive:
            for name in ('sub2api', PRICING, 'deploy/docker-entrypoint.sh'):
                # 不使用 extractall；白名单已拒绝链接、绝对路径和目录穿越。
                target = output / arch / name
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.extractfile(name) as source, target.open('wb') as dest:
                    shutil.copyfileobj(source, dest)
                target.chmod(0o755 if name in ('sub2api', 'deploy/docker-entrypoint.sh') else 0o644)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['validate', 'prepare', 'latest'])
    parser.add_argument('--tag', required=True)
    parser.add_argument('--directory', type=Path, default=Path('artifacts'))
    parser.add_argument('--output', type=Path, default=Path('context'))
    args = parser.parse_args()
    current = version(args.tag)
    if args.command == 'latest':
        releases = json.loads((args.directory / 'published.json').read_text())
        versions = [version(r['tag_name']) for r in releases if not r['draft'] and
                    not r['prerelease'] and TAG.fullmatch(r['tag_name'])]
        print(str(not versions or current > max(versions)).lower())
    elif args.command == 'prepare':
        prepare(args.directory, args.tag, args.output)
    else:
        validate(args.directory, args.tag)

if __name__ == '__main__':
    main()
