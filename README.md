# comfyware

Gentoo packages for Imvault and Witmoot: apps you can host for friends, family,
and small communities.

| Package | Release | What it does |
| --- | --- | --- |
| `www-apps/imvault` | `0.11.1` | [imvault](https://github.com/airencracken/imvault), a home for your group's photos and clips |
| `www-apps/witmoot` | `0.9.0` | [Witmoot](https://github.com/airencracken/witmoot), a small bulletin board for friends and family |

Release ebuilds build the published source archives with checksummed Go dependency
bundles; compilation does not need network access. Both also have **live `9999`
ebuilds** that build upstream `master` and fetch dependencies during unpack.
Go 1.26 or newer is required and pulled in by Portage.

Also made here: [Arise](https://github.com/airencracken/arise), experimental
Gentoo package tooling in Go. It brings package search, dependency resolution,
repository sync, builds, and recovery tools together in one binary, using your
existing Portage configuration. Find installation instructions in the
[Arise overlay](https://github.com/airencracken/arise-overlay). The commands below
use Portage; Arise can work with configured overlays too. Keep Portage installed
while Arise's compatibility work continues.

## Add the overlay

Run these commands as root:

```sh
emerge --ask app-eselect/eselect-repository dev-vcs/git
eselect repository add comfyware git https://github.com/airencracken/comfyware.git
emaint sync -r comfyware
```

This is a custom overlay; it does not need to be in Gentoo's central repository
list. If you manage `repos.conf` yourself, use this instead in
`/etc/portage/repos.conf/comfyware.conf`:

```ini
[comfyware]
location = /var/db/repos/comfyware
sync-type = git
sync-uri = https://github.com/airencracken/comfyware.git
auto-sync = yes
```

Then run `emaint sync -r comfyware`.

## Install

The packages currently use testing keywords for amd64 and arm64. Add the following to
`/etc/portage/package.accept_keywords/comfyware` (create the parent directory
if your configuration uses directories):

```text
www-apps/imvault::comfyware ~*
www-apps/witmoot::comfyware ~*
acct-user/imvault::comfyware ~*
acct-group/imvault::comfyware ~*
acct-user/witmoot::comfyware ~*
acct-group/witmoot::comfyware ~*
```

Keep the lines for the applications you install. `~*` accepts their testing
keywords while leaving unkeyworded live builds disabled. Review any additional
keyword or license changes Portage requests for dependencies.

For video thumbnails and duration checks, add this to
`/etc/portage/package.use/comfyware`:

```text
www-apps/imvault ffmpeg
```

For optional Bubblewrap confinement, add `bubblewrap` to each application's
USE flags. This installs a non-setuid launcher; enable confinement separately
in the service settings. Imvault's stricter media sandbox also needs `ffmpeg`.
See the [Imvault setup](https://github.com/airencracken/imvault/blob/v0.11.0/docs/sandbox.md)
or [Witmoot setup](https://github.com/airencracken/witmoot/blob/v0.9.0/docs/sandbox.md)
for OpenRC settings, systemd overrides and verification.

Install either application or both:

```sh
emerge --ask www-apps/imvault::comfyware www-apps/witmoot::comfyware
```

The packages provide dedicated service accounts, `/usr/bin` binaries, OpenRC
and systemd service definitions, configuration files, and logrotate rules.
They do not enable or start services for you.

| Application | OpenRC configuration | systemd configuration | Data directory |
| --- | --- | --- | --- |
| imvault | `/etc/conf.d/imvault` | `/etc/imvault/imvault.env` | `/var/lib/imvault` |
| Witmoot | `/etc/conf.d/witmoot` | `/etc/witmoot/witmoot.env` | `/var/lib/witmoot` |

Configure your hostname and reverse proxy, and provision the administrator or
owner before starting. Set `IMVAULT_ADDR="127.0.0.1:8080"` in imvault's service
configuration; Witmoot's native service defaults to `127.0.0.1:8082`.
Use `/usr/bin/imvault` or `/usr/bin/witmoot` in the provisioning commands.

Caddy is the recommended reverse proxy, with automatic HTTPS. nginx and Apache
are supported too; both applications install examples for all three under
`/usr/share/doc/PACKAGE-VERSION/examples/`, alongside their deployment guides:

- [imvault proxy setup](https://github.com/airencracken/imvault/blob/master/docs/reverse-proxies.md)
- [Witmoot proxy setup](https://github.com/airencracken/witmoot/blob/master/docs/reverse-proxies.md)

- [imvault deployment and administrator setup](https://github.com/airencracken/imvault/blob/master/docs/deployment.md)
- [Witmoot deployment and owner setup](https://github.com/airencracken/witmoot/blob/master/docs/deployment.md)

Run `imvault --help` or `witmoot --help` for commands, environment settings,
and service paths. Generate a site configuration for your hostname with:

```sh
imvault proxy-config caddy --domain img.example.com > imvault.Caddyfile
witmoot proxy-config caddy --domain board.example.org > witmoot.Caddyfile
```

Substitute `nginx` or `apache` for either helper. These commands print a config
and the matching application settings; follow the proxy guide to install it.

For OpenRC, enable your configured service with `rc-update add imvault default`
and start it with `rc-service imvault start`; substitute `witmoot` for the board.
For systemd, use `systemctl enable --now imvault` or `witmoot`.
OpenRC logs go to `/var/log/imvault.log` and `/var/log/witmoot.log`. The ebuilds
depend on `app-admin/logrotate` and install each rule in `/etc/logrotate.d/`.
Keep logrotate's cron job or timer enabled. Both systemd units explicitly send
stdout and stderr to journald, which handles rotation and retention.

## Update

Back up application data before upgrades. Sync the overlay and update the
installed packages:

```sh
emaint sync -r comfyware
emerge --ask --update www-apps/imvault::comfyware www-apps/witmoot::comfyware
```

Review protected configuration changes with `dispatch-conf` or `etc-update`,
then restart the affected service.

Imvault 0.11.1 refines member invitations: grant access with **Allow invites** on
the Users page. Read the [release notes](https://github.com/airencracken/imvault/blob/v0.11.1/docs/release-notes/0.11.1.md)
for permission removal, disabled issuers, and provider signup attribution.

Imvault 0.10.1 fixes recovery and two-factor sign-in, atomic password changes,
administrator safeguards, and SMTP transport. The [audit report](AUDIT-2026-09-29.md)
covers those fixes. Witmoot 0.8.0 adds member suspension, confirmed message
removal, house rules, and a refined owner interface. Read its
[upgrade notes](https://github.com/airencracken/witmoot/blob/master/docs/release-notes/0.8.0.md):
back up the entire stopped data directory before its schema migration. Owner
usernames appear on the public House rules & owners page. Existing OpenRC
installations should keep both configuration files at mode 0600, since they can contain SMTP credentials.

Imvault moved from `app-admin/imvault` to `www-apps/imvault`. The overlay includes
a [package move](https://devmanual.gentoo.org/ebuild-maintenance/package-moves/)
so Portage can update installed-package records and package references. After
syncing, review any proposed updates to your `package.*` configuration files.
Replace remaining `app-admin/imvault` entries with `www-apps/imvault`, including
entries ending in `::comfyware` in `package.accept_keywords`; Portage may leave
those repository-qualified entries unchanged.
The service, configuration paths, and application data stay in the same places.

### Opt into live builds

To follow upstream `master`, additionally accept the exact live versions:

```text
=www-apps/imvault-9999::comfyware **
=www-apps/witmoot-9999::comfyware **
```

Then explicitly rebuild with `emerge --ask --oneshot =www-apps/imvault-9999::comfyware`
or `=www-apps/witmoot-9999::comfyware`. The version stays `9999` when upstream changes,
so a normal version-based world update may not rebuild it. Remove these keyword
entries to return to released versions. If you previously used an unversioned
`**` entry for these applications, replace it with the release entries above.

If migrating from a hand-made overlay, remove its duplicate recipes after
switching to `::comfyware`. Keep your existing configuration and data, and
check that your service uses `/usr/bin` if it previously used a `make install`
binary under `/usr/local/bin`.

## Maintain

Run `pkgcheck scan --exit error`, `bash scripts/test-make-deps.sh`,
`python3 scripts/test-publication.py`, `python3 scripts/test-manifests.py`,
and `python3 scripts/test-sandbox-packaging.py`
from this checkout. GitHub Actions also checks ebuild syntax, dependency-bundle failure
handling, staged service/logging installation against verified release sources,
and pkgcheck on pushes and pull requests. The install check can run locally with
`bash scripts/test-install.sh EBUILD SOURCE_DIRECTORY`; it uses an unprivileged
staging directory and leaves account ownership checks to Portage. Enable the `test`
USE flag for Witmoot's upstream Go tests; imvault also provides `src_test` for
Portage's `FEATURES=test`. Full emerge and service checks belong in a disposable
Gentoo installation, since account packages create real users and groups.

The initial recipes come from each project's `contrib/gentoo` directory.
This repository is the installable overlay; review service and dependency
changes upstream when updating its recipes.

For a new version, download and verify the upstream source release, then create
its dependency bundle, for example:

```sh
bash scripts/make-deps.sh imvault 0.11.1 imvault_0.11.1_source.tar.gz /tmp/comfyware-distfiles
```

The helper verifies modules and refuses to overwrite an existing bundle. Publish
the bundle under the matching `imvault-0.11.1` or `witmoot-0.9.0` tag in this
repository's GitHub Releases. Update the release ebuild and generate its Manifest
with `ebuild path/to/package-version.ebuild manifest`. Verify unpack, compilation,
and tests with Portage before publishing. Keep existing distfiles immutable.

Packaging is licensed under **AGPL-3.0-or-later**; see [LICENSE](LICENSE).
Each application's ebuild records its own and its linked dependencies' licenses.

To check the funding links GitHub recognizes and the public repository sidebars,
run `python3 scripts/test-github-funding.py --live` with an authenticated `gh`.
Both a funding file and an enabled Sponsorships setting are required.
