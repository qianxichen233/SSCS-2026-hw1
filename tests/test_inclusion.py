import base64
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from cryptography import x509
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

from main import inclusion
from merkle_proof import RootMismatchError, compute_leaf_hash


class InclusionTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.artifact = Path(directory.name) / "artifact.md"
        self.artifact.write_bytes(b"original artifact")

        key = ec.generate_private_key(ec.SECP256R1())
        name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "test signer")])
        now = datetime.now(timezone.utc)
        certificate = (
            x509.CertificateBuilder()
            .subject_name(name)
            .issuer_name(name)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(minutes=1))
            .not_valid_after(now + timedelta(days=1))
            .sign(key, hashes.SHA256())
        )
        signature = key.sign(self.artifact.read_bytes(), ec.ECDSA(hashes.SHA256()))
        body = {
            "spec": {
                "signature": {
                    "content": base64.b64encode(signature).decode(),
                    "publicKey": {
                        "content": base64.b64encode(
                            certificate.public_bytes(serialization.Encoding.PEM)
                        ).decode()
                    },
                }
            }
        }
        encoded_body = base64.b64encode(json.dumps(body).encode()).decode()
        self.proof = {
            "logIndex": 0,
            "treeSize": 1,
            "hashes": [],
            "rootHash": compute_leaf_hash(encoded_body),
        }
        self.entry = {
            "body": encoded_body,
            "verification": {"inclusionProof": self.proof},
        }
        self.output = io.StringIO()

    def run_inclusion(self):
        # Replace only the network; exercise certificate, signature, and proof checks.
        with patch("main.requests.get") as get, redirect_stdout(self.output):
            get.return_value.json.return_value = {"test-entry": self.entry}
            inclusion(0, self.artifact)
        return get

    def test_inclusion_fetches_entry_only_once(self):
        get = self.run_inclusion()
        get.assert_called_once()

    def test_valid_signature_and_proof_print_success(self):
        self.run_inclusion()
        self.assertIn("Offline verification successful", self.output.getvalue())

    def test_modified_artifact_raises_without_success(self):
        self.artifact.write_bytes(b"modified artifact")
        with self.assertRaises(InvalidSignature):
            self.run_inclusion()
        self.assertNotIn("Offline verification successful", self.output.getvalue())

    def test_invalid_proof_raises_without_success(self):
        self.proof["rootHash"] = "00" * 32
        with self.assertRaises(RootMismatchError):
            self.run_inclusion()
        self.assertNotIn("Offline verification successful", self.output.getvalue())
