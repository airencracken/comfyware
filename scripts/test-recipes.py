#!/usr/bin/env python3
"""Check recipe conventions, release/live parity, and the staged install check."""

from pathlib import Path
import os
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


def compile_arguments(recipe, app, version):
    """Execute the compile phase with a recording Go helper."""
    script = r"""
inherit() { :; }
ego() { printf '%s\0' "$@"; }
PN=$2
PV=$3
source "$1" || exit 1
src_compile || exit 1
"""
    result = subprocess.run(["bash", "-c", script, "compile-test", str(recipe), app, version],
                            check=True, capture_output=True)
    return result.stdout.decode().rstrip("\0").split("\0")


def validate_compiled_version(arguments, version):
    if arguments.count("-ldflags") != 1:
        raise ValueError("compile must stamp one version")
    if arguments[arguments.index("-ldflags") + 1] != "-X main.version=" + version:
        raise ValueError("compile stamped the wrong version")


class CompiledVersionTests(unittest.TestCase):
    def test_release_and_live_builds_report_the_package_version(self):
        for app in APPS:
            release = release_recipes(app)[-1]
            for recipe, version in [(release, release.stem.removeprefix(app + "-")),
                                    (release.parent / f"{app}-9999.ebuild", "9999")]:
                with self.subTest(recipe=recipe.name):
                    arguments = compile_arguments(recipe, app, version)
                    validate_compiled_version(arguments, version)
                    self.assertEqual(arguments[0], "build")
                    self.assertEqual(arguments[-1], f"./cmd/{app}")

    def test_missing_or_wrong_version_is_rejected(self):
        recipe = release_recipes("imvault")[-1]
        for text in [recipe.read_text().replace(' -ldflags "-X main.version=${PV}"', ''),
                     recipe.read_text().replace('-X main.version=${PV}', '-X main.version=old')]:
            with tempfile.TemporaryDirectory() as directory:
                broken = Path(directory) / "imvault.ebuild"
                broken.write_text(text)
                with self.assertRaises(ValueError):
                    validate_compiled_version(compile_arguments(broken, "imvault", "0.13.1"), "0.13.1")


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


LOOPBACK = "127.0.0.1/32,::1/128"


