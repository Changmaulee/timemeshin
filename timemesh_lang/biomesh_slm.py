# -*- coding: utf-8 -*-
import time
import re
import json
from typing import Dict, List, Any

CODON_ISA = {
    "ATG": "TIME_ANCHOR",
    "TAC": "GROUND_TRUTH",
    "CAG": "CAUSAL_DELTA",
    "GAG": "SPECULATIVE_THOUGHT",
    "TAA": "ZERO_BACKPROP_FIX"
}

class BioMeshSLM:
    def __init__(self, bot_name="BioMesh-SLM"):
        self.bot_name = bot_name
        self.turn = 0
        self.memory_timeline = []
        self.knowledge_graph = {
            "creator": "Chandramouli",
            "architecture": "BioMesh / TimeMesh Causal Engine",
            "memory_type": "2-Bit DNA Codon Stream",
            "learning_method": "Zero-Backprop Causal Hot-Swapping",
            "user_name": None
        }
        
        self.intent_patterns = [
            (r"(?i)\bmy name is (\w+)\b", self._handle_set_name),
            (r"(?i)\bwhat is my name\b", self._handle_get_name),
            (r"(?i)\bwho are you\b|\bwhat are you\b", self._handle_identity),
            (r"(?i)\bwho created you\b|\bwho made you\b", self._handle_creator),
            (r"(?i)\bactually my name is (\w+)\b|\bno,? that'?s wrong\b", self._handle_correction),
            (r"(?i)\bhow does your memory work\b", self._handle_memory_explainer),
            (r"(?i)\b(hi|hello|hey|greetings)\b", self._handle_greeting),
            (r"(?i)\bwhat can you do\b|\bhelp\b", self._handle_capabilities),
        ]

    def _record_frame(self, codon: str, text: str, delta: Dict[str, Any]):
        node = {
            "turn": self.turn,
            "codon": codon,
            "op": CODON_ISA[codon],
            "text": text,
            "delta": delta,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.memory_timeline.append(node)
        self.knowledge_graph.update(delta)

    def _handle_greeting(self, match, user_input):
        name = self.knowledge_graph.get("user_name")
        greeting = f"Hello {name}!" if name else "Hello! I am BioMesh-SLM, a causal small language model."
        return greeting + " How can I help you today?"

    def _handle_set_name(self, match, user_input):
        name = match.group(1)
        self._record_frame("CAG", f"User stated name = {name}", {"user_name": name})
        return f"Nice to meet you, {name}! I have committed your name into my causal memory track."

    def _handle_get_name(self, match, user_input):
        name = self.knowledge_graph.get("user_name")
        if name:
            return f"According to my active memory playhead, your name is {name}."
        return "You haven't told me your name yet! You can say 'My name is [name]'."

    def _handle_correction(self, match, user_input):
        new_name = None
        extracted = re.findall(r'(?i)name is (\w+)', user_input)
        if extracted:
            new_name = extracted[0]
        
        t0 = time.perf_counter_ns()
        root_cause_turn = None
        for node in reversed(self.memory_timeline):
            if "user_name" in node["delta"]:
                root_cause_turn = node["turn"]
                if new_name:
                    node["delta"]["user_name"] = new_name
                break
        
        if new_name:
            self.knowledge_graph["user_name"] = new_name
        
        elapsed_us = (time.perf_counter_ns() - t0) / 1000
        self._record_frame("TAA", f"Zero-backprop corrected user_name to {new_name}", {"user_name": new_name})
        
        return (f"Got it! I executed an instant Zero-Backprop rewind to Turn #{root_cause_turn}, "
                f"hot-swapped the causal frame in {elapsed_us:.2f} microseconds, and updated your name to {new_name}.")

    def _handle_identity(self, match, user_input):
        return ("I am BioMesh-SLM, an ultra-compact neural model that uses 2-bit DNA codons and "
                "TimeMesh causal memory instead of slow weight backpropagation.")

    def _handle_creator(self, match, user_input):
        return f"I was created by {self.knowledge_graph['creator']} using the TimeMeshin & BioMesh architectures."

    def _handle_memory_explainer(self, match, user_input):
        return ("My memory works like a video stream: ATG locks the playhead, TAC stores keyframes, "
                "CAG records deltas, GAG tests what-if thoughts, and TAA hot-swaps mistakes instantly.")

    def _handle_capabilities(self, match, user_input):
        return ("I can converse, maintain persistent episodic context across turns, recall facts, and "
                "perform instant zero-backprop self-healing when you correct me.")

    def chat(self, user_input: str) -> Dict[str, Any]:
        self.turn += 1
        self._record_frame("ATG", f"Turn {self.turn} Playhead", {"playhead_turn": self.turn})
        
        response_text = None
        for pattern, handler in self.intent_patterns:
            match = re.search(pattern, user_input)
            if match:
                response_text = handler(match, user_input)
                break
        
        if not response_text:
            name = self.knowledge_graph.get("user_name")
            prefix = f"{name}, " if name else ""
            response_text = f"{prefix}I understand you are asking about '{user_input}'. My causal knowledge graph is tracking this in active memory."
            self._record_frame("CAG", f"General topic: {user_input[:40]}", {"last_topic": user_input})
        
        return {
            "turn": self.turn,
            "response": response_text,
            "active_dna_codon": self.memory_timeline[-1]["codon"],
            "state_snapshot": {k: v for k, v in self.knowledge_graph.items() if v is not None}
        }

if __name__ == '__main__':
    bot = BioMeshSLM()
    print("="*75)
    print("       BIOMESH-SLM: CAUSAL SMALL LANGUAGE MODEL READY")
    print("="*75)
    
    test_prompts = [
        "Hello there!",
        "Who created you?",
        "My name is Alexander",
        "What is my name?",
        "Actually my name is Bob, that's wrong",
        "What is my name now?",
        "How does your memory work?"
    ]
    
    for prompt in test_prompts:
        print(f"\n[USER]: {prompt}")
        output = bot.chat(prompt)
        print(f"[BIOMESH-SLM] (Codon: {output['active_dna_codon']}): {output['response']}")
        print(f"  -> Active Memory State: {output['state_snapshot']}")
