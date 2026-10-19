import unittest
from unittest.mock import patch

import requests

from main import get_latest_checkpoint, get_maybe_raise


class HttpTests(unittest.TestCase):
    @patch("main.requests.get")
    def test_returns_response_without_parsing_and_sets_timeout(self, get):
        result = get_maybe_raise("https://example.test/log", params={"treeID": "test"})
        self.assertIs(result, get.return_value)
        get.return_value.raise_for_status.assert_called_once()
        get.return_value.json.assert_not_called()
        get.assert_called_once_with(
            "https://example.test/log", params={"treeID": "test"}, timeout=10
        )

    @patch("main.requests.get")
    def test_http_error_propagates(self, get):
        get.return_value.raise_for_status.side_effect = requests.HTTPError("503")
        with self.assertRaises(requests.HTTPError):
            get_maybe_raise("https://example.test/log")
        get.return_value.json.assert_not_called()

    @patch("main.requests.get")
    def test_timeout_propagates(self, get):
        get.side_effect = requests.Timeout("Server did not respond")
        with self.assertRaises(requests.Timeout):
            get_maybe_raise("https://example.test/log")

    @patch("main.requests.get")
    def test_checkpoint_caller_propagates_invalid_json(self, get):
        get.return_value.json.side_effect = requests.exceptions.JSONDecodeError(
            "Invalid JSON", "not json", 0
        )
        with self.assertRaises(requests.exceptions.JSONDecodeError):
            get_latest_checkpoint()
