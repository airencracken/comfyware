#!/usr/bin/env python3
"""Check recipe conventions, release/live parity, and the staged install check."""

from pathlib import Path
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
APPS = ("imvault", "witmoot")
VERSION = re.compile(r"^(\d+\.\d+\.\d+)(-r\d+)?$")


def release_recipes(app):
    """Return the release recipes for an app, oldest first."""
    found = []
    for recipe in (ROOT / "www-apps" / app).glob(f"{app}-*.ebuild"):
        version = recipe.stem.removeprefix(app + "-")
        if version == "9999":
            continue
        match = VERSION.fullmatch(version)
        if not match:
            raise ValueError(f"{recipe.name}: unexpected version {version!r}")
        found.append((tuple(int(part) for part in match[1].split(".")), recipe))
    return [recipe for _, recipe in sorted(found)]


def recipe_errors(text):
    """Return the convention violations in one recipe's text."""
    errors = []
    compile_phase = re.search(r"^src_compile\(\) \{\n(.*?)^\}", text, re.MULTILINE | re.DOTALL)
    if not compile_phase:
        errors.append("missing src_compile")
    else:
        body = compile_phase[1]
        if re.search(r"-ldflags=[\"']?[^\n]*-[sw]\b", body):
            errors.append("binary is stripped before Portage can split debug information")
        if "CGO_ENABLED=0" not in body:
            errors.append("build does not disable cgo")
        if "-buildvcs=false" in body:
            errors.append("-buildvcs=false duplicates the eclass GOFLAGS")
    if 'docompress -x "/usr/share/doc/${PF}/examples"' not in text:
        errors.append("proxy examples would be compressed")
    if re.search(r"^DOCS=\([^)]*\bLICENSE\b", text, re.MULTILINE):
        errors.append("license texts belong in LICENSE, not DOCS")
    if re.search(r'^KEYWORDS=""', text, re.MULTILINE):
        errors.append("empty KEYWORDS is redundant")
    return errors


def live_equivalent(release_text, app):
    """Translate a release recipe into the live recipe it should match."""
    text = release_text.replace(
        "# SPDX-License-Identifier: AGPL-3.0-or-later\n",
        "# SPDX-License-Identifier: AGPL-3.0-or-later\n# Live ebuild for the master branch.\n", 1)
    text = text.replace("inherit go-module systemd", "inherit git-r3 go-module systemd", 1)
    text = re.sub(r'SRC_URI="\n.*?"\nS="\$\{WORKDIR\}/\$\{PN\}_\$\{PV\}_source"\n',
                  f'EGIT_REPO_URI="https://github.com/airencracken/{app}.git"\nEGIT_BRANCH="master"\n',
                  text, count=1, flags=re.DOTALL)
    text = text.replace('KEYWORDS="~amd64 ~arm64"\n',
                        '# go-module_live_vendor refuses to run without this.\nPROPERTIES="live"\n', 1)
    text = text.replace(
        "src_configure() {",
        "src_unpack() {\n\tgit-r3_src_unpack\n"
        "\t# Vendor the modules from go.mod so the build itself needs no network.\n"
        "\tgo-module_live_vendor\n}\n\nsrc_configure() {", 1)
    return text.replace("/tree/v${PV}/docs", "/tree/master/docs")


class RecipeConventions(unittest.TestCase):
    def test_every_recipe_follows_conventions(self):
        for app in APPS:
            for recipe in (ROOT / "www-apps" / app).glob("*.ebuild"):
                with self.subTest(recipe=recipe.name):
                    self.assertEqual(recipe_errors(recipe.read_text()), [])

    def test_live_recipe_matches_newest_release(self):
        for app in APPS:
            with self.subTest(app=app):
                newest = release_recipes(app)[-1]
                live = ROOT / "www-apps" / app / f"{app}-9999.ebuild"
                self.assertEqual(live.read_text(), live_equivalent(newest.read_text(), app),
                                 f"{live.name} drifted from {newest.name}")

    def test_convention_mutations_are_rejected(self):
        text = release_recipes("witmoot")[-1].read_text()
        mutations = {
            "binary is stripped": text.replace("ego build -trimpath",
                                               'ego build -trimpath -ldflags="-s -w"'),
            "does not disable cgo": text.replace("CGO_ENABLED=0 ego", "ego"),
            "duplicates the eclass": text.replace("-trimpath", "-buildvcs=false -trimpath"),
            "would be compressed": text.replace('docompress -x "/usr/share/doc/${PF}/examples"', ""),
            "license texts": text.replace("DOCS=( README.md", "DOCS=( LICENSE README.md"),
            "empty KEYWORDS": text + 'KEYWORDS=""\n',
        }
        for expected, mutated in mutations.items():
            with self.subTest(mutation=expected):
                self.assertNotEqual(mutated, text, "mutation did not apply")
                self.assertTrue(any(expected in error for error in recipe_errors(mutated)))

    def test_parity_detects_drift(self):
        text = release_recipes("imvault")[-1].read_text()
        live = live_equivalent(text, "imvault")
        self.assertNotEqual(live_equivalent(text.replace("fperms 0600", "fperms 0644"), "imvault"), live)


def readme_errors(readme, newest):
    """Return README claims that disagree with the newest release recipes."""
    errors = []
    for app, version in newest.items():
        if f"| `www-apps/{app}` | `{version}` |" not in readme:
            errors.append(f"package table does not list {app} {version}")
        for pinned in re.findall(rf"github\.com/airencracken/{app}/blob/v([0-9.]+)/", readme):
            if pinned != version:
                errors.append(f"{app} link pinned to v{pinned}, not v{version}")
    if re.search(r"\bimvault\b", prose(readme)):
        errors.append("Imvault is capitalised in prose")
    return errors


