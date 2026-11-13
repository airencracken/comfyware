# comfyware

Gentoo packages for Imvault, Witmoot, Songstead, Folkweave and Tidings: apps you can host for friends, family,
and small communities.

| Package | Release | What it does |
| --- | --- | --- |
| `www-apps/imvault` | `0.25.0` | [Imvault](https://github.com/airencracken/imvault), a home for your group's photos and clips |
| `www-apps/songstead` | `0.16.0` | [Songstead](https://github.com/airencracken/songstead), a quiet music recommendation shelf |
| `www-apps/folkweave` | `0.6.0` | [Folkweave](https://github.com/airencracken/folkweave), a private group timeline |
| `www-apps/tidings` | `0.8.0` | [Tidings](https://github.com/airencracken/tidings), an RSS and Atom reader |
| `www-apps/witmoot` | `0.23.0` | [Witmoot](https://github.com/airencracken/witmoot), a small bulletin board for friends and family |

Release ebuilds build the published source archives with checksummed Go dependency
bundles; compilation does not need network access. The released apps also have **live `9999`
ebuilds** that build upstream `master` and fetch dependencies during unpack.
Go 1.26.11 or a newer patched release is required and pulled in by Portage.

Also made here: [Arise](https://github.com/airencracken/arise), experimental
Gentoo package tooling in Go. It brings package search, dependency resolution,
repository sync, builds, and recovery tools together in one binary, using your
existing Portage configuration. Find installation instructions in the
[Arise overlay](https://github.com/airencracken/arise-overlay). The commands below
use Portage; Arise can work with configured overlays too. Keep Portage installed
while Arise's compatibility work continues.

## Coordinated releases

`release-catalog.json` records the planned suite versions. Update it with the
application source metadata, current recipes and website catalog before creating
tags. Each app's `make release-preflight` verifies a clean commit, published module
resolution and matching immutable workflow references. The shared `release-plan`
command also accepts `--catalog ../comfyware/release-catalog.json --suite-root ..`
to check all five applications, overlay recipes and website versions together.
The generated plan records source commits and input hashes; `--verify-plan` rejects
source changes before publication. Release workflows require native, package,
container and browser gates before publishing artifacts.

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
www-apps/folkweave::comfyware ~*
acct-user/folkweave::comfyware ~*
acct-group/folkweave::comfyware ~*
www-apps/tidings::comfyware ~*
acct-user/tidings::comfyware ~*
acct-group/tidings::comfyware ~*
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
See the [Imvault setup](https://github.com/airencracken/imvault/blob/v0.25.0/docs/sandbox.md)
or [Witmoot setup](https://github.com/airencracken/witmoot/blob/v0.23.0/docs/sandbox.md)
for OpenRC settings, systemd overrides and verification.

Install the applications you want:

```sh
emerge --ask www-apps/imvault::comfyware www-apps/witmoot::comfyware www-apps/songstead::comfyware www-apps/folkweave::comfyware www-apps/tidings::comfyware
```

The packages provide dedicated service accounts, `/usr/bin` binaries, OpenRC
and systemd service definitions, configuration files, and logrotate rules.
They do not enable or start services for you.

| Application | OpenRC configuration | systemd configuration | Data directory |
| --- | --- | --- | --- |
| Imvault | `/etc/conf.d/imvault` | `/etc/imvault/imvault.env` | `/var/lib/imvault` |
| Witmoot | `/etc/conf.d/witmoot` | `/etc/witmoot/witmoot.env` | `/var/lib/witmoot` |
| Songstead | `/etc/conf.d/songstead` | `/etc/songstead/songstead.env` | `/var/lib/songstead` |
| Folkweave | `/etc/conf.d/folkweave` | `/etc/folkweave/folkweave.env` | `/var/lib/folkweave` |
| Tidings | `/etc/conf.d/tidings` | `/etc/tidings/tidings.env` | `/var/lib/tidings` |

Configure your hostname and reverse proxy, and provision the administrator or
owner before starting. Set `IMVAULT_ADDR="127.0.0.1:8080"` in Imvault's service
configuration; Witmoot's native service defaults to `127.0.0.1:8082`.
Songstead defaults to `127.0.0.1:8083`, Folkweave to `127.0.0.1:8084`, and Tidings to `127.0.0.1:8085`. Use the packaged `/usr/bin` binaries
in provisioning commands.

Caddy is the recommended reverse proxy, with automatic HTTPS. nginx and Apache
are supported by Imvault and Witmoot too. Each app installs proxy examples under
`/usr/share/doc/PACKAGE-VERSION/examples/`, alongside their deployment guides:

- [Imvault proxy setup](https://github.com/airencracken/imvault/blob/v0.25.0/docs/reverse-proxies.md)
- [Witmoot proxy setup](https://github.com/airencracken/witmoot/blob/v0.23.0/docs/reverse-proxies.md)

- [Imvault deployment and administrator setup](https://github.com/airencracken/imvault/blob/v0.25.0/docs/deployment.md)
- [Witmoot deployment and owner setup](https://github.com/airencracken/witmoot/blob/v0.23.0/docs/deployment.md)
- [Songstead deployment and account setup](https://github.com/airencracken/songstead/blob/v0.16.0/docs/deployment.md)

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
[operations guide](https://github.com/airencracken/imvault/blob/v0.25.0/docs/operations.md).

## Shared Comfylib foundation

Imvault 0.20.6, Witmoot 0.18.4 and Songstead 0.11.3 pin the published
[Comfylib v0.1.7](https://github.com/airencracken/comfylib/releases/tag/v0.1.7)
module for shared invitation/account styles, invitation status calculation and
browser assertions. Its exact source is included in each verified dependency
bundle and linked into the app binary; it needs no separate runtime package.
Witmoot and Songstead also wrap long backup paths on mobile settings pages.

## Invitation and account screens

Imvault 0.20.6, Witmoot 0.18.4 and Songstead 0.11.3 align invitation management,
sign-in and joining forms across the apps. Compact creation forms sit beside
readable invitation records on desktop and stack on mobile. Decorative eyebrow
labels are removed. Songstead also shows invitation availability and keeps form
drafts after validation errors.

These patches add no database migrations. They retain Imvault schema 034,
Witmoot schema 020 and Songstead schema 10. Existing service configuration and
package paths continue to apply.

## Witmoot reply refresh

Witmoot 0.18.4 refreshes the conversation after replying from a message
permalink and drops repeated submissions while a reply is pending. It adds no
database migrations; the current schema remains 020. Sync this overlay, upgrade
the package, then restart Witmoot to apply the fix.

## Create albums while organizing photos

Imvault 0.20.6 adds “Create a new album” to the gallery’s bulk album picker,
including before the first album exists. The new album and all selected
memberships are saved atomically. Albums start private, and existing photo
sharing stays unchanged. No database migration is added; schema 034 remains
current. Upgrade the package and restart Imvault to use the new picker.

## Update

Back up application data before upgrades. Sync the overlay and update the
installed packages:

```sh
emaint sync -r comfyware
emerge --ask --update www-apps/imvault::comfyware www-apps/witmoot::comfyware www-apps/songstead::comfyware www-apps/folkweave::comfyware www-apps/tidings::comfyware
```

Review protected configuration changes with `dispatch-conf` or `etc-update`,
then restart the affected service.

Read each application's release notes before upgrading:
[Imvault](https://github.com/airencracken/imvault/tree/master/docs/release-notes)
[Witmoot](https://github.com/airencracken/witmoot/tree/master/docs/release-notes),
and [Songstead](https://github.com/airencracken/songstead/blob/v0.16.0/CHANGELOG.md).
Imvault 0.20.0 adds migrations 033 and 034 for private 30-day Trash and camera-date
browsing. Back up with the currently installed binary before upgrading; returning
to an older binary requires its matching pre-upgrade database. Owner API deletion
now moves files to Trash, which retains quota until permanent deletion. See the
[Imvault release notes](https://github.com/airencracken/imvault/blob/v0.25.0/docs/release-notes/0.20.0.md)
and [library guide](https://github.com/airencracken/imvault/blob/v0.25.0/docs/library.md).

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
=www-apps/folkweave-9999::comfyware **
=www-apps/tidings-9999::comfyware **
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
bash scripts/make-deps.sh imvault 0.21.1 imvault_0.21.1_source.tar.gz /tmp/comfyware-distfiles
```

The helper verifies modules and refuses to overwrite an existing bundle.
It disables Go workspaces so a sibling development checkout cannot supply
unpublished dependencies in place of the release's modules.
Publish the bundle under the matching `imvault-0.21.1`, `witmoot-0.19.1`, or `songstead-0.12.1` tag in this
repository's GitHub Releases. Update the release ebuild and generate its Manifest
with `ebuild path/to/package-version.ebuild manifest`. Verify unpack, compilation,
and tests with Portage before publishing. Keep existing distfiles immutable.

Packaging is licensed under **AGPL-3.0-or-later**; see [LICENSE](LICENSE).
Each application's ebuild records its own and its linked dependencies' licenses.

To check the funding links GitHub recognizes and the public repository sidebars,
run `python3 scripts/test-github-funding.py --live` with an authenticated `gh`.
Both a funding file and an enabled Sponsorships setting are required.

## Witmoot recent posts

Witmoot 0.18.0 shows individual posts and replies in Recent, newest first, with
message text, shared images, author and conversation context. Each page has twenty
posts and links to the exact message in its conversation. Existing board, group
and conversation permissions apply before pagination; removed messages and archived
boards stay out. Edits retain their original position.

Migration 020 adds an index without rewriting messages. Keep a verified pre-upgrade
backup; older binaries require the matching pre-upgrade database. Read the
[Witmoot 0.18.0 release notes](https://github.com/airencracken/witmoot/blob/v0.23.0/docs/release-notes/0.18.0.md)
before upgrading.

## Songstead and discussion links

Songstead 0.11.3 is available as a versioned package and a live build. Authors can
edit their post's music details and note, or delete it after confirmation. Edits
preserve the audience and leave other recommendations unchanged. YouTube album
playlists support automatic titles and artwork. Schema 10 stores corrections per
post and retries missing previews, including older playlist links. Like songs
privately and find them with Liked songs. Matching URLs share one song card by
default in Recent, keeping each recommendation's sender, date, note and conversation.
Cross-provider music stays separate. Schema 9 preserves existing listening
feedback and carries the latest private rating into each initial song like.
Account export format 6 includes your private song likes. Back up the stopped
data directory before upgrading; downgrades require that database backup. Posting a
recommendation marks the music as listened for its sender across all audiences.
Other members keep their own listening status; ratings and personal notes stay
unchanged. Its native service binds `127.0.0.1:8083`; configure your hostname, secure cookies and a
reverse proxy in `/etc/conf.d/songstead` or `/etc/songstead/songstead.env`.
Provision an owner with `songstead create-owner --username NAME --password-prompt`.
Use `create-user` with the same flags for members, and `list-users` to inspect roles.
For scripts, use `--password-stdin` with protected standard input instead. Account
commands discover the installed service configuration and root invocations run
as the configured service user. Restart the updated server before provisioning
on an existing instance. Back up `/var/lib/songstead` before upgrades; startup applies
forward migrations. Follow the [installation guide](https://github.com/airencracken/songstead/blob/v0.16.0/docs/releases.md)
and [Gentoo deployment](https://github.com/airencracken/songstead/blob/v0.16.0/docs/deployment.md)
for accounts, service settings and Caddy.

Witmoot 0.18.0 accepts explicit discussion drafts from Songstead recommendations
and Imvault albums. Imvault 0.20.0 includes album discussion links and previews that
check current public visibility. Each app keeps its own accounts and data.
Opening a draft creates no thread; choose a board or existing topic, review its
audience, then post. Private albums retain plain links without metadata previews.
Configure the optional connections using the deployment guides before enabling
them. Songstead 0.11.0 and Witmoot 0.18.0 pin published Comfylib 0.1.6;
Imvault 0.20.0 pins Comfylib 0.1.6.

The installation checks stage files without creating accounts or starting
services. They verify executable paths, private data/configuration permissions,
proxy examples, logrotate and journald output. Portage performs the full build
and account ownership checks. Songstead and companion recipe tests continue
checking release/live parity, version stamps and exact Manifest entries.

Songstead also supports the optional `bubblewrap` USE flag. Enable its launcher
with `SONGSTEAD_SANDBOX="true"` in OpenRC, or install the systemd drop-in from
`examples/systemd/songstead-sandbox.conf`. Run `songstead sandbox --check` as the
service user before restarting. See [Songstead sandbox setup](https://github.com/airencracken/songstead/blob/v0.16.0/docs/sandbox.md).

Songstead includes browser administration, invitations and account recovery.
After upgrading and restarting, sign in as an owner and open Admin. For a
previously provisioned member, `songstead set-role --username NAME --role owner`
explicitly enables administration. Configure the public Songstead and Witmoot
addresses in Instance settings; changes apply immediately. Owners keep the same
private music access rules as members. Imvault 0.20.0 and Witmoot 0.18.0 use
Comfylib's shared password confirmation and branding image normalization. Each
application retains its own account and invitation policies.

Songstead 0.11.0 includes freeform genre and tags, private discovery preferences,
compact List thumbnails, optional artwork tiles and supported-link previews before
sharing. View and discovery switches apply immediately; genre/tag pickers sit
beneath them, with additional dropdowns under More filters.
Your settings exposes spoiler settings, exclusions/favorites and profile pictures with
a viewer setting for GIF animation. Listening feedback shows a saved confirmation.
Labels follow each recommendation's audience; preferences and listening feedback
remain private. Public sharing cards show instance branding.

Startup applies schema 9 and retries existing missing artwork while retaining
cached images; back up before upgrading. Comfylib 0.1.6 supplies bounded profile
images and the shared artwork normalization. Witmoot uses the same profile image
handling for the avatar upgrade below.

Owners choose Songstead, Witmoot or Both under Admin's Discussion location.
Songstead and Both allow local participation without a Witmoot account. Witmoot
requires each person's separate account; no API key is needed for the browser
draft handoff. Existing comments remain readable, and configured connections
retain Both on upgrade. The current release uses schema 10 and Comfylib 0.1.8.

Witmoot 0.18.0 retains animated GIF avatars through Comfylib 0.1.6. Members
can upload or remove an avatar under Your account and save whether they see
animation. Device reduced-motion preferences and visitors receive still images.
Stop the service and back up its data directory before the schema 19 upgrade.

Songstead 0.11.0 includes Recent → Comments: a chronological feed of conversations
on music shared with everyone on the instance. Private sends and personal
listening feedback stay out, and timestamped comments follow each viewer's
annotation preferences and indicated positions before pagination. The current release
uses schema 10 and Comfylib 0.1.6.

All three applications now have members-only profiles with optional names,
plain-text bios and up to five labeled web links. Profiles are linked from
conversation, recommendation, file or album authors. Songstead uses Your settings;
Witmoot uses Your account → Edit your profile; Imvault uses Settings → Account →
Profile. Private content, account email and credentials stay off profile pages.
Personal exports include only the exporting member’s profile. New profile storage
uses Songstead schema 9, Witmoot schema 19 and Imvault migration 032. Back up each
stopped application’s complete data directory before upgrading.

Songstead 0.11.0 adds signed-in search for music titles, artists, genres, tags,
shared messages and visible comments. Private sends and groups retain their
audience rules, and spoiler-hidden comments cannot affect result pages.
Personal listening notes and ratings are never searched. Schema 8 is unchanged.

Imvault 0.20.0 includes optional avatars under Settings → Account → Profile, using
Comfylib 0.1.6's shared image normalizer. GIFs retain still renditions; animation
is a private viewer preference and respects device reduced motion. Avatars are
visible only to signed-in members and included in the owner's export. Stop and
back up Imvault before migration 032, then upgrade and restart.

## Automatic compressed backups

Songstead 0.11.0, Witmoot 0.18.0 and Imvault 0.20.0 create verified backups
automatically while running. The first attempt starts one minute after service
startup, then every 24h, remembering successful backups across restarts.
Comfylib 0.1.6 shares scheduling, compression, private publication and rotation.

Backups use zstd when available and built-in gzip otherwise. The default-enabled
`zstd` USE flag installs app-arch/zstd; disabling the flag permits the gzip
fallback when zstd is absent. No timer or cron job is required.

Each app keeps up to seven copies within a 10 GiB cap on compressed archive data.
The uncompressed snapshot copy cap is 5 GiB. Settings are configurable through
APP_BACKUP_INTERVAL, APP_BACKUP_KEEP, APP_BACKUP_MAX_BYTES and
APP_BACKUP_COPY_MAX_BYTES, replacing APP with the uppercase application name.
An interval of 0 disables the built-in schedule. Manual backups and Imvault's
external cron/timer destinations are independent of these caps.

Owners see success, failures and caps on the existing instance settings page.
Snapshots live under the app's private data directory in backups/; copy
completed snapshots off-host. Allow additional staging space during a backup.
Recovery and service configuration details:

- [Songstead automatic backups](https://github.com/airencracken/songstead/blob/v0.16.0/docs/automatic-backups.md)
- [Witmoot automatic backups](https://github.com/airencracken/witmoot/blob/v0.23.0/docs/automatic-backups.md)
- [Imvault automatic backups](https://github.com/airencracken/imvault/blob/v0.25.0/docs/automatic-backups.md)

## Folkweave and Tidings

Folkweave 0.1.1 and Tidings 0.2.0 are released applications, each with a
live 9999 recipe and a dedicated service account. Install `www-apps/folkweave`
or `www-apps/tidings` after adding their `~*` keyword and those of their matching
`acct-user` and `acct-group` packages, as for the other apps above.

Folkweave uses `/var/lib/folkweave` and localhost port **8084**. Configure
`/etc/conf.d/folkweave` (OpenRC) or `/etc/folkweave/folkweave.env` (systemd), then
run `folkweave init --username owner --name "Your name" --title "Our group"`.
It has one invited group-wide audience. Parental approval controls remain future
work; shared photographs are normalized copies, so keep originals separately.

Tidings uses `/var/lib/tidings` and localhost port **8085**, avoiding Songstead's
8083. Configure `/etc/conf.d/tidings` or `/etc/tidings/tidings.env`, then run
`tidings create-owner --username owner`. Individual subscriptions and reading
state stay personal. The shared household reading table is opt-in.

Run installed administrative commands as root to re-execute as the configured
service account. Configure HTTPS before inviting members, then enable/start
the matching OpenRC or systemd service. Both apps make verified automatic
backups, and support manual backup and restoration into a fresh directory.
Their source downloads, containers, documentation and Ko-fi support links live
at [Folkweave](https://github.com/airencracken/folkweave) and
[Tidings](https://github.com/airencracken/tidings).

The OpenRC scripts pass supported ordinary `APP_*=value` assignments from
`/etc/conf.d/folkweave` and `/etc/conf.d/tidings` to the service; `export` is optional.
Tidings owners manage suggested-source categories, invitations, and immediate
instance-wide feed fetching from their account. Suggested categories begin
disabled, including on upgrade, and never change existing subscriptions.

## Common first-run setup

The current releases share browser and command-line account setup. Start the
configured service and run `APP setup` to retrieve its private browser setup key,
or run `APP create-owner --username NAME` for a hidden, confirmed terminal prompt.
Use `APP set-password --username NAME` for recovery; it revokes earlier sessions.
Root invocations use the configured service account. `--password-stdin`,
`--password-file PATH`, and `--data-dir DIRECTORY` work across all five apps.

Tidings 0.3.1 also shows live fetch progress, fetches newly followed feeds
immediately, and offers optional locally cached feed images in the owner's account
settings. Its database migrates to schema 4 with images disabled initially.

Tidings 0.5.0 preserves article formatting, can fetch full stories, removes known
tracking fields from article links, and adapts each feed's polling schedule.
Keyboard shortcuts are a personal setting and default to off, including upgrades.
The saved theme now applies before page content appears. Schema 5 adds private
article copies and schedules; the first refresh requests full feed bodies to
populate formatting while keeping everyone's reading state.

Tidings 0.4.1 fixes publisher TLS and content-negotiation compatibility for full
stories, including OpenAI pages, and reports specific fetch failures. TLS
certificate checks and the public-network restriction remain enabled. No database
migration is needed for this patch.

## Service configuration format

All five apps ship service config values as `KEY="value"`, including numeric,
boolean, and empty values. OpenRC uses `/etc/conf.d/APP`; systemd uses
`/etc/APP/APP.env`. Every template identifies its manager and installed path.
Use ordinary assignments without `export` and restart the matching service.
Existing bare or single-quoted settings remain supported; Portage preserves
local configuration through its normal config protection.

See the [shared configuration convention](https://github.com/airencracken/comfylib/blob/master/docs/configuration.md).

## Optional suite integrations

The current releases support explicitly configured app links and community sign-in.
Native service configuration and Compose forward the optional settings; empty
values leave the integrations disabled. Existing local accounts, passwords and
application permissions remain independent. A member must deliberately connect
an existing account to the identity provider. See each app's suite guide:

- [Imvault](https://github.com/airencracken/imvault/blob/v0.25.0/docs/suite.md)
- [Witmoot](https://github.com/airencracken/witmoot/blob/v0.23.0/docs/suite.md)
- [Songstead](https://github.com/airencracken/songstead/blob/v0.16.0/docs/suite.md)
- [Folkweave](https://github.com/airencracken/folkweave/blob/v0.6.0/docs/suite.md)
- [Tidings](https://github.com/airencracken/tidings/blob/v0.8.0/docs/suite.md)

Back up the stopped data directory before upgrading. Songstead builds its schema 11
search index at startup; allow time for large libraries. Keep the pre-upgrade
backup for a downgrade. Shared sign-in adds an identity-binding table when enabled.

The shared-maintenance releases use published Comfylib 0.3.0 and its separately
versioned OIDC adapter 0.1.0. Application source imports the suite package and
serves the embedded shared assets directly. Maintenance commands resolve the
exact module pin, including from the offline dependency bundle.

## Display timezones

All five current applications offer **Times and dates** in account settings.
UTC is the default. Choose a city timezone and save it for your account across
sessions and devices. Device detection fills the field without saving; manual
selection and local date rendering work without JavaScript. Admin reporting days
remain UTC. Comfylib 0.6.0 supplies the shared control and formatting; see the
[display timezone integration guide](https://github.com/airencracken/comfylib/blob/v0.6.0/docs/display-time.md).
