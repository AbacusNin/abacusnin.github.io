"""Exercise fault recovery, pre-return blocking, and audit lead boundaries."""

from rsa_fault_lab import CryptoFaultDetected, D, E, N, P, Q, blind, demo, recover_factor, sign_raw, unblind
from signing_audit import analyze


def row(minute: int, kind: str, bits: int | None = None, client: str = "client-a") -> dict:
    event = {"time": f"2026-01-01T00:{minute:02d}:00Z", "kind": kind, "client_id": client, "key_id": "toy-key"}
    if bits is not None:
        event["message_bits"] = bits
    return event


def main() -> None:
    result = demo()
    assert result == {"validity": {2: True, 3: False, 5: True}, "factor": P, "other_factor": Q, "plaintext": 65}
    try:
        sign_raw(3, fault_q=True, validate=True)
    except CryptoFaultDetected:
        pass
    else:
        raise AssertionError("faulty signature escaped the guard")
    assert pow(sign_raw(3, validate=True), E, N) == 3
    try:
        recover_factor(3, sign_raw(3), E, N)
    except ValueError:
        pass
    else:
        raise AssertionError("valid signature produced a factor")
    ciphertext = pow(65, E, N)
    blinded = blind(ciphertext, 2, E, N)
    assert unblind(pow(blinded, D, N), 2, N) == 65
    try:
        blind(ciphertext, P, E, N)
    except ValueError:
        pass
    else:
        raise AssertionError("noninvertible blinding factor accepted")

    positive = [row(0, "sign_request", 2), row(1, "sign_request", 2), row(2, "sign_request", 3), row(3, "fault_validation_failed")]
    assert [x["reason"] for x in analyze(positive)] == ["small-message-probes", "output-fault"]
    benign = [row(0, "sign_request", 2, "healthcheck"), row(1, "sign_request", 2, "healthcheck"), row(2, "sign_request", 3, "healthcheck")]
    assert [x["reason"] for x in analyze(benign)] == ["small-message-probes"]
    near_miss = [row(0, "sign_request", 2), row(1, "sign_request", 2), row(12, "sign_request", 3)]
    assert analyze(near_miss) == []
    print("toy factor recovery, fault guard, blinding fallback, positive, benign, and near-miss checks passed")


if __name__ == "__main__":
    main()
