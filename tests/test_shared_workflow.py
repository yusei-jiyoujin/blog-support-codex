import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.doctor import RULE_FILES, STATE_FILES, inspect


class SharedWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        source = Path(__file__).resolve().parents[1]
        for name in (*RULE_FILES, *STATE_FILES):
            destination = self.root / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source / name, destination)

    def test_fresh_workspace_without_chat_history_is_ready(self):
        report = inspect(self.root)
        self.assertTrue(report["ready_for_text"], report["errors"])
        self.assertEqual(report["config"]["article_count"], 5)
        self.assertEqual(report["image_generation"], "unknown")
        self.assertTrue(report["warnings"])

    def test_missing_shared_rule_is_reported(self):
        (self.root / "SITE_PROFILE.md").unlink()
        report = inspect(self.root)
        self.assertFalse(report["ready_for_text"])
        self.assertIn("Missing shared file: SITE_PROFILE.md", report["errors"])

    def test_drift_in_settings_is_rejected(self):
        path = self.root / "WORKFLOW_CONFIG.json"
        config = json.loads(path.read_text())
        config["article_count"] = 1
        path.write_text(json.dumps(config), encoding="utf-8")
        report = inspect(self.root)
        self.assertFalse(report["ready_for_text"])
        self.assertIn("Shared configuration mismatch: article_count", report["errors"])

    def test_oversized_entry_is_rejected(self):
        (self.root / "AGENTS.md").write_text("x" * 8193)
        self.assertFalse(inspect(self.root)["ready_for_text"])

    def test_fingerprint_detects_rule_changes_but_not_article_logs(self):
        first = inspect(self.root)["workflow_fingerprint"]
        (self.root / "ARTICLE_LOG.json").write_text('{"events": [{"title": "example"}]}')
        self.assertEqual(first, inspect(self.root)["workflow_fingerprint"])
        with (self.root / "IMAGE_RULES.md").open("a") as file:
            file.write("\nChanged rule\n")
        self.assertNotEqual(first, inspect(self.root)["workflow_fingerprint"])


if __name__ == "__main__":
    unittest.main()
