import time
import copy
import re
try:
    from .lexer import TMFrame, TMLexer
except ImportError:
    from lexer import TMFrame, TMLexer

class CausalNode:
    def __init__(self, frame_id, sigil, content, timestamp, state_delta, parent_id=None):
        self.frame_id = frame_id
        self.sigil = sigil
        self.content = content
        self.timestamp = timestamp
        self.state_delta = state_delta
        self.parent_id = parent_id
        self.children = []

class TimeMeshVM:
    def __init__(self):
        self.playhead = "0000-00-00 00:00:00"
        self.timeline = []
        self.active_state = {}
        self.step_counter = 0

    def parse_entities_from_prose(self, text):
        deltas = {}
        eq_matches = re.findall(r'(\w+)\s*=\s*(\d+|"[^"]+"|\'[^\']+\'|\w+)', text)
        for k, v in eq_matches:
            if v.isdigit():
                deltas[k] = int(v)
            else:
                deltas[k] = v.strip("\"'")
        
        from_to = re.findall(r'(\w+)\s+from\s+(\d+|\w+)\s+to\s+(\d+|\w+)', text, re.IGNORECASE)
        for k, old_v, new_v in from_to:
            if new_v.isdigit():
                deltas[k] = int(new_v)
            else:
                deltas[k] = new_v
        
        if not deltas:
            deltas["_raw_event"] = text[:60]
        return deltas

    def execute_frame(self, frame):
        self.step_counter += 1
        frame_id = f"frame_{self.step_counter:03d}"

        if frame.alias == 'T':
            self.playhead = frame.content
            return {"op": "SET_PLAYHEAD", "playhead": self.playhead}

        elif frame.alias == 'I':
            deltas = self.parse_entities_from_prose(frame.content)
            self.active_state.update(deltas)
            node = CausalNode(frame_id, '#', frame.content, self.playhead, deltas)
            self.timeline.append(node)
            return {"op": "COMMIT_IFRAME", "id": frame_id, "state": copy.deepcopy(self.active_state)}

        elif frame.alias == 'P':
            parent_id = self.timeline[-1].frame_id if self.timeline else None
            deltas = self.parse_entities_from_prose(frame.content)
            self.active_state.update(deltas)
            node = CausalNode(frame_id, '>', frame.content, self.playhead, deltas, parent_id=parent_id)
            if self.timeline:
                self.timeline[-1].children.append(frame_id)
            self.timeline.append(node)
            return {"op": "APPLY_PFRAME", "id": frame_id, "deltas": deltas, "state": copy.deepcopy(self.active_state)}

        elif frame.alias == 'B':
            simulated_state = copy.deepcopy(self.active_state)
            sim_deltas = self.parse_entities_from_prose(frame.content)
            simulated_state.update(sim_deltas)
            return {
                "op": "EVAL_BFRAME_OCC", 
                "simulation": frame.content, 
                "hypothetical_state": simulated_state,
                "disk_pollution": False
            }

        elif frame.alias == 'R':
            fix_deltas = self.parse_entities_from_prose(frame.content)
            target_entity = list(fix_deltas.keys())[0] if fix_deltas else None
            
            root_cause_node = None
            for node in reversed(self.timeline):
                if target_entity in node.state_delta:
                    root_cause_node = node
                    break
            
            start_t = time.perf_counter()
            rewind_playhead = root_cause_node.timestamp if root_cause_node else self.playhead
            if root_cause_node:
                root_cause_node.state_delta.update(fix_deltas)
                root_cause_node.content += f" [HOT-PATCHED: {fix_deltas}]"
            
            replayed_state = {}
            for node in self.timeline:
                replayed_state.update(node.state_delta)
            self.active_state = replayed_state
            elapsed_ms = (time.perf_counter() - start_t) * 1000

            return {
                "op": "ZERO_BACKPROP_HOTSWAP",
                "root_cause_frame": root_cause_node.frame_id if root_cause_node else None,
                "rewound_to_playhead": rewind_playhead,
                "patched_deltas": fix_deltas,
                "repaired_state": copy.deepcopy(self.active_state),
                "resolution_time_ms": round(elapsed_ms, 3)
            }

    def run_script(self, script_text):
        frames = TMLexer.parse(script_text)
        results = []
        for frame in frames:
            res = self.execute_frame(frame)
            results.append({"sigil": frame.sigil, "alias": frame.alias, "result": res})
        return results
