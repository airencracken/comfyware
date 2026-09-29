#!/usr/bin/env python3
"""Regression tests for complete, exclusive dependency bundle publication."""

from pathlib import Path
import os
import subprocess
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PublicationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.work = Path(temporary.name)
        source = self.work / "source"
        source.mkdir()
        (source / "go.mod").write_text("module example.org/test\n\ngo 1.26.0\n")
        (source / "go.sum").write_text("")
        self.archive = self.work / "source.tar.gz"
        with tarfile.open(self.archive, "w:gz") as tar:
            tar.add(source, arcname="source")
        self.output = self.work / "output"
        self.output.mkdir()
        self.target = self.output / "imvault-1.2.3-deps.tar.xz"
        self.binary = self.work / "bin"
        self.binary.mkdir()

    def run_bundle(self, script):
        go = self.binary / "go"
        go.write_text("#!/bin/sh\n" + script)
        go.chmod(0o755)
        result = subprocess.run(
            ["bash", str(ROOT / "scripts/make-deps.sh"), "imvault", "1.2.3",
             str(self.archive), str(self.output)],
            env={**os.environ, "PATH": f"{self.binary}:{os.environ['PATH']}",
                 "PUBLICATION_TARGET": str(self.target)},
            capture_output=True, timeout=10,
        )
        self.assertEqual(list(self.output.glob(".make-deps.*")), [],
                         "temporary staging was left behind")
        return result

    def test_publication_does_not_replace_a_concurrent_output(self):
        result = self.run_bundle('''
if [ "$2" = download ]; then
    mkdir -p "$GOMODCACHE" || exit 1
    printf 'concurrent published bytes\\n' > "$PUBLICATION_TARGET" || exit 1
fi
exit 0
''')
        self.assertEqual(self.target.read_bytes(), b"concurrent published bytes\n",
                         "publication overwrote a file created after its existence check")
        self.assertNotEqual(result.returncode, 0)

    def test_success_publishes_a_complete_verified_cache(self):
        result = self.run_bundle('''
mkdir -p "$GOMODCACHE" || exit 1
if [ "$2" = download ]; then
    printf 'module bytes\\n' > "$GOMODCACHE/module" || exit 1
elif [ "$2" = verify ]; then
    printf 'verification finished\\n' > "$GOMODCACHE/verified" || exit 1
fi
''')
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        with tarfile.open(self.target, "r:xz") as tar:
            self.assertEqual(tar.extractfile("go-mod/module").read(), b"module bytes\n")
            self.assertEqual(tar.extractfile("go-mod/verified").read(), b"verification finished\n")
            for member in tar.getmembers():
                self.assertEqual((member.uid, member.gid, member.mtime), (0, 0, 0))

    def test_verification_failure_publishes_nothing(self):
        result = self.run_bundle('''
mkdir -p "$GOMODCACHE" || exit 1
if [ "$2" = verify ]; then exit 1; fi
''')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.target.exists())

    def test_dependency_resolution_cannot_mutate_module_files(self):
        for name in ("go.mod", "go.sum"):
            with self.subTest(name=name):
                result = self.run_bundle(f'''
mkdir -p "$GOMODCACHE" || exit 1
printf 'changed\\n' >> {name} || exit 1
''')
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(f"changed {name}".encode(), result.stderr)
                self.assertFalse(self.target.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