def prose(markdown):
    """Drop code, link targets, and URLs, where lowercase names are literal."""
    markdown = re.sub(r"```.*?```", "", markdown, flags=re.DOTALL)
    markdown = re.sub(r"`[^`]*`", "", markdown)
    markdown = re.sub(r"\]\([^)]*\)", "]", markdown)
    return re.sub(r"https?://\S+", "", markdown)


def newest_versions():
    return {app: release_recipes(app)[-1].stem.removeprefix(app + "-").split("-r", 1)[0] for app in APPS}


class ReadmeConsistency(unittest.TestCase):
    def test_readme_matches_newest_releases(self):
        self.assertEqual(readme_errors((ROOT / "README.md").read_text(), newest_versions()), [])

    def test_literal_names_are_allowed(self):
        readme = "Run `imvault --help`, see [Imvault](https://github.com/airencracken/imvault).\n"
        self.assertEqual(readme_errors(readme, {}), [])

    def test_stale_claims_are_rejected(self):
        readme = (ROOT / "README.md").read_text()
        newest = newest_versions()
        version = newest["witmoot"]
        mutations = {
            "package table": readme.replace(f"`www-apps/witmoot` | `{version}`", "`www-apps/witmoot` | `0.0.1`"),
            "pinned to": readme.replace(f"witmoot/blob/v{version}/", "witmoot/blob/v0.0.1/", 1),
            "capitalised": readme + "\nInstall imvault first.\n",
        }
        for expected, mutated in mutations.items():
            with self.subTest(mutation=expected):
                self.assertNotEqual(mutated, readme, "mutation did not apply")
                self.assertTrue(any(expected in error for error in readme_errors(mutated, newest)))


def write_fixture(source, app, bin_default):
    """Create the contrib files src_install reads, shaped like upstream's."""
    upper = app.upper()
    files = {
        f"contrib/openrc/{app}": f'#!/sbin/openrc-run\n: "${{{upper}_BIN:={bin_default}}}"\n'
                                 f'command="${{{upper}_BIN}}"\n',
        f"contrib/openrc/{app}.confd": f"# {upper}_ADDR=127.0.0.1:8080\n",
        f"contrib/logrotate/{app}": f"/var/log/{app}.log {{\n\tweekly\n}}\n",
        f"contrib/systemd/{app}.service": "[Service]\nStandardOutput=journal\nStandardError=journal\n"
                                          f"SyslogIdentifier={app}\nExecStart=/usr/local/bin/{app}\n",
        f"contrib/systemd/{app}.env": f"# {upper}_ADDR=127.0.0.1:8080\n",
    }
    for name, content in files.items():
        path = source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)


class StagedInstallCheck(unittest.TestCase):
    """The install check must reject the packaging regressions it exists for."""

    def run_check(self, app, text, bin_default):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            source = work / "source"
            write_fixture(source, app, bin_default)
            recipe = work / app / f"{app}-1.2.3.ebuild"
            recipe.parent.mkdir()
            recipe.write_text(text)
            return subprocess.run(["bash", str(ROOT / "scripts/test-install.sh"), str(recipe), str(source)],
                                  capture_output=True, text=True, timeout=30)

    def test_current_recipes_pass(self):
        for app, default in (("imvault", "/usr/bin/imvault"), ("witmoot", "/usr/local/bin/witmoot")):
            for recipe in (release_recipes(app)[-1], ROOT / "www-apps" / app / f"{app}-9999.ebuild"):
                with self.subTest(recipe=recipe.name):
                    result = self.run_check(app, recipe.read_text(), default)
                    self.assertEqual(result.returncode, 0, result.stderr)

    def test_mutations_are_caught(self):
        text = release_recipes("witmoot")[-1].read_text()
        initd_rewrite = ("\tsed 's|/usr/local/bin/witmoot|/usr/bin/witmoot|g' \\\n"
                         "\t\tcontrib/openrc/witmoot > \"${T}/witmoot.initd\" || die\n"
                         "\tnewinitd \"${T}/witmoot.initd\" witmoot\n")
        mutations = {
            "/usr/local/bin": text.replace(initd_rewrite, "\tnewinitd contrib/openrc/witmoot witmoot\n"),
            "compressed": text.replace('\tdocompress -x "/usr/share/doc/${PF}/examples"\n', ""),
            "mode 0600": text.replace("fperms 0600 /etc/conf.d/witmoot", "fperms 0644 /etc/conf.d/witmoot"),
            "world-readable": text.replace("fperms 0600 /etc/witmoot/witmoot.env",
                                           "fperms 0644 /etc/witmoot/witmoot.env"),
            "systemd executable": text.replace("contrib/systemd/witmoot.service > ",
                                               "contrib/systemd/witmoot.service | sed 's|/usr/bin|/opt|' > "),
            "logrotate": text.replace("\tapp-admin/logrotate\n\tapp-misc", "\tapp-misc"),
        }
        for expected, mutated in mutations.items():
            with self.subTest(mutation=expected):
                self.assertNotEqual(mutated, text, "mutation did not apply")
                result = self.run_check("witmoot", mutated, "/usr/local/bin/witmoot")
                self.assertNotEqual(result.returncode, 0, "mutation survived")
                self.assertIn(expected, result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
