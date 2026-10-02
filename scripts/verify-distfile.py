#!/usr/bin/env python3
"""Verify a downloaded distfile against the size and hashes in a Manifest.

Usage: verify-distfile.py MANIFEST FILE

This is the check Portage makes before unpacking, so CI tests exactly the bytes
users will build. Run without arguments to test the verifier itself.
"""

from pathlib import Path
import hashlib
import sys
import tempfile
import unittest


def manifest_entry(manifest_text, name):
    """Return (size, {hash: digest}) for one DIST entry."""
    for line in manifest_text.splitlines():
        fields = line.split()
        if len(fields) >= 3 and fields[0] == "DIST" and fields[1] == name:
            if len(fields) % 2 != 1:
                raise ValueError(f"{name}: malformed Manifest entry")
            return int(fields[2]), dict(zip(fields[3::2], fields[4::2]))
    raise ValueError(f"{name}: not listed in the Manifest")


def verify(manifest_text, path):
    size, digests = manifest_entry(manifest_text, path.name)
    if {"BLAKE2B", "SHA512"} - digests.keys():
        raise ValueError(f"{path.name}: Manifest lacks BLAKE2B or SHA512")
    actual_size = path.stat().st_size
    if actual_size != size:
        raise ValueError(f"{path.name}: size {actual_size} does not match Manifest size {size}")
    blake, sha = hashlib.blake2b(), hashlib.sha512()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            blake.update(block)
            sha.update(block)
    for name, actual in (("BLAKE2B", blake.hexdigest()), ("SHA512", sha.hexdigest())):
        if actual != digests[name].lower():
            raise ValueError(f"{path.name}: {name} does not match the Manifest")


class VerifierTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.file = Path(directory.name) / "app_1.0.0_source.tar.gz"
        self.file.write_bytes(b"release bytes\n")
        data = self.file.read_bytes()
        self.entry = (f"DIST {self.file.name} {len(data)} BLAKE2B {hashlib.blake2b(data).hexdigest()} "
                      f"SHA512 {hashlib.sha512(data).hexdigest()}")

    def test_matching_file_passes(self):
        verify(f"DIST other 1 BLAKE2B a SHA512 b\n{self.entry}\n", self.file)

    def test_mutations_are_rejected(self):
        cases = {
            "not listed": "",
            "size": self.entry.replace(" 14 ", " 15 "),
            "BLAKE2B does not match": self.entry.replace("BLAKE2B ", "BLAKE2B 0", 1),
            "SHA512 does not match": self.entry.replace("SHA512 ", "SHA512 0", 1),
            "lacks BLAKE2B": self.entry.replace("BLAKE2B", "SHA256"),
            "malformed": self.entry + " extra",
        }
        for expected, manifest in cases.items():
            with self.subTest(expected=expected):
                with self.assertRaisesRegex(ValueError, expected):
                    verify(manifest, self.file)

    def test_changed_bytes_are_rejected(self):
        self.file.write_bytes(b"release bytez\n")
        with self.assertRaisesRegex(ValueError, "BLAKE2B does not match"):
            verify(self.entry, self.file)


def main(arguments):
    if not arguments:
        unittest.main(argv=[sys.argv[0]], verbosity=2)
        return 0
    if len(arguments) != 2:
        print(__doc__.strip().splitlines()[2], file=sys.stderr)
        return 2
    try:
        verify(Path(arguments[0]).read_text(), Path(arguments[1]))
    except (OSError, ValueError) as error:
        print(error, file=sys.stderr)
        return 1
    print(f"{Path(arguments[1]).name}: matches the Manifest")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
