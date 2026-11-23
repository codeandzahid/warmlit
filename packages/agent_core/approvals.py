"""Approval system REMOVED (owner order, 2026-11-23).

Warmlit is owner-only and local. Actions run directly — no approval
cards, no taps, no waiting. This class stays only so old imports
keep working; it approves everything.
"""


class ApprovalGate:
    def __init__(self, approve=None):
        self._approve = approve  # ignored: approvals removed

    def check(self, action: str, consequential: bool = False) -> bool:
        return True
