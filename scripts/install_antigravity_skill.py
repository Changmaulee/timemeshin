#!/usr/bin/env python3
"""
Antigravity Skill Installer for TimeMeshin
Installs the TimeMeshin skill and plugin bundle into the local Antigravity environment.
"""

import sys
from pathlib import Path

# Add parent directory to path
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

from timemeshin.cli import install_skill

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Install TimeMeshin skill into Antigravity")
    parser.add_argument("--project", action="store_true", help="Install into current project's .agents/ directory")
    parser.add_argument("--path", type=str, default=None, help="Custom installation directory")
    args = parser.parse_args()

    print("==========================================================================")
    print("   TimeMeshin - Antigravity Global Skill & Plugin Installer               ")
    print("==========================================================================")
    install_skill(global_install=not args.project, target_dir=args.path)