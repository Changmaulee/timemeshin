"""
TimeMeshin Document Loader:
Supports parsing .md, .html, .pdf, .json, .jsonl, .csv, and .txt files
into structured text chunks and timestamped event streams.
"""

import io
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class DocumentLoader:
    """Universal multi-format document loader for TimeMeshin."""

    @staticmethod
    def load_file(file_path: str) -> List[Dict[str, Any]]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = path.suffix.lower()

        if ext == ".md":
            return DocumentLoader.load_markdown(path)
        elif ext in [".html", ".htm"]:
            return DocumentLoader.load_html(path)
        elif ext == ".pdf":
            return DocumentLoader.load_pdf(path)
        elif ext in [".json", ".jsonl"]:
            return DocumentLoader.load_json(path)
        elif ext == ".csv":
            return DocumentLoader.load_csv(path)
        else:
            return DocumentLoader.load_text(path)

    @staticmethod
    def load_markdown(path: Path) -> List[Dict[str, Any]]:
        """Parses markdown files, extracting headers and timestamps as event deltas."""
        text = path.read_text(encoding="utf-8", errors="replace")
        lines = text.split("\n")
        events = []
        curr_time = datetime.utcnow()

        for line in lines:
            line_clean = line.strip()
            if not line_clean:
                continue

            # Look for date patterns in markdown (e.g. ## [2026-09-02] or - 2026-09-02:)
            date_match = re.search(r'\b(20\d\d[-/]\d\d[-/]\d\d(?:\s+\d\d:\d\d)?)\b', line_clean)
            if date_match:
                try:
                    d_str = date_match.group(1).replace("/", "-")
                    if len(d_str) == 10:
                        d_str += " 10:00"
                    curr_time = datetime.strptime(d_str, "%Y-%m-%d %H:%M")
                except Exception:
                    pass

            events.append({
                "timestamp": curr_time.strftime("%Y-%m-%d %H:%M"),
                "text": re.sub(r'[#*_`]', '', line_clean) # Strip markdown tags
            })
        return events

    @staticmethod
    def load_html(path: Path) -> List[Dict[str, Any]]:
        """Parses HTML documents, stripping tags and preserving chronological paragraphs."""
        raw_html = path.read_text(encoding="utf-8", errors="replace")
        # Strip script and style tags
        cleaned = re.sub(r'<(script|style).*?</\1>', '', raw_html, flags=re.DOTALL)
        # Extract text within tags
        text_blocks = re.findall(r'>([^<]+)<', cleaned)
        
        events = []
        curr_time = datetime.utcnow()
        for block in text_blocks:
            clean = block.strip()
            if len(clean) > 15: # Filter empty whitespace or tiny fragments
                events.append({
                    "timestamp": curr_time.strftime("%Y-%m-%d %H:%M"),
                    "text": clean
                })
        return events

    @staticmethod
    def load_pdf(path: Path) -> List[Dict[str, Any]]:
        """Extracts text pages from PDF files."""
        events = []
        curr_time = datetime.utcnow()
        
        try:
            # Try pypdf if installed
            import pypdf
            reader = pypdf.PdfReader(str(path))
            for idx, page in enumerate(reader.pages):
                page_text = page.extract_text()
                for line in page_text.split("\n"):
                    clean = line.strip()
                    if len(clean) > 10:
                        events.append({
                            "timestamp": curr_time.strftime("%Y-%m-%d %H:%M"),
                            "text": f"[Page {idx+1}] {clean}"
                        })
        except Exception:
            # Fallback: Extract raw printable ASCII strings from PDF stream
            with open(path, "rb") as f:
                content = f.read()
            strings = re.findall(rb'[\x20-\x7E]{15,}', content)
            for s in strings[:50]:
                try:
                    events.append({
                        "timestamp": curr_time.strftime("%Y-%m-%d %H:%M"),
                        "text": s.decode('latin1', errors='ignore')
                    })
                except Exception:
                    pass

        return events

    @staticmethod
    def load_json(path: Path) -> List[Dict[str, Any]]:
        events = []
        text = path.read_text(encoding="utf-8", errors="replace")
        try:
            data = json.loads(text)
            if isinstance(data, list):
                for item in data:
                    events.append({
                        "timestamp": item.get("timestamp", datetime.utcnow().strftime("%Y-%m-%d %H:%M")),
                        "text": str(item.get("text", item))
                    })
        except Exception:
            # JSON-Lines
            for line in text.split("\n"):
                if line.strip():
                    try:
                        item = json.loads(line)
                        events.append({
                            "timestamp": item.get("created_at", item.get("timestamp", datetime.utcnow().strftime("%Y-%m-%d %H:%M"))),
                            "text": str(item.get("content", item.get("text", line)))
                        })
                    except Exception:
                        pass
        return events

    @staticmethod
    def load_csv(path: Path) -> List[Dict[str, Any]]:
        import csv
        events = []
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            for row in reader:
                if row:
                    events.append({
                        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
                        "text": " | ".join(row)
                    })
        return events

    @staticmethod
    def load_text(path: Path) -> List[Dict[str, Any]]:
        lines = path.read_text(encoding="utf-8", errors="replace").split("\n")
        return [
            {"timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M"), "text": l.strip()}
            for l in lines if l.strip()
        ]
