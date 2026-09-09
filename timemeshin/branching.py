"""
B-Frame Ephemeral Branching Sandbox for TimeMeshin.
Enables agents to spawn speculative, copy-on-write (CoW) timelines off any playhead
to simulate counterfactuals ("What-If" scenarios, rollbacks, migrations) without polluting ground truth.
"""

from __future__ import annotations
import copy
import uuid
import datetime
from typing import List, Dict, Any, Optional, Callable
from .models import StateDelta, SemanticEvent, Keyframe, Modality
from .storage import TimeMeshinStorage


class EphemeralBranch:
    """
    In-memory isolated branch sandbox representing S_branch(t) = S(t) ⊕ Δ_hypothetical.
    Guarded by Optimistic Concurrency Control (OCC) to prevent Ghost Rebases.
    """

    def __init__(self, parent_storage: TimeMeshinStorage, branch_playhead: str, branch_name: Optional[str] = None):
        self.parent_storage = parent_storage
        self.branch_playhead = branch_playhead
        self.branch_name = branch_name or f"branch_{uuid.uuid4().hex[:6]}"
        self.created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Snapshot base timeline epoch for OCC
        self.base_epoch = self.parent_storage.get_timeline_epoch(self.branch_playhead)

        # In-memory overlay state
        self._hypothetical_deltas: List[StateDelta] = []
        self._hypothetical_events: List[SemanticEvent] = []
        self._is_committed = False
        self._is_discarded = False

    def ingest_hypothetical(
        self,
        entity: str,
        attribute: str,
        v_new: str,
        v_old: Optional[str] = None,
        causal_rationale: str = "",
        rack: str = "Sandbox",
        timestamp: Optional[str] = None
    ) -> StateDelta:
        """
        Records a speculative mutation (B-Frame) on the ephemeral branch.
        """
        if self._is_discarded or self._is_committed:
            raise RuntimeError(f"Cannot write to branch '{self.branch_name}' which is already closed.")

        ts = timestamp or self.branch_playhead
        delta = StateDelta(
            id=f"bframe_{uuid.uuid4().hex[:8]}",
            timestamp=ts,
            entity=entity,
            rack=rack,
            attribute=attribute,
            v_old=v_old,
            v_new=v_new,
            causal_rationale=causal_rationale,
            modality=Modality.HYPOTHETICAL,
            metadata={"branch_name": self.branch_name, "is_hypothetical": True}
        )
        self._hypothetical_deltas.append(delta)
        return delta

    def rebase(self, new_playhead: Optional[str] = None) -> None:
        """
        Rebases the ephemeral branch onto the latest base timeline state and updates the base epoch.
        """
        if new_playhead:
            self.branch_playhead = new_playhead
        self.base_epoch = self.parent_storage.get_timeline_epoch(self.branch_playhead)

    def scrub(self, playhead: Optional[str] = None) -> Keyframe:
        """
        Reconstructs the consolidated state table on this branch at the specified playhead,
        combining base ground truth with branch-local hypothetical deltas.
        """
        target_playhead = playhead or self.branch_playhead
        
        # 1. Base keyframe from parent storage
        base_keyframe = self.parent_storage.fold_keyframe(target_playhead)
        state_table = copy.deepcopy(base_keyframe.state_table)
        source_ids = list(base_keyframe.source_delta_ids)

        # 2. Overlay hypothetical deltas
        for d in self._hypothetical_deltas:
            if d.timestamp <= target_playhead:
                if d.entity not in state_table:
                    state_table[d.entity] = {
                        "_rack": d.rack,
                        "_last_updated": d.timestamp,
                        "_last_modality": d.modality.value
                    }
                state_table[d.entity][d.attribute] = d.v_new
                state_table[d.entity]["_last_updated"] = d.timestamp
                state_table[d.entity]["_last_modality"] = d.modality.value
                source_ids.append(d.id)

        return Keyframe(
            timestamp=target_playhead,
            state_table=state_table,
            source_delta_ids=source_ids
        )

    def evaluate_hypothesis(self, validator_fn: Callable[[Dict[str, Any]], bool]) -> bool:
        """
        Executes a test/evaluation function against the branch's current state.
        """
        current_state = self.scrub().state_table
        return validator_fn(current_state)

    def commit_to_main(self, target_timestamp: Optional[str] = None, force: bool = False) -> List[StateDelta]:
        """
        Merges all hypothetical deltas into the parent ground truth timeline as COMMITTED state deltas.
        Performs Optimistic Concurrency Control (OCC) check against base_epoch.
        """
        if self._is_committed:
            return []
        if self._is_discarded:
            raise RuntimeError(f"Cannot commit a discarded branch '{self.branch_name}'.")

        # OCC Epoch Validation (Ghost Rebase Prevention)
        current_epoch = self.parent_storage.get_timeline_epoch(self.branch_playhead)
        if current_epoch != self.base_epoch and not force:
            from .models import BranchConflictError
            raise BranchConflictError(
                f"Optimistic Concurrency Control (OCC) conflict: Underlying timeline mutated from "
                f"{self.base_epoch} to {current_epoch} during branch simulation. Call sim.rebase() or commit with force=True."
            )

        committed_deltas = []
        commit_ts = target_timestamp or datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for d in self._hypothetical_deltas:
            real_delta = StateDelta(
                id=f"delta_{uuid.uuid4().hex[:8]}",
                timestamp=commit_ts,
                entity=d.entity,
                rack=d.rack,
                attribute=d.attribute,
                v_old=d.v_old,
                v_new=d.v_new,
                causal_rationale=f"[Merged from branch {self.branch_name}]: {d.causal_rationale}",
                modality=Modality.COMMITTED,
                parent_ids=d.parent_ids,
                metadata={"origin_branch": self.branch_name}
            )
            self.parent_storage.save_delta(real_delta)
            committed_deltas.append(real_delta)

        self._is_committed = True
        return committed_deltas

    def discard(self) -> None:
        """Drops the branch with zero disk write overhead."""
        self._hypothetical_deltas.clear()
        self._hypothetical_events.clear()
        self._is_discarded = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self._is_committed and not self._is_discarded:
            # Auto-discard on exit if not explicitly committed
            self.discard()
