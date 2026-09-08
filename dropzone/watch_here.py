#!/usr/bin/env python3
"""
Portable TimeMeshin Dropzone Runner
Works anywhere this folder is copied!
"""
import os
import sys
import webbrowser
from pathlib import Path

# Add project root to sys.path if not installed
current_dir = Path(__file__).resolve().parent
repo_root = current_dir.parent
sys.path.insert(0, str(repo_root))

try:
    from timemeshin.ingestion.folder_watcher import FolderWatcher
except ImportError:
    print("TimeMeshin package not found. Installing locally...")
    os.system(f"{sys.executable} -m pip install --user -e {repo_root}")
    from timemeshin.ingestion.folder_watcher import FolderWatcher

if __name__ == "__main__":
    db_path = str(current_dir / "timeline_memory.db")
    matrix_json = str(current_dir / "matrix_data.json")
    html_viewer = current_dir / "spatio_temporal_matrix.html"

    print("==========================================================================")
    print("   TimeMeshin Portable Dropzone Watcher                                   ")
    print(f"   Folder: {current_dir}                                                  ")
    print("==========================================================================")

    watcher = FolderWatcher(
        watch_dir=str(current_dir),
        db_path=db_path,
        matrix_output_path=matrix_json
    )

    # Initial scan of folder
    print("[*] Performing initial scan of chat files...")
    watcher.scan_once()

    # Automatically open visual matrix if HTML exists
    if html_viewer.exists():
        print(f"[*] Opening visual matrix UI in browser: {html_viewer.name}")
        webbrowser.open(html_viewer.as_uri())

    print("\n[+] Continuously watching for new chats (.html, .pdf, .md, .txt, .json)...")
    print("    Drag and drop any chat file into this folder to align its timeline!")
    print("    Press Ctrl+C to stop.\n")
    watcher.watch_continuous(interval_sec=2.0)