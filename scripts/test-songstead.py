#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Songstead recipe contracts and unprivileged installation regressions."""
from pathlib import Path
import importlib.util
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("recipes", ROOT / "scripts/test-recipes.py")
recipes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recipes)
STAGED = ROOT / "release-preparation/songstead-0.1.1.ebuild"
LIVE = ROOT / "www-apps/songstead/songstead-9999.ebuild"
ACTIVE = LIVE.parent / "songstead-0.1.1.ebuild"
RELEASE = ACTIVE if ACTIVE.exists() else STAGED


class SongsteadRecipes(unittest.TestCase):
    def test_release_preparation_and_live_parity(self):
        release, live = RELEASE.read_text(), LIVE.read_text()
        self.assertEqual(recipes.recipe_errors(release), [])
        self.assertEqual(recipes.recipe_errors(live), [])
        self.assertEqual(recipes.live_equivalent(release, "songstead"), live)
        self.assertIn('EGIT_BRANCH="master"', live)
        self.assertIn('LICENSE="AGPL-3+', live)
        self.assertIn("bubblewrap? ( >=sys-apps/bubblewrap-0.8[-suid(-)] )", live)
        self.assertIn("acct-user/songstead", live)

    def test_release_state_has_exact_manifest_entries(self):
        if ACTIVE.exists():
            self.assertFalse(STAGED.exists(), "Published recipe is still staged")
            entries = (LIVE.parent / "Manifest").read_text().splitlines()
            expected = {"songstead_0.1.0_source.tar.gz", "songstead-0.1.0-deps.tar.xz", "songstead_0.1.1_source.tar.gz", "songstead-0.1.1-deps.tar.xz"}
            spec = importlib.util.spec_from_file_location("manifests", ROOT / "scripts/test-manifests.py")
            manifests = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(manifests)
            self.assertEqual(manifests.validate_manifest(entries, expected), [])
        else:
            self.assertTrue(STAGED.exists())
            self.assertFalse((LIVE.parent / "Manifest").exists())

    def test_compile_version_and_accounts(self):
        for recipe, version in ((RELEASE, "0.1.1"), (LIVE, "9999")):
            args = recipes.compile_arguments(recipe, "songstead", version)
            recipes.validate_compiled_version(args, version)
            self.assertEqual(args[-1], "./cmd/songstead")
        for path in (RELEASE, LIVE, ROOT / "acct-user/songstead/songstead-0.ebuild",
                     ROOT / "acct-group/songstead/songstead-0.ebuild"):
            subprocess.run(["bash", "-n", str(path)], check=True)

    def run_install(self, text, name):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            source = work / "source"
            recipes.write_fixture(source, "songstead", "/usr/local/bin/songstead")
            unit = source / "contrib/systemd/songstead.service"
            unit.write_text(unit.read_text().replace(
                "ExecStart=/usr/local/bin/songstead\n",
                "ExecStart=/usr/local/bin/songstead serve\n"))
            recipe = work / "release-preparation" / name
            recipe.parent.mkdir()
            recipe.write_text(text)
            return subprocess.run(["bash", str(ROOT / "scripts/test-install.sh"),
                                   str(recipe), str(source)],
                                  capture_output=True, text=True, timeout=30)

    def test_live_and_staged_installation(self):
        for recipe in (RELEASE, LIVE):
            with self.subTest(recipe=recipe.name):
                result = self.run_install(recipe.read_text(), recipe.name)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_installation_mutations_fail(self):
        text = RELEASE.read_text()
        mutations = {
            "mode 0700": text.replace("fperms 0700 /var/lib/songstead", "fperms 0755 /var/lib/songstead"),
            "mode 0600": text.replace("fperms 0600 /etc/conf.d/songstead", "fperms 0644 /etc/conf.d/songstead"),
            "world-readable": text.replace("fperms 0600 /etc/songstead/songstead.env", "fperms 0644 /etc/songstead/songstead.env"),
            "OpenRC service still": text.replace("contrib/openrc/songstead >", "contrib/openrc/songstead | sed 's|/usr/bin|/usr/local/bin|' >"),
            "systemd command": text.replace("contrib/systemd/songstead.service >", "contrib/systemd/songstead.service | sed 's| serve||' >"),
            "sandbox drop-in": text.replace('dodoc "${T}/songstead-sandbox.conf"', ": # missing sandbox drop-in"),
            "logrotate": text.replace("newins contrib/logrotate/songstead songstead", ": # missing logrotate"),
            "compressed": text.replace('docompress -x "/usr/share/doc/${PF}/examples"', ": # compressed examples"),
        }
        for error, mutated in mutations.items():
            with self.subTest(error=error):
                self.assertNotEqual(text, mutated)
                result = self.run_install(mutated, STAGED.name)
                self.assertNotEqual(result.returncode, 0, "Installation mutation survived")
                self.assertIn(error, result.stderr)

    def test_invalid_recipe_names_fail_before_installation(self):
        for name in ("songstead-0.1.1-injected.ebuild", "songstead-0.1.ebuild", "unknown-0.1.0.ebuild"):
            with self.subTest(name=name):
                result = self.run_install(RELEASE.read_text(), name)
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn("src_install", result.stderr)

    def test_ci_runs_preparation_checks(self):
        workflow = (ROOT / ".github/workflows/qa.yml").read_text()
        self.assertRegex(workflow, r"for test in [^;\n]*\bsongstead\b")
        self.assertRegex(workflow, r"for test in [^;\n]*\bcompanion-preparation\b")


if __name__ == "__main__":
    unittest.main(verbosity=2)
