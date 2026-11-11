#!/usr/bin/env python3
"""Require source builds to use a Go release with the HTTP server fix."""

from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


def validate_toolchain(text):
    text = "\n".join(line.split("#", 1)[0] for line in text.splitlines())
    dependencies = re.findall(r'^BDEPEND\+?="([^"]*)"', text, re.MULTILINE)
    versions = re.findall(r'(?<!\S)>=dev-lang/go-(\d+)\.(\d+)(?:\.(\d+))?(?=\s|$)',
                          "\n".join(dependencies))
    if not versions or max(tuple(int(n or 0) for n in version) for version in versions) < (1, 26, 11):
        raise ValueError("source builds require Go 1.26.11 or a newer patched release")


class ToolchainTests(unittest.TestCase):
    def test_all_live_and_release_recipes_require_the_patched_toolchain(self):
        recipes = sorted((ROOT / "www-apps").glob("*/*.ebuild"))
        self.assertTrue(recipes)
        for recipe in recipes:
            with self.subTest(recipe=recipe.name):
                validate_toolchain(recipe.read_text())

    def test_removed_weakened_or_commented_dependencies_are_rejected(self):
        for dependency in ("", "dev-lang/go", ">=dev-lang/go-1.26", ">=dev-lang/go-1.26.0",
                           ">=dev-lang/go-1.26.10", ">=dev-lang/go-1.25.99",
                           "# >=dev-lang/go-1.26.11"):
            with self.subTest(dependency=dependency):
                with self.assertRaises(ValueError):
                    validate_toolchain('BDEPEND="\n' + dependency + '\n"')
        with self.assertRaises(ValueError):
            validate_toolchain('# BDEPEND="\n>=dev-lang/go-1.26.11\n"')

    def test_supported_patch_releases(self):
        for version in ("1.26.11", "1.26.12", "1.27.4"):
            validate_toolchain('BDEPEND+="\n>=dev-lang/go-' + version + '\n"')


if __name__ == "__main__":
    unittest.main()
