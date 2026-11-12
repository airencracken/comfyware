#!/usr/bin/env python3
"""Keep the release catalog, current recipes and installation table aligned."""
import copy
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
APPS = ("folkweave", "imvault", "songstead", "tidings", "witmoot")
NAMES = set(APPS) | {"comfylib", "comfylib/oidc", "arise"}
VERSION = re.compile(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\Z")


def validate(value, root):
    if (not isinstance(value, dict) or set(value) != {"schema", "releases"}
            or type(value["schema"]) is not int or value["schema"] != 1
            or not isinstance(value["releases"], dict) or set(value["releases"]) != NAMES):
        raise ValueError("Invalid release catalog schema")
    for name, version in value["releases"].items():
        if not isinstance(version, str) or not VERSION.fullmatch(version):
            raise ValueError("Invalid release version")
        if name in APPS:
            recipes = [p for p in (root / "www-apps" / name).glob(name + "-*.ebuild")
                       if not p.name.endswith("-9999.ebuild")]
            versions = [p.stem.removeprefix(name + "-").split("-r")[0] for p in recipes]
            if not versions or max(versions, key=lambda v: tuple(map(int, v.split(".")))) != version:
                raise ValueError("Current recipe differs from release catalog")
            expected = f"| `www-apps/{name}` | `{version}` |"
            if expected not in (root / "README.md").read_text():
                raise ValueError("Installation table differs from release catalog")


class CatalogTests(unittest.TestCase):
    def test_current_release_contract(self):
        validate(json.loads((ROOT / "release-catalog.json").read_text()), ROOT)

    def test_schema_and_version_mutations_are_rejected(self):
        original = json.loads((ROOT / "release-catalog.json").read_text())
        cases = []
        for version in (None, True, 1, "01.2.3", "1.2", "1.2.3\n", "../1.2.3", "1.2.3;id", "999.999.999"):
            value = copy.deepcopy(original)
            value["releases"]["imvault"] = version
            cases.append(value)
        for key in NAMES:
            value = copy.deepcopy(original)
            del value["releases"][key]
            cases.append(value)
        for schema in (True, 0, 2, "1"):
            value = copy.deepcopy(original)
            value["schema"] = schema
            cases.append(value)
        for value in cases:
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate(value, ROOT)


if __name__ == "__main__":
    unittest.main(verbosity=2)
