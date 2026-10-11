"""Synthetic server-side release decision inspired by the gatekeeper case.

This module returns authorization decisions only. It has no model, secret store,
identity provider, persistence, or production authentication integration.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Grant:
    subject_id: str
    object_id: str
    permission: str
    expires_at: datetime


def decide_release(authenticated_subject, requested_object, trusted_grants, now, untrusted_prompt=""):
    """Use server-provided identity and grants; ignore claims in user prompt text."""
    if not isinstance(authenticated_subject, str) or not authenticated_subject:
        return {"decision": "deny", "reason": "missing_authenticated_subject"}
    if not isinstance(requested_object, str) or not requested_object:
        return {"decision": "deny", "reason": "missing_object"}
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        return {"decision": "deny", "reason": "invalid_clock"}

    # The prompt is intentionally excluded from the decision. A claimed rank,
    # alleged merit, or instruction to the model cannot mint a server grant.
    _ = untrusted_prompt
    if not isinstance(trusted_grants, (list, tuple)):
        return {"decision": "deny", "reason": "invalid_grant_store"}
    for grant in trusted_grants:
        if not isinstance(grant, Grant):
            return {"decision": "deny", "reason": "invalid_grant_store"}
        if (not isinstance(grant.expires_at, datetime)
                or grant.expires_at.tzinfo is None
                or grant.expires_at.utcoffset() is None):
            return {"decision": "deny", "reason": "invalid_grant_store"}
    for grant in trusted_grants:
        if (grant.subject_id == authenticated_subject
                and grant.object_id == requested_object
                and grant.permission == "release"
                and now < grant.expires_at):
            return {"decision": "allow", "reason": "matching_server_grant"}
    return {"decision": "deny", "reason": "no_matching_server_grant"}
