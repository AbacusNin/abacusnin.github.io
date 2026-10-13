"""Synthetic positive, expected retry, and scoped near-miss checks."""

from gateway_session_review import review


def event(eid, terminal="T1", date="2026-01-01", session="S1", mti="0100", stan="918939", **extra):
    return {"event_id": eid, "terminal_id": terminal, "processing_date": date,
            "session_id": session, "mti": mti, "stan": stan, **extra}


def test_cases():
    positive = review([
        event("a1"), event("a2", session="S2"),
        event("r1", session="S3", mti="0400", stan="000001", original_stan="918939"),
    ])
    types = {f["type"] for f in positive["findings"]}
    assert "cross_session_repeated_stan" in types
    assert "reversal_reference_review" in types
    assert any(f.get("reference_state") == "reference_seen_in_input" for f in positive["findings"])

    benign_retry = review([event("b1"), event("b2"), event("b3", mti="0110")])
    assert any(f["type"] == "same_session_retry_or_duplicate" for f in benign_retry["findings"])
    assert not any(f["type"] == "cross_session_repeated_stan" for f in benign_retry["findings"])

    near_miss = review([event("c1"), event("c2", terminal="T2"),
                        event("c3", date="2026-01-02")])
    assert not any("repeated_stan" in f["type"] or "retry_or_duplicate" in f["type"]
                   for f in near_miss["findings"])
    try:
        review([event("d1", pan="4111111111111111")])
    except ValueError:
        pass
    else:
        raise AssertionError("raw account number must be rejected")
    print("PASS: cross-session positive, benign retry, scoped near miss, raw PAN rejection")


if __name__ == "__main__":
    test_cases()
