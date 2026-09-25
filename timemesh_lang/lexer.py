import re
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

@dataclass
class TMFrame:
    sigil: str          # '@', '#', '>', '?', '!'
    alias: str          # 'T', 'I', 'P', 'B', 'R'
    content: str
    parsed_meta: Optional[Dict[str, Any]] = None

class TMLexer:
    SIGIL_MAP = {
        '@': 'T', 'T:': 'T', 'TIME:': 'T',
        '#': 'I', 'I:': 'I', 'KEY:': 'I',
        '>': 'P', 'P:': 'P', 'DELTA:': 'P',
        '?': 'B', 'B:': 'B', 'WHATIF:': 'B',
        '!': 'R', 'R:': 'R', 'REWIND:': 'R',
    }

    @classmethod
    def parse(cls, source_text: str) -> List[TMFrame]:
        lines = source_text.strip().split('\n')
        frames = []
        current_sigil = None
        current_alias = None
        current_buffer = []

        def flush():
            if current_sigil and current_buffer:
                content = ' '.join(' '.join(current_buffer).split())
                frames.append(TMFrame(sigil=current_sigil, alias=current_alias, content=content))
                current_buffer.clear()

        for line in lines:
            trimmed = line.strip()
            if not trimmed or trimmed.startswith('//'):
                continue
            
            matched = False
            for token, alias in cls.SIGIL_MAP.items():
                if trimmed.startswith(token):
                    flush()
                    current_sigil = token[0]
                    current_alias = alias
                    body = trimmed[len(token):].strip()
                    if body:
                        current_buffer.append(body)
                    matched = True
                    break
            
            if not matched:
                if current_sigil:
                    current_buffer.append(trimmed)
        
        flush()
        return frames

if __name__ == '__main__':
    sample = """
@ 2026-09-23 10:00:00
# Service initialized with Postgres, Redis TTL 15m, and max_db_connections = 100.
> Reduced max_db_connections from 100 to 20 because cloud costs were high.
? Simulate 5,000 checkout requests under max_db_connections = 20.
! On error, trace root cause to connection limit, rewind playhead to 10:00:00, and hot-swap max_db_connections = 100.
"""
    frames = TMLexer.parse(sample)
    for f in frames:
        print(f"[{f.alias}] ({f.sigil}) -> {f.content}")
