#!/usr/bin/env python3
"""
PyPI Build and Release Helper for TimeMeshin
Builds sdist and wheel, runs integrity checks, and uploads via twine.
"""

import sys
import subprocess
import shutil
from pathlib import Path

def run(cmd):
    print(f"--> {cmd}")
    subprocess.check_call(cmd, shell=True)

def main():
    repo_root = Path(__file__).resolve().parent.parent
    dist_dir = repo_root / "dist"
    build_dir = repo_root / "build"

    print("==========================================================================")
    print("   TimeMeshin - PyPI Build & Release Script                               ")
    print("==========================================================================")

    # Clean old builds
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    if build_dir.exists():
        shutil.rmtree(build_dir)

    # Build distributions
    print("\n[1/3] Building Wheel and Source Distribution...")
    run(f"{sys.executable} -m pip install --upgrade build twine")
    run(f"{sys.executable} -m build")

    # Check artifacts
    print("\n[2/3] Checking distribution artifacts with twine...")
    run(f"{sys.executable} -m twine check dist/*")

    # Publishing instructions
    print("\n[3/3] Build successful! Packages ready in ./dist:")
    for f in dist_dir.glob("*"):
        print(f"  - {f.name} ({f.stat().st_size / 1024:.1f} KB)")

    print("\nTo publish to PyPI:")
    print("  twine upload dist/*")
    print("\nOr to publish to TestPyPI first:")
    print("  twine upload --repository testpypi dist/*")

if __name__ == "__main__":
    main()