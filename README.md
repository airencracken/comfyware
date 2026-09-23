# comfyware

A Gentoo overlay for familyware, cozyware, friendware: software for your tribe.

Built for dozens or hundreds of people who know why they're there, not millions
of strangers who don't.

| Package | Release | What it does |
| --- | --- | --- |
| `app-admin/imvault` | `0.5.0` | [imvault](https://github.com/airencracken/imvault), a home for your group's photos and clips |
| `www-apps/witmoot` | `0.2.0` | [Witmoot](https://github.com/airencracken/witmoot), a small bulletin board for friends and family |

Release ebuilds build the published source archives with checksummed Go dependency
bundles; compilation does not need network access. Both also have **live `9999`
ebuilds** that build upstream `master` and fetch dependencies during unpack.
Go 1.26 or newer is required and pulled in by Portage.

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
app-admin/imvault::comfyware ~*
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
app-admin/imvault ffmpeg
```

Install either application or both:

```sh
emerge --ask app-admin/imvault::comfyware www-apps/witmoot::comfyware
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

- [imvault deployment and administrator setup](https://github.com/airencracken/imvault/blob/master/docs/deployment.md)
- [Witmoot deployment and owner setup](https://github.com/airencracken/witmoot/blob/master/docs/deployment.md)

For OpenRC, enable your configured service with `rc-update add imvault default`
and start it with `rc-service imvault start`; substitute `witmoot` for the board.
For systemd, use `systemctl enable --now imvault` or `witmoot`.
Ensure logrotate runs regularly for OpenRC logs; systemd services use the journal.

## Update

Back up application data before upgrades. Sync the overlay and update the
installed packages:

```sh
emaint sync -r comfyware
emerge --ask --update app-admin/imvault::comfyware www-apps/witmoot::comfyware
```

Review protected configuration changes with `dispatch-conf` or `etc-update`,
then restart the affected service.

### Opt into live builds

To follow upstream `master`, additionally accept the exact live versions:

```text
=app-admin/imvault-9999::comfyware **
=www-apps/witmoot-9999::comfyware **
```

Then explicitly rebuild with `emerge --ask --oneshot =app-admin/imvault-9999::comfyware`
or `=www-apps/witmoot-9999::comfyware`. The version stays `9999` when upstream changes,
so a normal version-based world update may not rebuild it. Remove these keyword
entries to return to released versions. If you previously used an unversioned
`**` entry for these applications, replace it with the release entries above.

If migrating from a hand-made overlay, remove its duplicate recipes after
switching to `::comfyware`. Keep your existing configuration and data, and
check that your service uses `/usr/bin` if it previously used a `make install`
binary under `/usr/local/bin`.

## Maintain

Run `pkgcheck scan --exit error` and `bash scripts/test-make-deps.sh` from this
checkout. GitHub Actions also checks ebuild syntax, dependency-bundle failure
handling, and pkgcheck on pushes and pull requests. Enable the `test`
USE flag for Witmoot's upstream Go tests; imvault also provides `src_test` for
Portage's `FEATURES=test`. Full emerge and service checks belong in a disposable
Gentoo installation, since account packages create real users and groups.

The initial recipes come from each project's `contrib/gentoo` directory.
This repository is the installable overlay; review service and dependency
changes upstream when updating its recipes.

For a new version, download and verify the upstream source release, then create
its dependency bundle, for example:

```sh
bash scripts/make-deps.sh imvault 0.5.0 imvault_0.5.0_source.tar.gz /tmp/comfyware-distfiles
```

The helper verifies modules and refuses to overwrite an existing bundle. Publish
the bundle under the matching `imvault-0.5.0` or `witmoot-0.2.0` tag in this
repository's GitHub Releases. Update the release ebuild and generate its Manifest
with `ebuild path/to/package-version.ebuild manifest`. Verify unpack, compilation,
and tests with Portage before publishing. Keep existing distfiles immutable.

Packaging is licensed under **AGPL-3.0-or-later**; see [LICENSE](LICENSE).
Each application's ebuild records its own and its linked dependencies' licenses.
