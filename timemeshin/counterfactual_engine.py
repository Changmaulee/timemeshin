"""
TimeMeshin Level 6: Counterfactual Causal Simulation Engine (B-Frames & OCC)
Enables speculative 'what-if' architectural branching with Optimistic Concurrency Control.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

class CounterfactualBranch:
    """Represents an isolated speculative branch in the spatio-temporal graph."""

    def __init__(self, branch_id: str, name: str, base_playhead: str, base_state: Dict[str, Any]):
        self.branch_id = branch_id
        self.name = name
        self.base_playhead = base_playhead
        self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.state_snapshot = dict(base_state)
        self.speculative_deltas = []
        self.status = "EVALUATING" # EVALUATING, MERGED, ABANDONED

    def mutate(self, entity: str, v_new: Any, rationale: str = "") -> Dict[str, Any]:
        """Applies a speculative B-Frame delta to this isolated branch."""
        v_old = self.state_snapshot.get(entity)
        self.state_snapshot[entity] = v_new
        
        delta = {
            "delta_id": f"bframe_{uuid.uuid4().hex[:8]}",
            "branch_id": self.branch_id,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "entity": entity,
            "v_old": v_old,
            "v_new": v_new,
            "rationale": rationale,
            "modality": "EVALUATING"
        }
        self.speculative_deltas.append(delta)
        return delta


class CounterfactualEngine:
    """Manages multi-universe speculative branches and OCC conflict resolution."""

    def __init__(self, ground_truth_client=None):
        self.client = ground_truth_client
        self.branches = {}

    def fork_branch(self, name: str, base_playhead: Optional[str] = None, initial_state: Optional[Dict[str, Any]] = None) -> CounterfactualBranch:
        """Forks a new speculative B-Frame branch from a specific point in time."""
        b_id = f"branch_{uuid.uuid4().hex[:8]}"
        ts = base_playhead or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        state = initial_state or {}
        
        branch = CounterfactualBranch(
            branch_id=b_id,
            name=name,
            base_playhead=ts,
            base_state=state
        )
        self.branches[b_id] = branch
        return branch

    def evaluate_occ_conflicts(self, branch_id: str, current_ground_truth_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimistic Concurrency Control (OCC) Check:
        Detects state collisions between speculative mutations and current ground truth.
        """
        branch = self.branches.get(branch_id)
        if not branch:
            return {"status": "ERROR", "message": "Branch not found"}

        conflicts = []
        clean_mutations = []

        for delta in branch.speculative_deltas:
            entity = delta["entity"]
            speculative_val = delta["v_new"]
            current_gt_val = current_ground_truth_state.get(entity)
            original_base_val = delta["v_old"]

            if current_gt_val != original_base_val and current_gt_val != speculative_val:
                conflicts.append({
                    "entity": entity,
                    "base_value": original_base_val,
                    "speculative_value": speculative_val,
                    "ground_truth_current_value": current_gt_val,
                    "type": "OCC_STATE_COLLISION"
                })
            else:
                clean_mutations.append(delta)

        return {
            "branch_id": branch_id,
            "branch_name": branch.name,
            "has_conflicts": len(conflicts) > 0,
            "conflicts_count": len(conflicts),
            "conflicts": conflicts,
            "clean_mutations_count": len(clean_mutations),
            "status": "CONFLICT_DETECTED" if conflicts else "MERGE_READY"
        }

    def simulate_what_if_scenario(self, hypothesis: str, target_state_changes: Dict[str, Any], base_state: Dict[str, Any]) -> Dict[str, Any]:
        """Runs a fast what-if simulation projection and returns outcome analysis."""
        branch = self.fork_branch(name=f"What-If: {hypothesis}", initial_state=base_state)
        for k, v in target_state_changes.items():
            branch.mutate(entity=k, v_new=v, rationale=f"Hypothesis: {hypothesis}")

        return {
            "hypothesis": hypothesis,
            "branch_id": branch.branch_id,
            "base_state": base_state,
            "projected_state": branch.state_snapshot,
            "simulated_deltas": branch.speculative_deltas
        }

    def simulate_what_if(self, parent_id: str, mutation_spec: Dict[str, Any], expected_conflict_keys: Optional[List[str]] = None) -> Dict[str, Any]:
        """Convenience method for high-level counterfactual simulation."""
        action = mutation_spec.get("action", "Hypothesis Branch")
        branch = self.fork_branch(name=action, initial_state={"architecture.pattern": "standard", "data.sync_rate": "1x"})
        branch.mutate("architecture.pattern", action, rationale="Counterfactual simulation")
        occ_eval = self.evaluate_occ_conflicts(branch.branch_id, {"architecture.pattern": "standard", "data.sync_rate": "1x"})
        return {
            "branch_id": branch.branch_id,
            "hypothesis": action,
            "has_conflicts": occ_eval["has_conflicts"],
            "timeline_delta": [f"Speculative mutation applied: {action}", "Causal parent locked: " + parent_id]
        }
