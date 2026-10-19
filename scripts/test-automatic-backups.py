#!/usr/bin/env python3
"""Validate backup compressor installation and the published operator policy."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
VERSIONS = {"songstead": "0.11.0", "witmoot": "0.18.0", "imvault": "0.20.0"}

def errors(text):
    problems = []
    flags = re.search(r'^IUSE="([^"]*)"', text, re.MULTILINE)
    if flags is None or "+zstd" not in flags[1].split():
        problems.append("zstd is not enabled by default")
    if "zstd? ( app-arch/zstd )" not in text:
        problems.append("optional zstd dependency missing")
    for phrase in ("seven copies", "10 GiB", "5 GiB", "instance settings", "off-host", "gzip", "docs/automatic-backups.md"):
        if phrase not in text:
            problems.append("missing backup instruction: " + phrase)
    return problems

class AutomaticBackupTests(unittest.TestCase):
    def test_versioned_and_live_recipes_install_and_describe_compression(self):
        for app, version in VERSIONS.items():
            for v in (version, "9999"):
                with self.subTest(app=app, version=v):
                    text = (ROOT / "www-apps" / app / f"{app}-{v}.ebuild").read_text()
                    self.assertEqual(errors(text), [])
                    self.assertIn("dodoc -r docs", text)

    def test_removing_dependency_or_policy_is_detected(self):
        text = (ROOT / "www-apps/songstead/songstead-0.11.0.ebuild").read_text()
        for before, after in (("+zstd", "zstd"), ("zstd? ( app-arch/zstd )", ""), ("seven copies", "unlimited copies"), ("10 GiB", "unlimited bytes"), ("off-host", "locally")):
            with self.subTest(before=before):
                self.assertNotEqual(text, text.replace(before, after))
                self.assertTrue(errors(text.replace(before, after)))

    def test_operator_policy_links_to_exact_published_versions(self):
        readme = (ROOT / "README.md").read_text()
        for app, version in VERSIONS.items():
            self.assertIn(f"{app}/blob/v{version}/docs/automatic-backups.md", readme)
        for phrase in ("24h", "seven copies", "10 GiB", "5 GiB", "APP_BACKUP_INTERVAL", "APP_BACKUP_COPY_MAX_BYTES", "off-host"):
            self.assertIn(phrase, readme)

if __name__ == "__main__":
    unittest.main(verbosity=2)
