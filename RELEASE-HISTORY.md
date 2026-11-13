# Release history

Feature notes from past overlay releases, moved out of the README. Each
application's own release notes are the full record.

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

## Display timezones

All five current applications offer **Times and dates** in account settings.
UTC is the default. Choose a city timezone and save it for your account across
sessions and devices. Device detection fills the field without saving; manual
selection and local date rendering work without JavaScript. Admin reporting days
remain UTC. Comfylib 0.6.0 supplies the shared control and formatting; see the
[display timezone integration guide](https://github.com/airencracken/comfylib/blob/v0.6.0/docs/display-time.md).

## Tidings fetching and formatting

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
