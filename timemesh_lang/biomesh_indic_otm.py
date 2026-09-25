# -*- coding: utf-8 -*-
import sys
import time
import json
from biomesh_core import BioMeshCompiler, BioMeshVM

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

class BioMeshIndicEngine:
    def __init__(self, tokenizer_repo_or_path="timemeshin-otm-tokenizer"):
        self.tokenizer_path = tokenizer_repo_or_path
        self.vm = BioMeshVM()

    def run_indic_script(self, indic_tm_script: str):
        print("="*75)
        print("    EXECUTING INDIC BIOMESH TM-LANG SCRIPT (DEVNAGARI & TAMIL)")
        print("="*75)
        
        dna_str, binary_bytes = BioMeshCompiler.compile_to_dna(indic_tm_script)
        print(f"\n[1] 2-Bit DNA Compiled Sequence:\n    {dna_str}")
        print(f"[2] Raw Binary Bytecode Footprint: {len(binary_bytes)} bytes")
        
        t0 = time.perf_counter_ns()
        results = self.vm.execute_dna_stream(dna_str)
        t_elapsed_ms = (time.perf_counter_ns() - t0) / 1_000_000
        
        print(f"\n[3] Execution Results (Completed in {t_elapsed_ms:.3f} ms):")
        for r in results:
            codon = r["codon"]
            res = r["result"]
            print(f"    * Codon [{codon}] -> {res.get('op')}: {json.dumps(res, ensure_ascii=False)}")
            
        print("\n[4] Active Causal State Snapshot:")
        print(f"    {json.dumps(self.vm.state, indent=4, ensure_ascii=False)}")
        print("="*75)

if __name__ == '__main__':
    engine = BioMeshIndicEngine("timemeshin-otm-tokenizer")
    
    sample_indic_program = """
    @ 2026-09-24 10:00:00
    # मुख्य_डेटाबेस = "PostgreSQL" कनेक्शन_सीमा = 100
    > कनेक्शन_सीमा = 20
    ? क्या 5000 अनुरोधों पर 504 टाइमआउट होगा?
    ! त्रुटि होने पर कनेक्शन_सीमा = 100
    """
    
    engine.run_indic_script(sample_indic_program)
