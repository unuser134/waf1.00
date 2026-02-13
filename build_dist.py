#!/usr/bin/env python3
"""Build a portable distribution ZIP for the DL-WAF project.

Usage:
  python build_dist.py --output dist/waf-1.0.zip

The script collects a curated set of files and directories, writes them
into a zip with relative paths, and sets executable permission bits for
POSIX shell scripts to avoid "can't open" issues on UNIX-like VMs.
"""
import argparse
import os
import time
import zipfile
from pathlib import Path


DEFAULT_OUT = "dist/waf-1.0.zip"


INCLUDE = [
    "main.py",
    "requirements.txt",
    "start-waf.bat",
    "start-waf.sh",
    "deploy.py",
    "README.md",
    "QUICK_START.md",
    "config",
    "src",
    "rules",
    "models",
    "docs",
    "logs",  # Empty directory for log files
]

EXCLUDE_NAMES = {
    ".git",
    ".github",
    ".idea",
    ".vscode",
    ".env",
    "venv",
    ".venv",
    "build",
    "dist",  # exclude existing build outputs to avoid nesting
    "__pycache__",
}

EXCLUDE_SUFFIXES = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".DS_Store",
    ".swp",
    ".tmp",
}


def should_include(path: Path) -> bool:
    # Skip common env/cache/editor artifacts
    parts = set(path.parts)
    if any(p in EXCLUDE_NAMES for p in parts):
        return False
    if path.suffix in EXCLUDE_SUFFIXES:
        return False
    return True


def add_file_to_zip(zf: zipfile.ZipFile, filepath: Path, arcname: str):
    zi = zipfile.ZipInfo(arcname)
    st = filepath.stat()
    # Set a valid DOS date tuple from file mtime to avoid zipfile errors
    mtime = time.localtime(st.st_mtime)
    zi.date_time = tuple(mtime[:6])
    # Preserve file mode for .sh (make executable on unix)
    if arcname.endswith('.sh'):
        zi.external_attr = (0o755 & 0xFFFF) << 16  # rwxr-xr-x
    else:
        # default: rw-r--r-- for files when possible
        zi.external_attr = (0o644 & 0xFFFF) << 16
    with filepath.open('rb') as f:
        data = f.read()
    zf.writestr(zi, data)


def build(output: str):
    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(out_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        root = Path('.').resolve()
        for item in INCLUDE:
            p = (root / item).resolve()
            if not p.exists():
                print(f"Warning: {item} not found, skipping")
                continue

            if p.is_file():
                arc = p.relative_to(root).as_posix()
                add_file_to_zip(zf, p, arc)
                print(f"Added file: {arc}")
            else:
                for dirpath, dirnames, filenames in os.walk(p):
                    dirpath = Path(dirpath)
                    rel_dir = dirpath.relative_to(root).as_posix()
                    # ensure we skip unwanted folders
                    if not should_include(dirpath):
                        continue
                    # add directory entry
                    zf.writestr(rel_dir + '/', b'')
                    for fname in filenames:
                        fpath = dirpath / fname
                        if not should_include(fpath):
                            continue
                        arc = (dirpath / fname).relative_to(root).as_posix()
                        add_file_to_zip(zf, fpath, arc)
                        print(f"Added file: {arc}")

    print(f"Built distribution: {out_path}")

    # Write a SHA256 checksum alongside the zip for integrity verification
    digest = compute_sha256(out_path)
    checksum_path = out_path.with_suffix(out_path.suffix + '.sha256')
    checksum_path.write_text(f"{digest}  {out_path.name}\n", encoding='utf-8')
    print(f"Wrote checksum: {checksum_path}")


def compute_sha256(path: Path) -> str:
    import hashlib

    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--output', '-o', default=DEFAULT_OUT, help='Output zip path')
    return p.parse_args()


def main():
    args = parse_args()
    build(args.output)


if __name__ == '__main__':
    main()
