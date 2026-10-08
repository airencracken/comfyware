#!/usr/bin/env python3
"""Check that release recipes and thin Manifests describe the same distfiles."""

from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


def validate_manifest(lines, expected):
    errors = []
    names = []
    for line in lines:
        fields = line.split()
        if (len(fields) != 7 or fields[0] != "DIST"
                or not fields[2].isdigit() or int(fields[2]) <= 0
                or fields[3] != "BLAKE2B" or fields[5] != "SHA512"
                or any(not re.fullmatch(r"[0-9a-f]{128}", fields[i]) for i in (4, 6))):
            errors.append("Invalid DIST schema")
            continue
        names.append(fields[1])
    if len(names) != len(set(names)):
        errors.append("Duplicate distfile")
    if set(names) != expected:
        errors.append("Distfiles do not match release recipes")
    return errors


class ManifestTests(unittest.TestCase):
    def test_tracked_directories_are_categories_or_repository_infrastructure(self):
        allowed = {"metadata", "profiles", "scripts", "release-preparation"}
        allowed.update(path.parent.parent.name for path in ROOT.glob("*/*/metadata.xml"))
        paths = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
        directories = {path.split("/", 1)[0] for path in paths if "/" in path and not path.startswith(".")}
        self.assertEqual(directories - allowed, set(),
                         "A root directory would be treated as an unknown package category")

    def test_release_recipes_have_exact_distfiles(self):
        for app in ("imvault", "witmoot", "songstead"):
            with self.subTest(app=app):
                package = ROOT / "www-apps" / app
                expected = set()
                for recipe in package.glob(f"{app}-*.ebuild"):
                    version = recipe.stem.removeprefix(app + "-")
                    if version == "9999":
                        continue
                    self.assertRegex(version, r"^\d+\.\d+\.\d+(-r\d+)?$")
                    version = version.split("-r", 1)[0]
                    expected.update((f"{app}-{version}-deps.tar.xz",
                                     f"{app}_{version}_source.tar.gz"))
                self.assertEqual(validate_manifest((package / "Manifest").read_text().splitlines(), expected), [])

    def test_mutations_are_rejected(self):
        name = "imvault-1.2.3-deps.tar.xz"
        valid = f"DIST {name} 10 BLAKE2B {'a' * 128} SHA512 {'b' * 128}"
        self.assertEqual(validate_manifest([valid], {name}), [])
        mutations = [
            ([valid, valid], "Duplicate distfile"),
            ([], "Distfiles do not match"),
            ([valid.replace(name, "unexpected.tar.xz")], "Distfiles do not match"),
            ([valid.replace(" 10 ", " 0 ")], "Invalid DIST schema"),
            ([valid.replace("BLAKE2B", "SHA256")], "Invalid DIST schema"),
            ([valid.replace("b" * 128, "b" * 127)], "Invalid DIST schema"),
            ([valid.replace("a" * 128, "g" * 128)], "Invalid DIST schema"),
        ]
        for lines, error in mutations:
            with self.subTest(error=error, lines=lines):
                self.assertTrue(any(error in found for found in validate_manifest(lines, {name})))


if __name__ == "__main__":
    unittest.main(verbosity=2)
