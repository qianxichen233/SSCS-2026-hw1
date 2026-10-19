import hashlib
import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import Mock, patch

from main import consistency
from merkle_proof import RootMismatchError


class ConsistencyTests(unittest.TestCase):
    def setUp(self):
        # Build a one-leaf tree extended to two leaves using RFC 6962 prefixes.
        first = hashlib.sha256(b"\x00first entry").digest()
        second = hashlib.sha256(b"\x00second entry").digest()
        root = hashlib.sha256(b"\x01" + first + second).hexdigest()
        self.previous = {"treeID": "test-tree", "treeSize": 1, "rootHash": first.hex()}
        self.latest = {"treeID": "test-tree", "treeSize": 2, "rootHash": root}
        self.proof = {"hashes": [second.hex()]}
        self.output = io.StringIO()

    def run_consistency(self):
        checkpoint_response = Mock()
        checkpoint_response.json.return_value = self.latest
        proof_response = Mock()
        proof_response.json.return_value = self.proof
        # Mock only HTTP responses; run the real consistency verifier.
        with (
            patch(
                "main.requests.get", side_effect=[checkpoint_response, proof_response]
            ),
            redirect_stdout(self.output),
        ):
            consistency(self.previous)

    def test_valid_proof_prints_success(self):
        self.run_consistency()
        self.assertIn("Consistency verification successful", self.output.getvalue())

    def test_tampered_proof_raises_without_success(self):
        self.proof["hashes"] = ["00" * 32]
        with self.assertRaises(RootMismatchError):
            self.run_consistency()
        self.assertNotIn("Consistency verification successful", self.output.getvalue())

    def test_empty_proof_raises_without_success(self):
        self.proof["hashes"] = []
        with self.assertRaises(ValueError):
            self.run_consistency()
        self.assertNotIn("Consistency verification successful", self.output.getvalue())
