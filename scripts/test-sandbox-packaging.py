#!/usr/bin/env python3
"""Validate optional Bubblewrap dependencies and local USE metadata."""

from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
VERSIONS = {"imvault": "0.11.0", "witmoot": "0.9.0"}


def validate_recipe(text):
    flags = re.search(r'^IUSE="([^"]*)"', text, re.MULTILINE)
    if not flags or "bubblewrap" not in flags[1].split():
        raise ValueError("Bubblewrap must be an optional, disabled-by-default USE flag")
    dependencies = re.search(r'^RDEPEND="([^"]*)"', text, re.MULTILINE)
    if not dependencies or not re.search(
        r'bubblewrap\?\s*\(\s*sys-apps/bubblewrap\[-suid\(-\)\]\s*\)', dependencies[1]
    ):
        raise ValueError("Bubblewrap dependency must be conditional and reject setuid builds")


def validate_metadata(text):
    tree = ET.fromstring(text)
    flags = tree.findall("./use/flag[@name='bubblewrap']")
    if len(flags) != 1 or not (flags[0].text or "").strip():
        raise ValueError("Bubblewrap needs exactly one nonempty USE description")


class SandboxPackaging(unittest.TestCase):
    def test_release_and_live_recipes(self):
        for app, version in VERSIONS.items():
            for release in (version, "9999"):
                with self.subTest(app=app, version=release):
                    validate_recipe((ROOT / "www-apps" / app / f"{app}-{release}.ebuild").read_text())

    def test_use_metadata(self):
        for app in VERSIONS:
            validate_metadata((ROOT / "www-apps" / app / "metadata.xml").read_text())

    def test_recipe_mutations(self):
        text = (ROOT / "www-apps/imvault/imvault-0.11.0.ebuild").read_text()
        for broken in (
            text.replace('IUSE="bubblewrap', 'IUSE="+bubblewrap'),
            text.replace("bubblewrap? (", ""),
            text.replace("[-suid(-)]", ""),
            text.replace("sys-apps/bubblewrap", "sys-apps/not-bubblewrap"),
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
