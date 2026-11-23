"""Approval gate: consequential actions need an explicit approval.

A typed 'yes' in chat is not approval in the real product; here the
gate is a callback so a UI can show a card and wait for a tap.
"""


class ApprovalGate:
    def __init__(self, approve=None):
        # approve(action: str) -> bool. Default: deny consequential actions.
        self._approve = approve or (lambda action: False)

    def check(self, action: str, consequential: bool = False) -> bool:
        if not consequential:
            return True
        return bool(self._approve(action))
