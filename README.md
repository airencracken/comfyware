# comfyware

Gentoo packages for Imvault, Witmoot and Songstead: apps you can host for friends, family,
and small communities.

| Package | Release | What it does |
| --- | --- | --- |
| `www-apps/imvault` | `0.16.2` | [Imvault](https://github.com/airencracken/imvault), a home for your group's photos and clips |
| `www-apps/songstead` | `0.5.0` | [Songstead](https://github.com/airencracken/songstead), a quiet music recommendation shelf |
| `www-apps/witmoot` | `0.14.2` | [Witmoot](https://github.com/airencracken/witmoot), a small bulletin board for friends and family |

Release ebuilds build the published source archives with checksummed Go dependency
bundles; compilation does not need network access. The released apps also have **live `9999`
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
www-apps/songstead::comfyware ~*
acct-user/imvault::comfyware ~*
acct-group/imvault::comfyware ~*
acct-user/witmoot::comfyware ~*
acct-group/witmoot::comfyware ~*
acct-user/songstead::comfyware ~*
acct-group/songstead::comfyware ~*
```

Keep the lines for the applications you install. `~*` accepts their testing
keywords while leaving unkeyworded live builds disabled. Review any additional
keyword or license changes Portage requests for dependencies.

For video thumbnails and duration checks, add this to
`/etc/portage/package.use/comfyware`:

```text
www-apps/imvault ffmpeg
```

For optional Bubblewrap confinement in Imvault and Witmoot, add `bubblewrap`
to their USE flags. This installs a non-setuid launcher; enable confinement separately
in the service settings. Imvault's stricter media sandbox also needs `ffmpeg`.
See the [Imvault setup](https://github.com/airencracken/imvault/blob/v0.16.2/docs/sandbox.md)
or [Witmoot setup](https://github.com/airencracken/witmoot/blob/v0.14.2/docs/sandbox.md)
for OpenRC settings, systemd overrides and verification.

Install the applications you want:

```sh
emerge --ask www-apps/imvault::comfyware www-apps/witmoot::comfyware www-apps/songstead::comfyware
```

The packages provide dedicated service accounts, `/usr/bin` binaries, OpenRC
and systemd service definitions, configuration files, and logrotate rules.
They do not enable or start services for you.

| Application | OpenRC configuration | systemd configuration | Data directory |
| --- | --- | --- | --- |
| Imvault | `/etc/conf.d/imvault` | `/etc/imvault/imvault.env` | `/var/lib/imvault` |
| Witmoot | `/etc/conf.d/witmoot` | `/etc/witmoot/witmoot.env` | `/var/lib/witmoot` |
| Songstead | `/etc/conf.d/songstead` | `/etc/songstead/songstead.env` | `/var/lib/songstead` |

Configure your hostname and reverse proxy, and provision the administrator or
owner before starting. Set `IMVAULT_ADDR="127.0.0.1:8080"` in Imvault's service
configuration; Witmoot's native service defaults to `127.0.0.1:8082`.
Songstead defaults to `127.0.0.1:8083`. Use the packaged `/usr/bin` binaries
in provisioning commands.

Caddy is the recommended reverse proxy, with automatic HTTPS. nginx and Apache
are supported by Imvault and Witmoot too. Each app installs proxy examples under
`/usr/share/doc/PACKAGE-VERSION/examples/`, alongside their deployment guides:

- [Imvault proxy setup](https://github.com/airencracken/imvault/blob/v0.16.2/docs/reverse-proxies.md)
- [Witmoot proxy setup](https://github.com/airencracken/witmoot/blob/v0.14.2/docs/reverse-proxies.md)

- [Imvault deployment and administrator setup](https://github.com/airencracken/imvault/blob/v0.16.2/docs/deployment.md)
- [Witmoot deployment and owner setup](https://github.com/airencracken/witmoot/blob/v0.14.2/docs/deployment.md)
- [Songstead deployment and account setup](https://github.com/airencracken/songstead/blob/v0.5.0/docs/deployment.md)

Run `imvault --help` or `witmoot --help` for commands, environment settings,
and service paths. Generate a site configuration for your hostname with:

```sh
imvault proxy-config caddy --domain img.example.com > imvault.Caddyfile
witmoot proxy-config caddy --domain board.example.org > witmoot.Caddyfile
```

Substitute `nginx` or `apache` for either helper. These commands print a config
and the matching application settings; follow the proxy guide to install it.

For OpenRC, enable your configured service with `rc-update add imvault default`
and start it with `rc-service imvault start`; substitute `witmoot` or `songstead`
for the other applications.
For systemd, use `systemctl enable --now APPLICATION`.
OpenRC logs go to `/var/log/imvault.log`, `/var/log/witmoot.log`, and
`/var/log/songstead.log`. The ebuilds
depend on `app-admin/logrotate` and install each rule in `/etc/logrotate.d/`.
Keep logrotate's cron job or timer enabled. All three systemd units explicitly send
stdout and stderr to journald, which handles rotation and retention.

### Optional Imvault backups

Imvault 0.13 can take verified snapshots while browsing and uploads continue.
Create `/var/backups/imvault` with mode 0700, owned by the service account. On
systemd, enable `imvault-backup.timer`. For OpenRC, copy the uncompressed
`examples/cron/imvault-backup` from the package documentation into `/etc/cron.d/`,
mode 0644. Enable one scheduler; installation enables neither. The root-run CLI
reads service settings and switches to the service account. Both examples keep
the newest seven completed snapshots; rotation follows successful verification.
Change `--keep` to choose another count; manual snapshots never rotate. Keep an
off-host copy and test restores. See the upstream
[operations guide](https://github.com/airencracken/imvault/blob/v0.16.2/docs/operations.md).

## Update

Back up application data before upgrades. Sync the overlay and update the
installed packages:

```sh
emaint sync -r comfyware
emerge --ask --update www-apps/imvault::comfyware www-apps/witmoot::comfyware www-apps/songstead::comfyware
```

Review protected configuration changes with `dispatch-conf` or `etc-update`,
then restart the affected service.

Read each application's release notes before upgrading:
[Imvault](https://github.com/airencracken/imvault/tree/master/docs/release-notes)
[Witmoot](https://github.com/airencracken/witmoot/tree/master/docs/release-notes),
and [Songstead](https://github.com/airencracken/songstead/blob/v0.5.0/CHANGELOG.md).
Witmoot schema upgrades cannot be undone, so back up the entire stopped data
directory first. Keep all OpenRC configuration files at mode 0600; they can
contain SMTP credentials. The [September 2026 audit](AUDIT-2026-09-29.md)
describes the fixes in Imvault 0.10.1 and Witmoot 0.7.3.

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
=www-apps/songstead-9999::comfyware **
```

Then explicitly rebuild with `emerge --ask --oneshot =www-apps/imvault-9999::comfyware`
or the corresponding Witmoot or Songstead live package. The version stays `9999` when upstream changes,
so a normal version-based world update may not rebuild it. Remove these keyword
entries to return to released versions. If you previously used an unversioned
`**` entry for these applications, replace it with the release entries above.

If migrating from a hand-made overlay, remove its duplicate recipes after
switching to `::comfyware`. Keep your existing configuration and data, and
check that your service uses `/usr/bin` if it previously used a `make install`
binary under `/usr/local/bin`.

## Maintain

Run `pkgcheck scan --exit error`, `bash scripts/test-make-deps.sh`,
`shellcheck scripts/*.sh`, and each `python3 scripts/test-*.py` from this
checkout. `scripts/test-recipes.py` keeps each live ebuild identical to its
newest release apart from the source, and rejects pre-stripped binaries,
compressed proxy examples, and install-check regressions. GitHub Actions also
checks ebuild syntax, verifies downloaded release sources against the Manifest
with `scripts/verify-distfile.py`, stages service and logging installation, and
runs pkgcheck on pushes and pull requests. The install check can run locally with
`bash scripts/test-install.sh EBUILD SOURCE_DIRECTORY`; it uses an unprivileged
staging directory and leaves account ownership checks to Portage. Enable the `test`
USE flag for Witmoot and Songstead's upstream Go tests; Imvault also provides `src_test` for
Portage's `FEATURES=test`. Full emerge and service checks belong in a disposable
Gentoo installation, since account packages create real users and groups.

The initial recipes come from each project's `contrib/gentoo` directory.
This repository is the installable overlay; review service and dependency
changes upstream when updating its recipes.

For a new version, download and verify the upstream source release, then create
its dependency bundle, for example:

```sh
bash scripts/make-deps.sh imvault 0.16.2 imvault_0.16.2_source.tar.gz /tmp/comfyware-distfiles
```

The helper verifies modules and refuses to overwrite an existing bundle.
It disables Go workspaces so a sibling development checkout cannot supply
unpublished dependencies in place of the release's modules.
Publish the bundle under the matching `imvault-0.16.2`, `witmoot-0.14.2`, or `songstead-0.5.0` tag in this
repository's GitHub Releases. Update the release ebuild and generate its Manifest
with `ebuild path/to/package-version.ebuild manifest`. Verify unpack, compilation,
and tests with Portage before publishing. Keep existing distfiles immutable.

Packaging is licensed under **AGPL-3.0-or-later**; see [LICENSE](LICENSE).
Each application's ebuild records its own and its linked dependencies' licenses.

To check the funding links GitHub recognizes and the public repository sidebars,
run `python3 scripts/test-github-funding.py --live` with an authenticated `gh`.
Both a funding file and an enabled Sponsorships setting are required.

## Songstead and discussion links

Songstead 0.5.0 is available as a versioned package and a live build. Its native
service binds `127.0.0.1:8083`; configure your hostname, secure cookies and a
reverse proxy in `/etc/conf.d/songstead` or `/etc/songstead/songstead.env`.
Provision an owner with `songstead create-owner --username NAME --password-prompt`.
Use `create-user` with the same flags for members, and `list-users` to inspect roles.
For scripts, use `--password-stdin` with protected standard input instead. Account
commands discover the installed service configuration and root invocations run
as the configured service user. Restart the updated server before provisioning
on an existing instance. Back up `/var/lib/songstead` before upgrades; startup applies
forward migrations. Follow the [installation guide](https://github.com/airencracken/songstead/blob/v0.5.0/docs/releases.md)
and [Gentoo deployment](https://github.com/airencracken/songstead/blob/v0.5.0/docs/deployment.md)
for accounts, service settings and Caddy.

Witmoot 0.14.2 accepts explicit discussion drafts from Songstead recommendations
and Imvault albums. Imvault 0.16.2 adds album discussion links and previews that
check current public visibility. Each app keeps its own accounts and data.
Opening a draft creates no thread; choose a board or existing topic, review its
audience, then post. Private albums retain plain links without metadata previews.
Configure the optional connections using the deployment guides before enabling
them. The three packages use the published Comfylib 0.1.3 module.

The installation checks stage files without creating accounts or starting
services. They verify executable paths, private data/configuration permissions,
proxy examples, logrotate and journald output. Portage performs the full build
and account ownership checks. Songstead and companion recipe tests continue
checking release/live parity, version stamps and exact Manifest entries.

Songstead also supports the optional `bubblewrap` USE flag. Enable its launcher
with `SONGSTEAD_SANDBOX="true"` in OpenRC, or install the systemd drop-in from
`examples/systemd/songstead-sandbox.conf`. Run `songstead sandbox --check` as the
service user before restarting. See [Songstead sandbox setup](https://github.com/airencracken/songstead/blob/v0.5.0/docs/sandbox.md).

Songstead includes browser administration, invitations and account recovery.
After upgrading and restarting, sign in as an owner and open Admin. For a
previously provisioned member, `songstead set-role --username NAME --role owner`
explicitly enables administration. Configure the public Songstead and Witmoot
addresses in Instance settings; changes apply immediately. Owners keep the same
private music access rules as members. Imvault 0.16.2 and Witmoot 0.14.2 share
Comfylib 0.1.3 password confirmation and image normalization, without schema
changes to either companion.

Songstead 0.5.0 includes freeform genre and tags, private discovery preferences,
compact List thumbnails, optional artwork tiles and supported-link previews before
sharing. View and discovery switches apply immediately; genre/tag pickers sit
beneath them, with additional dropdowns under More filters.
Your settings exposes spoiler settings, exclusions/favorites and profile pictures with
a viewer setting for GIF animation. Listening feedback shows a saved confirmation.
Labels follow each recommendation's audience; preferences and listening feedback
remain private. Public sharing cards show instance branding.

Startup applies schema 7 and retries existing missing artwork while retaining
cached images; back up before upgrading. Comfylib 0.1.4 supplies bounded profile
images and the shared artwork normalization. Companion versions remain unchanged.

Owners choose Songstead, Witmoot or Both under Admin's Discussion location.
Songstead and Both allow local participation without a Witmoot account. Witmoot
requires each person's separate account; no API key is needed for the browser
draft handoff. Existing comments remain readable, and configured connections
retain Both on upgrade. This release keeps schema 7 and Comfylib 0.1.4.