def run_rename(text, files, rounds=1):
    """Run the newest Imvault recipe's pkg_preinst against fixture files.

    files maps a path under /etc to its contents (None for absent). Returns the
    resulting contents, backups, and the log, after the given number of runs.
    """
    import re as _re
    functions = _re.findall(r"^(imvault_rename_trusted_proxies\(\) \{.*?^\}|pkg_preinst\(\) \{.*?^\})",
                            text, _re.MULTILINE | _re.DOTALL)
    if len(functions) != 2:
        raise AssertionError("the recipe has no rename function and pkg_preinst")
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        for name, content in files.items():
            if content is not None:
                path = root / name.lstrip("/")
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
                path.chmod(0o600)
        script = "\n".join([
            "die() { printf 'die: %s\\n' \"$*\" >&2; exit 1; }",
            "elog() { printf 'elog: %s\\n' \"$*\"; }",
            f"EROOT={root}", "PV=0.12.0", *functions,
            *(["pkg_preinst || exit 1"] * rounds),
        ])
        result = subprocess.run(["bash", "-c", script], capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            raise AssertionError(result.stderr)
        state = {}
        for path in sorted(p for p in root.rglob("*") if p.is_file()):
            state["/" + str(path.relative_to(root))] = (path.read_text(), path.stat().st_mode & 0o777)
        return state, result.stdout


class TrustedProxyRename(unittest.TestCase):
    """The 0.12.0 recipe renames the setting the new server refuses."""

    def setUp(self):
        self.text = release_recipes("imvault")[-1].read_text()

    def rename(self, line, rounds=1):
        state, log = run_rename(self.text, {"/etc/conf.d/imvault": f"IMVAULT_ADDR=127.0.0.1:8080\n{line}\n"}, rounds)
        return state["/etc/conf.d/imvault"][0].splitlines()[1], state, log

    def test_true_becomes_the_loopback_proxy(self):
        for line, want in {
            "IMVAULT_TRUST_PROXY_HEADERS=true": f'IMVAULT_TRUSTED_PROXIES="{LOOPBACK}"',
            'IMVAULT_TRUST_PROXY_HEADERS="TRUE"': f'IMVAULT_TRUSTED_PROXIES="{LOOPBACK}"',
            "export IMVAULT_TRUST_PROXY_HEADERS='1'": f'export IMVAULT_TRUSTED_PROXIES="{LOOPBACK}"',
            "  IMVAULT_TRUST_PROXY_HEADERS=t  # behind caddy": f'  IMVAULT_TRUSTED_PROXIES="{LOOPBACK}"',
        }.items():
            with self.subTest(line=line):
                self.assertEqual(self.rename(line)[0], want)

    def test_other_values_trusted_nobody_and_are_commented_out(self):
        for line in ("IMVAULT_TRUST_PROXY_HEADERS=false", "IMVAULT_TRUST_PROXY_HEADERS=",
                     "IMVAULT_TRUST_PROXY_HEADERS=yes", 'IMVAULT_TRUST_PROXY_HEADERS="$(id)"'):
            with self.subTest(line=line):
                renamed = self.rename(line)[0]
                self.assertTrue(renamed.startswith("# Removed by the 0.12.0 upgrade"), renamed)
                self.assertTrue(renamed.endswith(line), renamed)

    def test_the_shipped_comment_becomes_the_new_example(self):
        self.assertEqual(self.rename("# IMVAULT_TRUST_PROXY_HEADERS=true")[0],
                         f"# IMVAULT_TRUSTED_PROXIES={LOOPBACK}")

    def test_both_configuration_files_are_renamed_and_backed_up(self):
        files = {"/etc/conf.d/imvault": "IMVAULT_TRUST_PROXY_HEADERS=true\n",
                 "/etc/imvault/imvault.env": "IMVAULT_TRUST_PROXY_HEADERS=true\n"}
        state, log = run_rename(self.text, files)
        for name, original in files.items():
            self.assertEqual(state[name][0], f'IMVAULT_TRUSTED_PROXIES="{LOOPBACK}"\n')
            self.assertEqual(state[name + ".pre-0.12.0"], (original, 0o600), "backup keeps contents and mode")
            self.assertIn(name, log)

    def test_the_result_is_what_the_server_reads(self):
        state, _ = run_rename(self.text, {"/etc/conf.d/imvault": "IMVAULT_TRUST_PROXY_HEADERS=true\n"})
        with tempfile.NamedTemporaryFile("w", suffix=".sh") as config:
            config.write(state["/etc/conf.d/imvault"][0])
            config.flush()
            value = subprocess.run(["sh", "-c", f'. "{config.name}" && printf %s "$IMVAULT_TRUSTED_PROXIES"'],
                                   capture_output=True, text=True, check=True).stdout
        self.assertEqual(value, LOOPBACK)
        self.assertNotIn("IMVAULT_TRUST_PROXY_HEADERS=", state["/etc/conf.d/imvault"][0].replace("# Removed", ""))

    def test_untouched_files_and_reinstalls_change_nothing(self):
        state, log = run_rename(self.text, {"/etc/conf.d/imvault": "IMVAULT_ADDR=127.0.0.1:8080\n",
                                            "/etc/imvault/imvault.env": None})
        self.assertEqual(list(state), ["/etc/conf.d/imvault"], "no backup or new file")
        self.assertEqual(log, "")
        for line in ("IMVAULT_TRUST_PROXY_HEADERS=true", "IMVAULT_TRUST_PROXY_HEADERS=false"):
            with self.subTest(line=line):
                once = self.rename(line)
                twice = self.rename(line, rounds=2)
                self.assertEqual(once[0], twice[0])
                self.assertEqual(twice[1]["/etc/conf.d/imvault.pre-0.12.0"][0],
                                 f"IMVAULT_ADDR=127.0.0.1:8080\n{line}\n", "a second run kept the first backup")
                self.assertEqual(twice[2].count("elog:"), 1)

    def test_mutations_are_caught(self):
        mutations = {
            "no rename in preinst": self.text.replace(
                '\timvault_rename_trusted_proxies "${EROOT}/etc/conf.d/imvault"\n', ""),
            "true not recognised": self.text.replace("(1|t|T|TRUE|true|True)", "(yes)"),
            "matches any mention": self.text.replace(
                "grep -Eq '^[[:space:]]*(#[[:space:]]*)?(export[[:space:]]+)?IMVAULT_TRUST_PROXY_HEADERS=' ",
                "grep -q 'IMVAULT_TRUST_PROXY_HEADERS' "),
        }
        for name, mutated in mutations.items():
            with self.subTest(mutation=name):
                self.assertNotEqual(mutated, self.text, "mutation did not apply")
                suite = unittest.TestSuite()
                for test in ("test_true_becomes_the_loopback_proxy", "test_both_configuration_files_are_renamed_and_backed_up",
                             "test_untouched_files_and_reinstalls_change_nothing"):
                    case = TrustedProxyRename(test)
                    case.setUp = (lambda c=case, m=mutated: setattr(c, "text", m))
                    suite.addTest(case)
                with open(os.devnull, "w") as output:
                    result = unittest.TextTestRunner(stream=output).run(suite)
                self.assertFalse(result.wasSuccessful(), "mutation survived")


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
    if app == "imvault":
        files.update({
            "contrib/systemd/imvault-backup.service": "[Service]\nExecStart=/usr/local/bin/imvault backup --output-dir /var/backups/imvault --keep 7\n",
            "contrib/systemd/imvault-backup.timer": "[Timer]\nOnCalendar=*-*-* 03:00:00\n",
            "contrib/cron/imvault-backup": "17 3 * * * root /usr/bin/imvault backup --output-dir /var/backups/imvault --keep 7\n",
        })
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
