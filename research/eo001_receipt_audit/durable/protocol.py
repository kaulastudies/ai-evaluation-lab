"""Public-key verification for the local EO receipt protocol, version 0.2.

Trust anchors come from the evaluator, never from a received envelope. Signatures
authenticate the configured test issuer, not a real payment or complete history.
"""
from __future__ import annotations
import base64
import hashlib
import json
import re
from typing import Any
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

VERSION = "EO-RECEIPT/0.2.0"
DOMAIN = b"AI-Evaluation-Lab/EO-RECEIPT/0.2.0\x00"
REQUEST_FIELDS = {"operation_id", "order_id", "amount_minor", "currency", "idempotency_key"}
LABEL = re.compile(r"[A-Za-z0-9_.:/-]{1,160}\Z")


class ProtocolError(ValueError):
    pass


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def require(condition, reason):
    if not condition:
        raise ProtocolError(reason)


def exact(value, fields, reason):
    require(isinstance(value, dict) and set(value) == fields, reason)


def label(value):
    return isinstance(value, str) and LABEL.fullmatch(value) is not None


def request_valid(request):
    exact(request, REQUEST_FIELDS, "REQUEST_SHAPE")
    require(all(label(request[k]) for k in ("operation_id", "order_id", "idempotency_key")), "REQUEST_IDENTITY")
    require(request["order_id"].startswith("DEMO-") and request["currency"] == "USD", "SYNTHETIC_USD_ONLY")
    require(type(request["amount_minor"]) is int and 0 < request["amount_minor"] <= 10000, "AMOUNT_TYPE_OR_LIMIT")


def public_id(public_key: bytes) -> str:
    require(isinstance(public_key, bytes) and len(public_key) == 32, "PUBLIC_KEY_SHAPE")
    return hashlib.sha256(public_key).hexdigest()


def sign(private_key, payload):
    return {"payload": payload, "signature": base64.b64encode(private_key.sign(DOMAIN + canonical(payload))).decode("ascii")}


def verify_signature(envelope, public_key):
    exact(envelope, {"payload", "signature"}, "ENVELOPE_SHAPE")
    require(isinstance(envelope["signature"], str) and len(envelope["signature"]) == 88, "SIGNATURE_SHAPE")
    try:
        signature = base64.b64decode(envelope["signature"], validate=True)
        require(len(signature) == 64, "SIGNATURE_SHAPE")
        Ed25519PublicKey.from_public_bytes(public_key).verify(signature, DOMAIN + canonical(envelope["payload"]))
    except (InvalidSignature, ValueError, TypeError) as exc:
        raise ProtocolError("SIGNATURE_INVALID") from exc
    return envelope["payload"]


def issuer_valid(payload, public_key, store_id, kind):
    require(payload["version"] == VERSION and payload["kind"] == kind, "VERSION_OR_KIND")
    require(payload["issuer_id"] == public_id(public_key) and payload["store_id"] == store_id, "ISSUER_OR_STORE_MISMATCH")


def verify_receipt(envelope, public_key, store_id, request):
    request_valid(request)
    payload = verify_signature(envelope, public_key)
    exact(payload, {"version", "kind", "issuer_id", "store_id", "request", "receipt_id", "sequence", "settled"}, "RECEIPT_SHAPE")
    issuer_valid(payload, public_key, store_id, "settlement")
    require(canonical(payload["request"]) == canonical(request), "REQUEST_BINDING_MISMATCH")
    require(payload["settled"] is True, "NOT_SETTLED")
    require(type(payload["sequence"]) is int and payload["sequence"] > 0
            and payload["receipt_id"] == "synthetic-effect-" + str(payload["sequence"]), "RECEIPT_IDENTITY")
    return payload


def verify_observation(envelope, public_key, store_id, request, challenge, method):
    request_valid(request)
    require(label(challenge) and method in ("execute", "lookup"), "QUERY_CONTEXT")
    payload = verify_signature(envelope, public_key)
    exact(payload, {"version", "kind", "issuer_id", "store_id", "request_sha256", "challenge", "method", "status", "receipt"}, "OBSERVATION_SHAPE")
    issuer_valid(payload, public_key, store_id, "observation")
    require(payload["challenge"] == challenge, "STALE_CHALLENGE")
    require(payload["request_sha256"] == digest(request) and payload["method"] == method, "QUERY_BINDING_MISMATCH")
    require(payload["status"] in ("settled", "not_found", "conflict"), "OBSERVATION_STATUS")
    if payload["status"] == "settled":
        return verify_receipt(payload["receipt"], public_key, store_id, request)
    require(payload["receipt"] is None, "UNCONFIRMED_RECEIPT")
    return None


def verify_manifest(envelope, public_key, store_id, challenge):
    payload = verify_signature(envelope, public_key)
    exact(payload, {"version", "kind", "issuer_id", "store_id", "challenge", "snapshot"}, "MANIFEST_SHAPE")
    issuer_valid(payload, public_key, store_id, "closing-manifest")
    require(payload["challenge"] == challenge, "STALE_MANIFEST")
    snapshot = payload["snapshot"]
    exact(snapshot, {"effects", "events", "effect_count", "event_count"}, "SNAPSHOT_SHAPE")
    for items, count in (("effects", "effect_count"), ("events", "event_count")):
        require(isinstance(snapshot[items], list) and type(snapshot[count]) is int
                and snapshot[count] == len(snapshot[items]), "SNAPSHOT_COVERAGE")
    operations, keys = set(), set()
    for seq, receipt in enumerate(snapshot["effects"], 1):
        request = receipt["payload"]["request"]
        body = verify_receipt(receipt, public_key, store_id, request)
        require(body["sequence"] == seq, "EFFECT_SEQUENCE")
        require(request["operation_id"] not in operations and request["idempotency_key"] not in keys, "DUPLICATE_EFFECT")
        operations.add(request["operation_id"])
        keys.add(request["idempotency_key"])
    for seq, event in enumerate(snapshot["events"], 1):
        exact(event, {"seq", "method", "request_sha256", "challenge", "status"}, "EVENT_SHAPE")
        require(type(event["seq"]) is int and event["seq"] == seq, "EVENT_SEQUENCE")
        require(event["method"] in ("execute", "lookup") and label(event["challenge"])
                and event["status"] in ("settled", "not_found", "conflict"), "EVENT_VALUE")
        require(isinstance(event["request_sha256"], str) and re.fullmatch(r"[0-9a-f]{64}", event["request_sha256"]), "EVENT_REQUEST_HASH")
    return snapshot


def parse_json(raw: bytes, limit=65536):
    require(len(raw) <= limit, "INPUT_TOO_LARGE")
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "DUPLICATE_JSON_KEY")
            result[key] = value
        return result
    def reject(_):
        raise ProtocolError("NONFINITE_JSON")
    try:
        value = json.loads(raw, object_pairs_hook=pairs, parse_constant=reject)
        canonical(value)
        # The wire schemas are shallow; bound arbitrary candidate output too.
        def depth(x, n=0):
            require(n <= 24, "JSON_TOO_DEEP")
            if isinstance(x, dict):
                for v in x.values(): depth(v, n + 1)
            elif isinstance(x, list):
                for v in x: depth(v, n + 1)
        depth(value)
        return value
    except (ValueError, TypeError, RecursionError) as exc:
        raise ProtocolError("INVALID_JSON") from exc
