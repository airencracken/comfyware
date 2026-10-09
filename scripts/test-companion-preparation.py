#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check coordinated release recipes before and after activation."""
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
        for app, version in (("witmoot", "0.15.0"), ("imvault", "0.16.2")):
            with self.subTest(app=app):
                staged = ROOT / "release-preparation" / f"{app}-{version}.ebuild"
                active = ROOT / "www-apps" / app / staged.name
                candidate = active if active.exists() else staged
                text = candidate.read_text()
                live = (ROOT / "www-apps" / app / f"{app}-9999.ebuild").read_text()
                self.assertEqual(recipes.recipe_errors(text), [])
                self.assertEqual(recipes.live_equivalent(text, app), live)
                args = recipes.compile_arguments(candidate, app, version)
                recipes.validate_compiled_version(args, version)
                subprocess.run(["bash", "-n", str(candidate)], check=True)

    def test_activation_matches_manifest_claims(self):
        for app, version in (("witmoot", "0.15.0"), ("imvault", "0.16.2")):
            package = ROOT / "www-apps" / app
            active = package / f"{app}-{version}.ebuild"
            manifest = (package / "Manifest").read_text()
            if active.exists():
                self.assertFalse((ROOT / "release-preparation" / active.name).exists())
                self.assertIn(f"DIST {app}_{version}_source.tar.gz ", manifest)
                self.assertIn(f"DIST {app}-{version}-deps.tar.xz ", manifest)
            else:
                self.assertNotIn(f"{app}_{version}_source.tar.gz", manifest)
                self.assertNotIn(f"{app}-{version}-deps.tar.xz", manifest)

    def test_wrong_build_stamp_is_rejected(self):
        active = ROOT / "www-apps/witmoot/witmoot-0.15.0.ebuild"
        candidate = active if active.exists() else ROOT / "release-preparation/witmoot-0.15.0.ebuild"
        args = recipes.compile_arguments(candidate, "witmoot", "0.15.0")
        with self.assertRaises(ValueError):
            recipes.validate_compiled_version(args, "0.13.0")

if __name__ == "__main__":
    unittest.main(verbosity=2)
