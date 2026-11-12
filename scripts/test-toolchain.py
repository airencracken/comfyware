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


def validate_oidc_license(text):
    match = re.search(r'^LICENSE="([^"\n]+)"', text, re.M)
    if match is None or 'Apache-2.0' not in match[1].split():
        raise ValueError('the OIDC verifier dependencies require Apache-2.0')


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

    def test_suite_releases_and_live_recipes_cover_oidc_dependency_licenses(self):
        versions = {'folkweave': '0.3.4', 'imvault': '0.22.2', 'songstead': '0.13.2',
                    'tidings': '0.5.4', 'witmoot': '0.20.2'}
        for app, version in versions.items():
            for release in (version, '9999'):
                recipe = ROOT / 'www-apps' / app / f'{app}-{release}.ebuild'
                text = recipe.read_text()
                with self.subTest(recipe=recipe.name):
                    validate_oidc_license(text)
                    validate_toolchain(text)

    def test_missing_commented_and_near_match_oidc_licenses_are_rejected(self):
        original = 'LICENSE="AGPL-3+ Apache-2.0 BSD MIT"'
        validate_oidc_license(original)
        for text in ('', original.replace('Apache-2.0', ''), '# ' + original,
                     original.replace('Apache-2.0', 'Apache-2'),
                     original.replace('Apache-2.0', 'Apache-2.0-or-later')):
            with self.subTest(text=text), self.assertRaises(ValueError):
                validate_oidc_license(text)

    def test_supported_patch_releases(self):
        for version in ("1.26.11", "1.26.12", "1.27.4"):
            validate_toolchain('BDEPEND+="\n>=dev-lang/go-' + version + '\n"')


if __name__ == "__main__":
    unittest.main()
