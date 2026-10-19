import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

from main import main


class CliTests(unittest.TestCase):
    def setUp(self):
        self.commands = {}
        for name in ("inclusion", "consistency", "get_latest_checkpoint"):
            patcher = patch("main." + name)
            self.commands[name] = patcher.start()
            self.addCleanup(patcher.stop)
        self.commands["get_latest_checkpoint"].return_value = {"treeSize": 2}

    def run_cli(self, args):
        output = io.StringIO()
        errors = io.StringIO()
        with patch("sys.argv", ["main.py"] + args), redirect_stdout(output), redirect_stderr(errors):
            try:
                main()
            except SystemExit as exc:
                return exc.code, errors.getvalue()
        return 0, output.getvalue()

    def assert_no_command_ran(self):
        for command in self.commands.values():
            command.assert_not_called()

    def test_inclusion_requires_artifact(self):
        for args in (["--inclusion", "1"], ["--inclusion", "0", "--artifact", ""]):
            with self.subTest(args=args):
                code, error = self.run_cli(args)
                self.assertEqual(code, 2)
                self.assertIn("--artifact", error)
                self.assert_no_command_ran()

    def test_commands_are_mutually_exclusive(self):
        combinations = (
            ["-c", "--inclusion", "1", "--artifact", "artifact.md"],
            ["-c", "--consistency"],
            ["--inclusion", "1", "--artifact", "artifact.md", "--consistency"],
        )
        for args in combinations:
            with self.subTest(args=args):
                code, error = self.run_cli(args)
                self.assertEqual(code, 2)
                self.assertIn("not allowed with argument", error)
                self.assert_no_command_ran()

    def test_inclusion_accepts_zero_index(self):
        code, _ = self.run_cli(["--inclusion", "0", "--artifact", "artifact.md"])
        self.assertEqual(code, 0)
        self.commands["inclusion"].assert_called_once_with(0, "artifact.md", False)

    def test_checkpoint_command_still_runs(self):
        code, output = self.run_cli(["-c"])
        self.assertEqual(code, 0)
        self.assertIn('"treeSize": 2', output)
        self.commands["get_latest_checkpoint"].assert_called_once_with(False)

    def test_consistency_command_still_runs(self):
        root = "00" * 32
        code, _ = self.run_cli([
            "--consistency", "--tree-id", "test-tree", "--tree-size", "1",
            "--root-hash", root,
        ])
        self.assertEqual(code, 0)
        self.commands["consistency"].assert_called_once_with(
            {"treeID": "test-tree", "treeSize": 1, "rootHash": root}, False
        )
