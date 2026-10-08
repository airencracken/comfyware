#!/usr/bin/env python3
"""Validate optional Bubblewrap dependencies and local USE metadata."""

from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
APPS = ("imvault", "witmoot", "songstead")


def recipes(app):
    """Every release and live recipe, so new versions are checked without edits."""
    return sorted(path for path in (ROOT / "www-apps" / app).glob(f"{app}-*.ebuild")
                  if app != "songstead" or path.name != "songstead-0.1.0.ebuild")


def validate_recipe(text):
    flags = re.search(r'^IUSE="([^"]*)"', text, re.MULTILINE)
    if not flags or "bubblewrap" not in flags[1].split():
        raise ValueError("Bubblewrap must be an optional, disabled-by-default USE flag")
    dependencies = re.search(r'^RDEPEND="([^"]*)"', text, re.MULTILINE)
    # --disable-userns, which the service policy passes, arrived in 0.8.
    conditional = r'bubblewrap\?\s*\(\s*>=sys-apps/bubblewrap-0\.8\[-suid\(-\)\]\s*\)'
    if not dependencies or not re.search(conditional, dependencies[1]):
        raise ValueError("Bubblewrap dependency must be conditional, at least 0.8, and reject setuid builds")
    # Nothing else may pull Bubblewrap in when the flag is off.
    for name in ("RDEPEND", "DEPEND", "BDEPEND", "PDEPEND"):
        for value in re.findall(rf'^{name}\+?="([^"]*)"', text, re.MULTILINE):
            if "sys-apps/bubblewrap" in re.sub(conditional, "", value):
                raise ValueError(f"{name} pulls in Bubblewrap without the USE flag")


def validate_metadata(text):
    tree = ET.fromstring(text)
    flags = tree.findall("./use/flag[@name='bubblewrap']")
    if len(flags) != 1 or not (flags[0].text or "").strip():
        raise ValueError("Bubblewrap needs exactly one nonempty USE description")


class SandboxPackaging(unittest.TestCase):
    def test_release_and_live_recipes(self):
        for app in APPS:
            found = recipes(app)
            self.assertTrue(any(r.stem.endswith("-9999") for r in found), f"{app} has no live recipe")
            self.assertGreater(len(found), 1, f"{app} has no release recipe")
            for recipe in found:
                with self.subTest(recipe=recipe.name):
                    validate_recipe(recipe.read_text())

    def test_use_metadata(self):
        for app in APPS:
            validate_metadata((ROOT / "www-apps" / app / "metadata.xml").read_text())

    def test_recipe_mutations(self):
        text = next(r for r in recipes("imvault") if not r.stem.endswith("-9999")).read_text()
        for broken in (
            text.replace('IUSE="bubblewrap', 'IUSE="+bubblewrap'),
            text.replace("bubblewrap? (", ""),
            text.replace("[-suid(-)]", ""),
            text.replace("sys-apps/bubblewrap", "sys-apps/not-bubblewrap"),
            text.replace(">=sys-apps/bubblewrap-0.8", "sys-apps/bubblewrap"),
            text.replace(">=sys-apps/bubblewrap-0.8", ">=sys-apps/bubblewrap-0.7"),
            text.replace('BDEPEND+="\n', 'BDEPEND+="\n\tsys-apps/bubblewrap\n', 1),
            text.replace('RDEPEND="\n', 'RDEPEND="\n\tsys-apps/bubblewrap\n', 1),
        ):
            with self.assertRaises(ValueError):
                validate_recipe(broken)

    def test_metadata_schema_rejects_missing_duplicate_or_empty_description(self):
        for text in (
            "<pkgmetadata/>",
            '<pkgmetadata><use><flag name="bubblewrap"/></use></pkgmetadata>',
            '<pkgmetadata><use><flag name="bubblewrap">a</flag><flag name="bubblewrap">b</flag></use></pkgmetadata>',
        ):
            with self.assertRaises(ValueError):
                validate_metadata(text)


if __name__ == "__main__":
    unittest.main()
