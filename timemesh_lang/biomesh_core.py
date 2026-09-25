# -*- coding: utf-8 -*-
import time
import struct
import copy
import re
from typing import Dict, List, Any, Optional, Tuple

BASE2BIT = {"A": 0b00, "T": 0b01, "C": 0b10, "G": 0b11}
BIT2BASE = {0b00: "A", 0b01: "T", 0b10: "C", 0b11: "G"}

CODON_ISA = {
    "ATG": ("T", "OP_SET_PLAYHEAD"),
    "TAC": ("I", "OP_COMMIT_IFRAME"),
    "CAG": ("P", "OP_APPLY_PFRAME"),
    "GAG": ("B", "OP_EVAL_BFRAME_OCC"),
    "TAA": ("R", "OP_ZERO_BACKPROP_HOTSWAP")
}

class BioMeshCompiler:
    SIGIL_TO_CODON = {
        "@": "ATG", "T:": "ATG",
        "#": "TAC", "I:": "TAC",
        ">": "CAG", "P:": "CAG",
        "?": "GAG", "B:": "GAG",
        "!": "TAA", "R:": "TAA",
    }

    @classmethod
    def compile_to_dna(cls, prose_script: str) -> Tuple[str, bytes]:
        lines = prose_script.strip().split("\n")
        dna_sequence = []
        payload_bytes = bytearray()

        for line in lines:
            trimmed = line.strip()
            if not trimmed or trimmed.startswith("//"):
                continue
            
            for sigil, codon in cls.SIGIL_TO_CODON.items():
                if trimmed.startswith(sigil):
                    body = trimmed[len(sigil):].strip()
                    dna_sequence.append(f"[{codon}] {body}")
                    
                    codon_bits = 0
                    for base in codon:
                        codon_bits = (codon_bits << 2) | BASE2BIT[base]
                    payload_bytes.append(codon_bits)
                    break
                    
        return " || ".join(dna_sequence), bytes(payload_bytes)

class BioMeshVM:
    def __init__(self):
        self.playhead = "0000-00-00 00:00:00"
        self.timeline = []
        self.state = {}

    def parse_deltas(self, text: str) -> Dict[str, Any]:
        deltas = {}
        eq_matches = re.findall(r'([^\s=]+)\s*=\s*(\d+|"[^"]+"|\'[^\']+\'|[^\s]+)', text)
        for k, v in eq_matches:
            if v.isdigit():
                deltas[k] = int(v)
            else:
                deltas[k] = v.strip("\"'")
        if not deltas:
            deltas["_payload"] = text
        return deltas

    def execute_dna_codon(self, codon_op: str, payload: str) -> Dict[str, Any]:
        sigil_type, isa_op = CODON_ISA.get(codon_op, ("?", "UNKNOWN"))

        if isa_op == "OP_SET_PLAYHEAD":
            self.playhead = payload
            return {"op": isa_op, "playhead": self.playhead}

        elif isa_op == "OP_COMMIT_IFRAME":
            d = self.parse_deltas(payload)
            self.state.update(d)
            node = {"id": len(self.timeline) + 1, "codon": codon_op, "t": self.playhead, "state": copy.deepcopy(self.state), "delta": d}
            self.timeline.append(node)
            return {"op": isa_op, "state": copy.deepcopy(self.state)}

        elif isa_op == "OP_APPLY_PFRAME":
            d = self.parse_deltas(payload)
            self.state.update(d)
            node = {"id": len(self.timeline) + 1, "codon": codon_op, "t": self.playhead, "delta": d, "parent": self.timeline[-1]["id"] if self.timeline else None}
            self.timeline.append(node)
            return {"op": isa_op, "deltas": d, "state": copy.deepcopy(self.state)}

        elif isa_op == "OP_EVAL_BFRAME_OCC":
            sim_state = copy.deepcopy(self.state)
            sim_deltas = self.parse_deltas(payload)
            sim_state.update(sim_deltas)
            return {"op": isa_op, "simulated_state": sim_state, "disk_pollution": False}

        elif isa_op == "OP_ZERO_BACKPROP_HOTSWAP":
            t0 = time.perf_counter_ns()
            fix_deltas = self.parse_deltas(payload)
            target_key = list(fix_deltas.keys())[0] if fix_deltas else None
            
            root_node = None
            for node in reversed(self.timeline):
                if target_key in node.get("delta", {}):
                    root_node = node
                    break
            
            if root_node:
                root_node["delta"].update(fix_deltas)
            
            replayed = {}
            for node in self.timeline:
                replayed.update(node.get("delta", {}))
            self.state = replayed
            t_elapsed_ns = time.perf_counter_ns() - t0

            return {
                "op": isa_op,
                "root_cause_frame": root_node["id"] if root_node else None,
                "repaired_state": copy.deepcopy(self.state),
                "resolution_time_microsec": round(t_elapsed_ns / 1000, 3)
            }

    def execute_dna_stream(self, dna_script: str) -> List[Dict[str, Any]]:
        tokens = dna_script.split(" || ")
        results = []
        for tok in tokens:
            if not tok.strip(): continue
            match = re.match(r'\[([A-Z]{3})\]\s*(.*)', tok)
            if match:
                codon = match.group(1)
                payload = match.group(2)
                res = self.execute_dna_codon(codon, payload)
                results.append({"codon": codon, "result": res})
        return results
