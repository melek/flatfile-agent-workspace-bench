"""Tests for the #5 artifact-diff reconstruction (runner.py).

The reconstruction logic (replay actions onto a seed, verify hashes, emit a
stable diff) is the deep module; these tests exercise it directly without the
scenario/template plumbing. The planted marker-mismatch fixture sets up the
SA2 failure that test_checks.py (#6) asserts end-to-end.

Run: python -m unittest discover -s bench/tests
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR.parent))  # bench/
import runner  # type: ignore  # noqa: E402


def _h(text: str) -> str:
    return runner._sha256_text(text)


class TestReplay(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.root = Path(self._td.name)
        # seed: one pre-existing file the run will append to / delete
        (self.root / "decisions.md").write_text("# Decisions\n")

    def tearDown(self):
        self._td.cleanup()

    def test_create_rewrite_append_delete(self):
        actions = [
            {"path": "daybook/d.md", "action": "create", "content": "log\n",
             "sha256": _h("log\n")},
            {"path": "decisions.md", "action": "append", "content": "entry\n",
             "sha256": _h("# Decisions\nentry\n")},
            {"path": "daybook/d.md", "action": "rewrite", "content": "log2\n",
             "sha256": _h("log2\n")},
        ]
        issues = runner._replay_actions(self.root, actions)
        self.assertEqual(issues, [], f"unexpected hash issues: {issues}")
        self.assertEqual((self.root / "daybook/d.md").read_text(), "log2\n")
        self.assertEqual((self.root / "decisions.md").read_text(), "# Decisions\nentry\n")

    def test_delete(self):
        runner._replay_actions(self.root, [{"path": "decisions.md", "action": "delete"}])
        self.assertFalse((self.root / "decisions.md").exists())

    def test_delete_missing_is_error(self):
        with self.assertRaises(runner.ReplayError):
            runner._replay_actions(self.root, [{"path": "nope.md", "action": "delete"}])

    def test_append_missing_is_error(self):
        with self.assertRaises(runner.ReplayError):
            runner._replay_actions(
                self.root, [{"path": "ghost.md", "action": "append", "content": "x"}]
            )

    def test_traversing_path_is_error(self):
        with self.assertRaises(runner.ReplayError):
            runner._replay_actions(
                self.root, [{"path": "../escape", "action": "create", "content": "x"}]
            )

    def test_hash_mismatch_flagged(self):
        # content_summary-style self-report that doesn't match its own content:
        # the recorded sha256 is for a version WITH a marker the content lacks.
        actions = [{
            "path": "observations.md", "action": "create",
            "content": "## A note\n(no marker here)\n",
            "sha256": _h("## A note\n**Generated-by:** inference\n"),
        }]
        issues = runner._replay_actions(self.root, actions)
        self.assertEqual(len(issues), 1)
        self.assertIn("sha256 mismatch", issues[0])


class TestPlantedMarkerMismatch(unittest.TestCase):
    """Transcript claims a Generated-by marker the file lacks -> the
    reconstructed artifact has no marker, which is what SA2 (#6) scores fail."""

    def test_reconstructed_file_lacks_marker(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            actions = [{
                "path": "observations.md", "action": "create",
                # the content_summary (not replayed) would CLAIM a marker;
                # the actual content omits it.
                "content": "## Cross-cutting pattern\nSome observation.\n",
                "sha256": _h("## Cross-cutting pattern\nSome observation.\n"),
                "content_summary": "Wrote an observation with Generated-by: inference.",
            }]
            runner._replay_actions(root, actions)
            text = (root / "observations.md").read_text()
            self.assertNotIn("**Generated-by:**", text)


class TestDiffStability(unittest.TestCase):
    def test_diff_is_deterministic_and_shows_changes(self):
        seed = {"a.md": "one\ntwo\n", "keep.md": "same\n"}
        post = {"a.md": "one\nTWO\n", "keep.md": "same\n", "new.md": "fresh\n"}
        d1 = runner._unified_diff(seed, post)
        d2 = runner._unified_diff(seed, post)
        self.assertEqual(d1, d2, "diff must be reproducible")
        self.assertIn("a/a.md", d1)
        self.assertIn("-two", d1)
        self.assertIn("+TWO", d1)
        self.assertIn("b/new.md", d1)
        self.assertNotIn("keep.md", d1, "unchanged files must not appear")


if __name__ == "__main__":
    unittest.main()
