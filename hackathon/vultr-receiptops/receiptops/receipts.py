"""Ed25519 execution attestations, bound to input, code and observed result.

A signature proves origin and integrity given a separately trusted public key.
It is not hardware attestation and does not prove the server itself is honest.
"""
import base64
import hashlib
import json
import os
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False).encode()

def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()

class Signer:
    def __init__(self, directory: Path):
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        path = directory / "signing-key.pem"
        if path.exists():
            self.key = serialization.load_pem_private_key(path.read_bytes(), password=None)
        else:
            self.key = Ed25519PrivateKey.generate()
            data = self.key.private_bytes(serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "wb") as stream:
                stream.write(data)
        self.public = base64.b64encode(self.key.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw)).decode()
        self.key_id = digest(base64.b64decode(self.public))[:16]

    def sign(self, payload: dict) -> dict:
        raw = canonical(payload)
        return {"payload": payload, "payload_sha256": digest(raw),
                "signature": base64.b64encode(self.key.sign(raw)).decode(),
                "public_key": self.public, "key_id": self.key_id,
                "algorithm": "Ed25519", "canonicalization": "receiptops-json-v1"}

def verify(receipt: dict, trusted_public_key: str) -> bool:
    try:
        if receipt["algorithm"] != "Ed25519" or receipt["canonicalization"] != "receiptops-json-v1":
            return False
        if receipt["public_key"] != trusted_public_key:
            return False
        raw = canonical(receipt["payload"])
        if digest(raw) != receipt["payload_sha256"]:
            return False
        key = Ed25519PublicKey.from_public_bytes(base64.b64decode(trusted_public_key, validate=True))
        key.verify(base64.b64decode(receipt["signature"], validate=True), raw)
        return True
    except (KeyError, TypeError, ValueError, Exception):
        return False
