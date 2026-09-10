"""
TimeMeshin Level 4: OS Kernel & File/Process I/O Tracing Engine
Monitors real-time filesystem mutations, terminal command executions, compiler builds, and process lifecycles.
"""

import os
import sys
import time
import subprocess
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

class FileSystemWatcher:
    """Monitors directory trees for file creations, modifications, and deletions."""

    def __init__(self, watch_paths: Optional[Any] = None, watch_path: Optional[str] = None):
        if watch_path:
            paths = [watch_path]
        elif watch_paths:
            if isinstance(watch_paths, (str, Path)):
                paths = [watch_paths]
            else:
                paths = list(watch_paths)
        else:
            paths = [Path.cwd()]
        self.watch_paths = [Path(p) for p in paths]
        self.file_snapshots = {}
        self.recent_events_log = []
        try:
            self.poll_initial_state()
        except Exception:
            pass

    def _hash_file(self, p: Path) -> str:
        try:
            if p.is_file() and p.stat().st_size < 10 * 1024 * 1024: # < 10MB
                return hashlib.sha256(p.read_bytes()).hexdigest()[:16]
        except Exception:
            pass
        return ""

    def poll_initial_state(self):
        for wp in self.watch_paths:
            if wp.exists():
                for f in wp.rglob("*"):
                    if f.is_file() and not any(part.startswith(".") for part in f.parts):
                        self.file_snapshots[str(f)] = {
                            "mtime": f.stat().st_mtime,
                            "hash": self._hash_file(f)
                        }

    def check_mutations(self) -> List[Dict[str, Any]]:
        mutations = []
        now_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        current_files = set()

        for wp in self.watch_paths:
            if not wp.exists():
                continue
            for f in wp.rglob("*"):
                if f.is_file() and not any(part.startswith(".") or part == "__pycache__" for part in f.parts):
                    f_str = str(f)
                    current_files.add(f_str)
                    
                    try:
                        mtime = f.stat().st_mtime
                        if f_str not in self.file_snapshots:
                            # File Created
                            f_hash = self._hash_file(f)
                            self.file_snapshots[f_str] = {"mtime": mtime, "hash": f_hash}
                            mutations.append({
                                "type": "FILE_CREATED",
                                "filepath": f_str,
                                "timestamp": now_ts,
                                "size_bytes": f.stat().st_size,
                                "hash": f_hash
                            })
                        elif self.file_snapshots[f_str]["mtime"] != mtime:
                            # File Modified
                            new_hash = self._hash_file(f)
                            if new_hash != self.file_snapshots[f_str]["hash"]:
                                self.file_snapshots[f_str] = {"mtime": mtime, "hash": new_hash}
                                mutations.append({
                                    "type": "FILE_MODIFIED",
                                    "filepath": f_str,
                                    "timestamp": now_ts,
                                    "size_bytes": f.stat().st_size,
                                    "new_hash": new_hash
                                })
                    except Exception:
                        pass

        # Check for deleted files
        for old_f in list(self.file_snapshots.keys()):
            if old_f not in current_files:
                del self.file_snapshots[old_f]
                mutations.append({
                    "type": "FILE_DELETED",
                    "filepath": old_f,
                    "timestamp": now_ts
                })

        return mutations

    def get_recent_events(self, limit: int = 25) -> List[Dict[str, Any]]:
        muts = self.check_mutations()
        if muts:
            for m in muts:
                self.recent_events_log.insert(0, {
                    "timestamp": m.get("timestamp", datetime.now().strftime("%H:%M:%S")),
                    "type": m.get("type", "FILE_EVENT"),
                    "path": Path(m.get("filepath", "")).name or m.get("filepath", ""),
                    "status": "DETECTED"
                })
            self.recent_events_log = self.recent_events_log[:100]
        if not self.recent_events_log:
            return [{
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "type": "FS_WATCHER_ACTIVE",
                "path": "Active workspace listener",
                "status": "MONITORING"
            }]
        return self.recent_events_log[:limit]


class ProcessCommandTracer:
    """Tracks executed terminal commands, process exit codes, and build runtimes."""

    @staticmethod
    def trace_command_execution(command: str, cwd: Optional[str] = None) -> Dict[str, Any]:
        start_time = datetime.now()
        ts_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
        try:
            res = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=cwd, timeout=30)
            dur = (datetime.now() - start_time).total_seconds()
            return {
                "command": command,
                "timestamp": ts_str,
                "exit_code": res.returncode,
                "duration_seconds": round(dur, 3),
                "stdout_snippet": res.stdout[:200] if res.stdout else "",
                "stderr_snippet": res.stderr[:200] if res.stderr else "",
                "status": "SUCCESS" if res.returncode == 0 else "FAILED"
            }
        except Exception as e:
            return {
                "command": command,
                "timestamp": ts_str,
                "exit_code": -1,
                "duration_seconds": 0,
                "error": str(e),
                "status": "ERROR"
            }
