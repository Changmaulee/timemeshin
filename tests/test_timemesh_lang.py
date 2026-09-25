import unittest
from timemesh_lang import TMLexer, TimeMeshVM, BioMeshCompiler, CODON_ISA

class TestTimeMeshLang(unittest.TestCase):
    def test_lexer_and_sigils(self):
        script = """
        @ 2026-09-25 10:00:00
        # database = "Postgres" max_connections = 100
        > max_connections = 20
        ? Simulate 5,000 requests
        ! max_connections = 100
        """
        frames = TMLexer.parse(script)
        self.assertEqual(len(frames), 5)
        self.assertEqual([f.alias for f in frames], ["T", "I", "P", "B", "R"])

    def test_dna_codon_compiler(self):
        script = "@ 10:00\n# max_conn = 100\n> max_conn = 20\n? test = 1\n! max_conn = 100"
        dna, payload_bytes = BioMeshCompiler.compile_to_dna(script)
        self.assertIn("[ATG]", dna)
        self.assertIn("[TAC]", dna)
        self.assertIn("[CAG]", dna)
        self.assertIn("[GAG]", dna)
        self.assertIn("[TAA]", dna)
        self.assertEqual(len(payload_bytes), 5)

    def test_vm_execution_and_occ(self):
        vm = TimeMeshVM()
        script = """
        @ 2026-09-25 10:00:00
        # database = "Postgres" max_connections = 100
        > max_connections = 20
        """
        for frame in TMLexer.parse(script):
            vm.execute_frame(frame)
        
        self.assertEqual(vm.active_state.get("max_connections"), 20)
        self.assertEqual(vm.active_state.get("database"), "Postgres")

        # Test B-Frame OCC (Zero disk pollution)
        b_frame = TMLexer.parse('? max_connections = 500')[0]
        res = vm.execute_frame(b_frame)
        self.assertEqual(res["hypothetical_state"]["max_connections"], 500)
        # Active state should remain unchanged at 20!
        self.assertEqual(vm.active_state["max_connections"], 20)

if __name__ == "__main__":
    unittest.main()
