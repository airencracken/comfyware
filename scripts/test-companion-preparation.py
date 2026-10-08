#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check proposed integration releases without enabling unpublished distfiles."""
from pathlib import Path
import importlib.util
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("recipes", ROOT / "scripts/test-recipes.py")
recipes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recipes)

class CompanionPreparation(unittest.TestCase):
    def test_recipes_match_live_services_and_compile_versions(self):
        for app, version in (("witmoot", "0.14.0"), ("imvault", "0.16.0")):
            with self.subTest(app=app):
                staged = ROOT / "release-preparation" / f"{app}-{version}.ebuild"
                text = staged.read_text()
                live = (ROOT / "www-apps" / app / f"{app}-9999.ebuild").read_text()
                self.assertEqual(recipes.recipe_errors(text), [])
                self.assertEqual(recipes.live_equivalent(text, app), live)
                args = recipes.compile_arguments(staged, app, version)
                recipes.validate_compiled_version(args, version)
                subprocess.run(["bash", "-n", str(staged)], check=True)

    def test_unpublished_recipes_have_no_active_package_or_manifest_claim(self):
        for app, version in (("witmoot", "0.14.0"), ("imvault", "0.16.0")):
            package = ROOT / "www-apps" / app
            self.assertFalse((package / f"{app}-{version}.ebuild").exists())
            self.assertNotIn(f"{app}_{version}_source.tar.gz", (package / "Manifest").read_text())
            self.assertNotIn(f"{app}-{version}-deps.tar.xz", (package / "Manifest").read_text())

    def test_wrong_build_stamp_is_rejected(self):
        args = recipes.compile_arguments(ROOT / "release-preparation/witmoot-0.14.0.ebuild", "witmoot", "0.14.0")
        with self.assertRaises(ValueError):
            recipes.validate_compiled_version(args, "0.13.0")

if __name__ == "__main__":
    unittest.main(verbosity=2)
