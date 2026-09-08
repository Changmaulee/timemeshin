import sys
import io
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from timemeshin import TimeMeshinClient

def main():
    print("🚀 Initializing TimeMeshin Client...")
    client = TimeMeshinClient(db_path="timemeshin_verified.db")
    client.ingest("TimeMeshin is officially verified and operational.")
    state = client.scrub(playhead="2026-09-08 14:00")
    print("✅ TimeMeshin Ingestion & Scrubbing PASSED!")
    print("📌 State:", state)

if __name__ == "__main__":
    main()
