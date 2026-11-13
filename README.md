# comfyware

Gentoo packages for the Comfyware apps, which you can host for friends, family
and small communities.

| Package | Release | What it does |
| --- | --- | --- |
| `www-apps/imvault` | `0.26.0` | [Imvault](https://github.com/airencracken/imvault): photos and short clips |
| `www-apps/witmoot` | `0.24.0` | [Witmoot](https://github.com/airencracken/witmoot): a bulletin board |
| `www-apps/songstead` | `0.17.0` | [Songstead](https://github.com/airencracken/songstead): music recommendations |
| `www-apps/folkweave` | `0.7.1` | [Folkweave](https://github.com/airencracken/folkweave): a private group timeline |
| `www-apps/tidings` | `0.9.0` | [Tidings](https://github.com/airencracken/tidings): an RSS and Atom reader |

Release ebuilds build the published source with a checksummed bundle of Go
dependencies, so the build needs no network. Each app also has a live `9999`
ebuild that builds upstream `master`. Portage pulls in Go 1.26.11 or newer.

Past release notes are in [RELEASE-HISTORY.md](RELEASE-HISTORY.md).

## Add the overlay

As root:

```sh
emerge --ask app-eselect/eselect-repository dev-vcs/git
eselect repository add comfyware git https://github.com/airencracken/comfyware.git
emaint sync -r comfyware
```

If you manage `repos.conf` yourself, put this in
`/etc/portage/repos.conf/comfyware.conf` and run `emaint sync -r comfyware`:

```ini
[comfyware]
location = /var/db/repos/comfyware
sync-type = git
sync-uri = https://github.com/airencracken/comfyware.git
auto-sync = yes
```

## Install

The packages use testing keywords on amd64 and arm64. Add the lines for the
apps you want to `/etc/portage/package.accept_keywords/comfyware`:

```text
www-apps/imvault::comfyware ~*
acct-user/imvault::comfyware ~*
acct-group/imvault::comfyware ~*
www-apps/witmoot::comfyware ~*
acct-user/witmoot::comfyware ~*
acct-group/witmoot::comfyware ~*
www-apps/songstead::comfyware ~*
acct-user/songstead::comfyware ~*
acct-group/songstead::comfyware ~*
www-apps/folkweave::comfyware ~*
acct-user/folkweave::comfyware ~*
acct-group/folkweave::comfyware ~*
www-apps/tidings::comfyware ~*
acct-user/tidings::comfyware ~*
acct-group/tidings::comfyware ~*
```

`~*` accepts the testing keywords and leaves the live builds off.

Optional USE flags, in `/etc/portage/package.use/comfyware`:

- `ffmpeg` on Imvault makes video thumbnails and enforces clip length.
- `bubblewrap` on Imvault, Witmoot or Songstead installs a non-setuid launcher
  for service confinement. Turn it on in the service settings; see the
  [Imvault](https://github.com/airencracken/imvault/blob/v0.26.0/docs/sandbox.md),
  [Witmoot](https://github.com/airencracken/witmoot/blob/v0.24.0/docs/sandbox.md) or
  [Songstead](https://github.com/airencracken/songstead/blob/v0.17.0/docs/sandbox.md)
  guide. Imvault's media sandbox also needs `ffmpeg`.
- `zstd` is on by default and compresses backups. Without it, the apps use
  built-in gzip.

Install:

```sh
emerge --ask www-apps/imvault::comfyware www-apps/witmoot::comfyware www-apps/songstead::comfyware www-apps/folkweave::comfyware www-apps/tidings::comfyware
```

Each package adds a service account, a `/usr/bin` binary, OpenRC and systemd
services, a configuration file and a logrotate rule. Nothing starts on its own.

| App | OpenRC config | systemd config | Data | Listens on |
| --- | --- | --- | --- | --- |
| Imvault | `/etc/conf.d/imvault` | `/etc/imvault/imvault.env` | `/var/lib/imvault` | set `IMVAULT_ADDR="127.0.0.1:8080"` |
| Witmoot | `/etc/conf.d/witmoot` | `/etc/witmoot/witmoot.env` | `/var/lib/witmoot` | `127.0.0.1:8082` |
| Songstead | `/etc/conf.d/songstead` | `/etc/songstead/songstead.env` | `/var/lib/songstead` | `127.0.0.1:8083` |
| Folkweave | `/etc/conf.d/folkweave` | `/etc/folkweave/folkweave.env` | `/var/lib/folkweave` | `127.0.0.1:8084` |
| Tidings | `/etc/conf.d/tidings` | `/etc/tidings/tidings.env` | `/var/lib/tidings` | `127.0.0.1:8085` |

Write settings as `KEY="value"`, without `export`; see the
[shared configuration format](https://github.com/airencracken/comfylib/blob/master/docs/configuration.md).
Keep OpenRC files at mode 0600, since they can hold mail passwords.

### Set up

1. Set your hostname and put an HTTPS reverse proxy in front. Caddy is the
   easiest. Examples for each app are in
   `/usr/share/doc/PACKAGE-VERSION/examples/`. Imvault, Witmoot and Tidings
   can print a config for your domain:

   ```sh
   imvault proxy-config caddy --domain img.example.com > imvault.Caddyfile
   ```

   Swap `caddy` for `nginx` or `apache` if you prefer.
2. Start the service:
   `rc-update add APP default && rc-service APP start` on OpenRC, or
   `systemctl enable --now APP` on systemd.
3. Create the first owner. Run `APP setup` for a private browser setup key, or
   `APP create-owner --username NAME` to set a password in the terminal.
   `APP set-password --username NAME` resets a password and signs out old
   sessions. Run these as root; they switch to the service account.
   `--password-stdin`, `--password-file PATH` and `--data-dir DIRECTORY` help
   with scripts.

Each app's deployment guide has the details:
[Imvault](https://github.com/airencracken/imvault/blob/v0.26.0/docs/deployment.md),
[Witmoot](https://github.com/airencracken/witmoot/blob/v0.24.0/docs/deployment.md),
[Songstead](https://github.com/airencracken/songstead/blob/v0.17.0/docs/deployment.md),
[Folkweave](https://github.com/airencracken/folkweave/blob/v0.7.1/docs/deployment.md),
[Tidings](https://github.com/airencracken/tidings/blob/v0.9.0/docs/deployment.md).

OpenRC logs go to `/var/log/APP.log` and logrotate rotates them; keep its cron
job or timer on. Under systemd, logs go to the journal.

### Backups

Every app backs itself up while it runs. The first backup starts a minute after
startup, then every 24h. Each app keeps seven copies, up to 10 GiB of archives,
with a 5 GiB cap on each uncompressed snapshot. Owners see the results in
the app's settings (instance settings in Imvault, Witmoot and Songstead). Snapshots land in `backups/` under the data directory; copy
them off-host.

To change the schedule, set `APP_BACKUP_INTERVAL` (0 turns it off),
`APP_BACKUP_KEEP`, `APP_BACKUP_MAX_BYTES` or `APP_BACKUP_COPY_MAX_BYTES`, with
`APP` as the app's name in capitals. Restore steps are in each guide:
[Imvault](https://github.com/airencracken/imvault/blob/v0.26.0/docs/automatic-backups.md),
[Witmoot](https://github.com/airencracken/witmoot/blob/v0.24.0/docs/automatic-backups.md),
[Songstead](https://github.com/airencracken/songstead/blob/v0.17.0/docs/automatic-backups.md),
[Folkweave](https://github.com/airencracken/folkweave/blob/v0.7.1/docs/automatic-backups.md),
[Tidings](https://github.com/airencracken/tidings/blob/v0.9.0/docs/automatic-backups.md).

Imvault can also write extra verified snapshots to another directory. Create
`/var/backups/imvault` (mode 0700, owned by `imvault`), then enable
`imvault-backup.timer` on systemd, or copy `examples/cron/imvault-backup` into
`/etc/cron.d/` (mode 0644) on OpenRC. Neither is on by default. Both keep seven
snapshots; change `--keep` for another count. See the
[operations guide](https://github.com/airencracken/imvault/blob/v0.26.0/docs/operations.md).

### Connect the apps

The apps can link to each other and share a community sign-in. Both are off
until you configure them, and accounts stay separate. See the suite guides for
[Imvault](https://github.com/airencracken/imvault/blob/v0.26.0/docs/suite.md),
[Witmoot](https://github.com/airencracken/witmoot/blob/v0.24.0/docs/suite.md),
[Songstead](https://github.com/airencracken/songstead/blob/v0.17.0/docs/suite.md),
[Folkweave](https://github.com/airencracken/folkweave/blob/v0.7.1/docs/suite.md) and
[Tidings](https://github.com/airencracken/tidings/blob/v0.9.0/docs/suite.md).

## Update

Back up first. Upgrades can migrate the database, and going back needs the
backup made before the upgrade. Then:

```sh
emaint sync -r comfyware
emerge --ask --update www-apps/imvault::comfyware www-apps/witmoot::comfyware www-apps/songstead::comfyware www-apps/folkweave::comfyware www-apps/tidings::comfyware
```

Merge configuration changes with `dispatch-conf` or `etc-update`, then restart
the service. Each app's release notes are on its GitHub releases page:
[Imvault](https://github.com/airencracken/imvault/releases),
[Witmoot](https://github.com/airencracken/witmoot/releases),
[Songstead](https://github.com/airencracken/songstead/releases),
[Folkweave](https://github.com/airencracken/folkweave/releases),
[Tidings](https://github.com/airencracken/tidings/releases).

Imvault moved from `app-admin/imvault` to `www-apps/imvault`. Portage applies
the [package move](https://devmanual.gentoo.org/ebuild-maintenance/package-moves/)
on sync. Replace any leftover `app-admin/imvault` entries in your `package.*`
files, including ones ending in `::comfyware`. Paths and data stay the same.

Coming from a hand-made overlay? Remove its duplicate recipes, keep your
configuration and data, and point your service at `/usr/bin` instead of
`/usr/local/bin`.

### Live builds

To follow upstream `master`, also accept the live versions:

```text
=www-apps/imvault-9999::comfyware **
=www-apps/witmoot-9999::comfyware **
=www-apps/songstead-9999::comfyware **
=www-apps/folkweave-9999::comfyware **
=www-apps/tidings-9999::comfyware **
```

The version stays `9999`, so a world update won't rebuild it. Rebuild with
`emerge --ask --oneshot =www-apps/APP-9999::comfyware`. Remove these lines to go
back to releases.

## Maintain

Run the checks from this checkout:

```sh
pkgcheck scan --exit error
shellcheck scripts/*.sh
bash scripts/test-make-deps.sh
for test in scripts/test-*.py; do python3 "$test" || echo "FAILED: $test"; done
```

`bash scripts/test-install.sh EBUILD SOURCE_DIRECTORY` stages one install
without root. Enable the `test` USE flag, or `FEATURES=test` for Imvault, to run
upstream Go tests. Test full installs in a throwaway Gentoo system, because the
account packages create real users.

For a new version, verify the upstream source release, then build its
dependency bundle:

```sh
bash scripts/make-deps.sh imvault 0.26.0 imvault_0.26.0_source.tar.gz /tmp/comfyware-distfiles
```

Publish the bundle under the matching tag (`imvault-0.26.0`) in this
repository's GitHub Releases. Update the ebuild, run
`ebuild path/to/package-version.ebuild manifest`, and build it with Portage.
Never replace a published distfile.

`python3 scripts/test-github-funding.py --live` checks the funding links GitHub
shows; it needs an authenticated `gh`.

Packaging is licensed under **AGPL-3.0-or-later**; see [LICENSE](LICENSE). Each
ebuild lists the licenses of its app and linked dependencies.

## Coordinated releases

`release-catalog.json` records the suite's versions. Update it, the recipes and
the website catalog before tagging. Each app's `make release-preflight` checks
one app. The shared `release-plan` command with
`--catalog ../comfyware/release-catalog.json --suite-root ..` checks all five
apps, these recipes and the website together, and `--verify-plan` refuses
source changes made after planning.

## Also made here

[Arise](https://github.com/airencracken/arise) is experimental Gentoo package
tooling in Go: search, dependency resolution, sync, builds and recovery in one
binary, using your Portage configuration. Install it from the
[Arise overlay](https://github.com/airencracken/arise-overlay), and keep
Portage installed while it matures.
