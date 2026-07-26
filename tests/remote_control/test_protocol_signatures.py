import base64
import importlib
import json
from pathlib import Path
from types import ModuleType
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
VECTORS_PATH = (
    REPOSITORY_ROOT
    / "apps"
    / "remote-control-protocol"
    / "fixtures"
    / "v1"
    / "security-vectors.json"
)
VECTORS: dict[str, Any] = json.loads(VECTORS_PATH.read_text(encoding="utf-8"))


def _load_module(name: str) -> ModuleType | None:
    try:
        return importlib.import_module(name)
    except ModuleNotFoundError as error:
        if error.name in {name, name.rsplit(".", 1)[0]}:
            return None
        raise


def _wrong_algorithm_signature(signature: str) -> str:
    _, payload, proof = signature.split(".")
    protected_header = base64.urlsafe_b64encode(
        json.dumps(
            {
                "alg": "ES384",
                "typ": "hermes-remote-control+jws",
            },
            separators=(",", ":"),
        ).encode()
    ).rstrip(b"=")
    return f"{protected_header.decode()}.{payload}.{proof}"


def test_rfc8785_bytes_and_capability_hash_match_typescript_vector() -> None:
    protocol = _load_module("remote_control.protocol")

    assert protocol is not None, "the Python protocol module must exist"
    canonicalize = getattr(protocol, "canonicalize_remote_document", None)
    document_hash = getattr(protocol, "remote_document_hash", None)
    assert canonicalize is not None, "RFC 8785 canonicalization must exist"
    assert document_hash is not None, "the capability hash helper must exist"

    assert (
        canonicalize(VECTORS["signedEnvelope"]["document"]).decode()
        == VECTORS["signedEnvelope"]["canonical"]
    )
    assert (
        canonicalize(VECTORS["capability"]["document"]).decode()
        == VECTORS["capability"]["canonical"]
    )
    assert (
        document_hash(VECTORS["capability"]["document"])
        == VECTORS["capability"]["hash"]
    )


def test_es256_proof_is_bound_to_payload_target_and_expiry() -> None:
    protocol = _load_module("remote_control.protocol")

    assert protocol is not None, "the Python protocol module must exist"
    verify = getattr(protocol, "verify_signed_document", None)
    assert verify is not None, "the ES256 verifier must exist"

    envelope = VECTORS["signedEnvelope"]
    common = {
        "document": envelope["document"],
        "signature": envelope["signature"],
        "public_jwk": envelope["publicJwk"],
        "now": "2026-07-26T08:01:00Z",
        "expected": {
            "computerId": "cmp_vector_0001",
            "deviceId": "dev_vector_0001",
            "sessionId": "ses_vector_0001",
        },
    }

    assert verify(**common) == {"valid": True}
    assert verify(
        **{
            **common,
            "expected": {
                **common["expected"],
                "computerId": "cmp_different_0001",
            },
        }
    ) == {"valid": False, "reason": "target-mismatch"}
    assert verify(
        **{
            **common,
            "expected": {
                "computerId": "cmp_vector_0001",
            },
        }
    ) == {"valid": False, "reason": "target-mismatch"}
    assert verify(
        **{**common, "now": "2026-07-26T08:05:00.001Z"}
    ) == {"valid": False, "reason": "expired"}
    assert verify(**{**common, "now": "not-a-date"}) == {
        "valid": False,
        "reason": "invalid-signature",
    }
    assert verify(
        **{
            **common,
            "document": {
                **envelope["document"],
                "payload": {
                    "queueIfOffline": True,
                    "text": "Continue safely.",
                },
            },
        }
    ) == {"valid": False, "reason": "payload-mismatch"}
    assert verify(
        **{
            **common,
            "signature": _wrong_algorithm_signature(envelope["signature"]),
        }
    ) == {"valid": False, "reason": "wrong-algorithm"}


def test_capability_risk_policy_rejects_stale_and_sensitive_offline_actions() -> None:
    authorization = _load_module("remote_control.authorization")

    assert authorization is not None, "the Python authorization module must exist"
    authorize = getattr(authorization, "authorize_remote_action", None)
    assert authorize is not None, "capability-bound authorization must exist"

    base = {
        "capability": VECTORS["capability"]["document"],
        "capability_hash": VECTORS["capability"]["hash"],
        "method": "prompt.submit",
        "online": True,
        "queue_if_offline": False,
        "foreground": True,
        "unlocked": True,
        "unlock_age_ms": 0,
    }

    assert authorize(
        **{
            **base,
            "capability_hash": "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
        }
    ) == {"authorized": False, "reason": "capability-stale"}
    assert authorize(
        **{
            **base,
            "capability": {
                **VECTORS["capability"]["document"],
                "methods": {
                    **VECTORS["capability"]["document"]["methods"],
                    "prompt.submit": {
                        "risk": "unknown",
                        "offline": True,
                        "biometric": False,
                    },
                },
            },
            "capability_hash": (
                "sha256-fJjH90ReOcHUOsvmepSPlrVtCNF78ZH72E_ImDCqUCc"
            ),
        }
    ) == {"authorized": False, "reason": "method-unsupported"}
    assert authorize(
        **{
            **base,
            "method": "prompt.submit",
            "online": False,
            "queue_if_offline": True,
        }
    ) == {"authorized": True, "risk": "low"}
    assert authorize(
        **{
            **base,
            "method": "approval.respond",
            "online": False,
            "queue_if_offline": True,
        }
    ) == {"authorized": False, "reason": "offline-queue-disallowed"}
    assert authorize(
        **{
            **base,
            "method": "interrupt.request",
            "unlock_age_ms": 300_001,
        }
    ) == {"authorized": False, "reason": "step-up-required"}
    assert authorize(**{**base, "method": "approval.respond"}) == {
        "authorized": False,
        "reason": "step-up-required",
    }
    assert authorize(
        **{
            **base,
            "method": "approval.respond",
            "biometric_proof_verified": True,
        }
    ) == {"authorized": True, "risk": "high"}


def test_unknown_message_policy_fails_closed() -> None:
    authorization = _load_module("remote_control.authorization")

    assert authorization is not None, "the Python authorization module must exist"
    disposition = getattr(authorization, "unknown_message_disposition", None)
    assert disposition is not None, "unknown-message handling must exist"

    assert disposition(kind="event", critical=False) == "retain-opaque"
    assert disposition(kind="event", critical=True) == "reject"
    assert disposition(kind="command", critical=False) == "reject"
    assert disposition(kind="security", critical=False) == "reject"
