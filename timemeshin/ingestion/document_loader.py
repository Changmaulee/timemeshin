"""
Bulletproof DocumentLoader supporting raw text, HTML, Markdown, PDF, JSON, CSV.
Handles malformed HTML, missing tags, various encodings, and string paths.
"""

import html
import io
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class DocumentLoader:
    """Universal multi-format document loader for TimeMeshin."""

    @staticmethod
    def load_file(file_path: Union[str, Path]) -> List[Dict[str, Any]]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = path.suffix.lower()

        if ext in [".html", ".htm"]:
            return DocumentLoader.load_html(path)
        elif ext == ".md":
            return DocumentLoader.load_markdown(path)
        elif ext == ".pdf":
            return DocumentLoader.load_pdf(path)
        elif ext in [".json", ".jsonl"]:
            return DocumentLoader.load_json(path)
        elif ext == ".csv":
            return DocumentLoader.load_csv(path)
        else:
            return DocumentLoader.load_text(path)

    @staticmethod
    def load_html(file_path: Union[str, Path]) -> List[Dict[str, Any]]:
        """Robust HTML extractor that handles malformed tags, scripts, and entities."""
        path = Path(file_path)
        try:
            raw_html = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            with open(path, "rb") as f:
                raw_html = f.read().decode("latin1", errors="ignore")

        # 1. Remove script, style, SVG, and comment blocks
        cleaned = re.sub(r'<(script|style|svg|head).*?</\1>', ' ', raw_html, flags=re.DOTALL | re.IGNORECASE)
        cleaned = re.sub(r'<!--.*?-->', ' ', cleaned, flags=re.DOTALL)
        
        # 2. Convert <br>, <p>, <div>, <li>, <h1>-<h6> to newlines
        cleaned = re.sub(r'<(br|p|div|li|tr|h[1-6])[^>]*>', '\n', cleaned, flags=re.IGNORECASE)
        
        # 3. Strip all remaining HTML tags
        cleaned = re.sub(r'<[^>]+>', ' ', cleaned)
        
        # 4. Unescape HTML entities (e.g., &amp; -> &, &lt; -> <)
        unescaped = html.unescape(cleaned)

        # 5. Extract meaningful lines (filtering out pure box-drawing borders)
        events = []
        curr_time = datetime.utcnow()
        box_drawing_pattern = re.compile(r'[\u2500-\u257F\u2580-\u259F\u25A0-\u25FF\u2014\u2013\u2015\u2550-\u256C═│─┌┐└┘├┤┬┴┼━║—–―¯_\|\+\=\<\>\^▲▼►◄~`#*]')
        
        for line in unescaped.split("\n"):
            clean_line = re.sub(r'\s+', ' ', line).strip()
            # Test how many alphanumeric characters exist
            alpha_count = len(re.findall(r'[a-zA-Z0-9]', clean_line))
            if alpha_count >= 3:
                # Clean stray box chars from edges
                stripped_box = box_drawing_pattern.sub(' ', clean_line)
                stripped_box = re.sub(r'\s+', ' ', stripped_box).strip()
                if len(stripped_box) >= 3:
                    events.append({
                        "timestamp": curr_time.strftime("%Y-%m-%d %H:%M"),
                        "text": stripped_box
                    })
        
        if not events and unescaped.strip():
            fallback = box_drawing_pattern.sub(' ', unescaped.strip())
            events.append({
                "timestamp": curr_time.strftime("%Y-%m-%d %H:%M"),
                "text": re.sub(r'\s+', ' ', fallback).strip()[:300]
            })

        return events

    @staticmethod
    def load_markdown(file_path: Union[str, Path]) -> List[Dict[str, Any]]:
        path = Path(file_path)
        text = path.read_text(encoding="utf-8", errors="replace")
        lines = text.split("\n")
        events = []
        curr_time = datetime.utcnow()

        for line in lines:
            line_clean = line.strip()
            if not line_clean:
                continue

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
                "text": re.sub(r'[#*_`>]', '', line_clean).strip()
            })
        return events

    @staticmethod
    def load_pdf(file_path: Union[str, Path]) -> List[Dict[str, Any]]:
        path = Path(file_path)
        events = []
        curr_time = datetime.utcnow()
        
        try:
            import pypdf
            reader = pypdf.PdfReader(str(path))
            for idx, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                for line in page_text.split("\n"):
                    clean = line.strip()
                    if len(clean) > 10:
                        events.append({
                            "timestamp": curr_time.strftime("%Y-%m-%d %H:%M"),
                            "text": f"[Page {idx+1}] {clean}"
                        })
        except Exception:
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
    def load_json(file_path: Union[str, Path]) -> List[Dict[str, Any]]:
        path = Path(file_path)
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
    def load_csv(file_path: Union[str, Path]) -> List[Dict[str, Any]]:
        import csv
        path = Path(file_path)
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
    def load_text(file_path: Union[str, Path]) -> List[Dict[str, Any]]:
        path = Path(file_path)
        lines = path.read_text(encoding="utf-8", errors="replace").split("\n")
        return [
            {"timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M"), "text": l.strip()}
            for l in lines if l.strip()
        ]
