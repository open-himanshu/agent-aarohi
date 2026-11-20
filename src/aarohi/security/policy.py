"""Deterministic permission policy; model output cannot override this module."""
from dataclasses import dataclass
from enum import StrEnum

class Risk(StrEnum):
    READ = "read"
    REVERSIBLE = "reversible"
    EXTERNAL = "external"
    DESTRUCTIVE = "destructive"

@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: str

def authorise(risk: Risk, approved: bool = False) -> Decision:
    if risk is Risk.READ:
        return Decision(True, "Read-only action")
    if risk in (Risk.REVERSIBLE, Risk.EXTERNAL) and approved:
        return Decision(True, "User-approved action")
    if risk is Risk.DESTRUCTIVE:
        return Decision(False, "Destructive actions are denied by default")
    return Decision(False, "Explicit user approval is required")
