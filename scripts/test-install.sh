#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-or-later
# Exercise src_install in an unprivileged staging directory. Portage owns the
# helper implementations and account ownership; this checks the recipe's output.
fail() { printf '%s\n' "$*" >&2; exit 1; }
[[ $# == 2 ]] || fail 'Usage: test-install.sh EBUILD SOURCE_DIRECTORY'
ebuild=$(realpath "$1") || exit 1
source_dir=$(realpath "$2") || exit 1
PN=$(basename "$(dirname "$ebuild")")
case "$PN" in imvault|witmoot) ;; *) fail 'Expected an imvault or witmoot ebuild.' ;; esac
PF=$(basename "$ebuild" .ebuild)
PV=${PF#"$PN"-}
P=$PF
work=$(mktemp -d) || exit 1
trap 'rm -rf "$work"' EXIT
trap 'exit 130' HUP INT TERM
ED="$work/image"
T="$work/temp"
WORKDIR="$work"
mkdir -p "$ED" "$T" "$work/source" || exit 1
cp -R "$source_dir/contrib" "$work/source/" || exit 1
cd "$work/source" || exit 1
printf '#!/bin/sh\nexit 0\n' > "$PN" || exit 1
chmod 0755 "$PN" || exit 1

die() { fail "src_install failed: $*"; }
inherit() { :; }
einstalldocs() { :; }
dodoc() { :; }
docinto() { :; }
fowners() { :; } # Actual ownership requires the service accounts and Portage.
elog() { :; }
insinto() { install_dir=$1; }
newins() { install -Dm0644 "$1" "$ED$install_dir/$2" || die; }
newinitd() { install -Dm0755 "$1" "$ED/etc/init.d/$2" || die; }
newconfd() { install -Dm0644 "$1" "$ED/etc/conf.d/$2" || die; }
dobin() { install -Dm0755 "$1" "$ED/usr/bin/$(basename "$1")" || die; }
keepdir() { mkdir -p "$ED$1" || die; }
fperms() { chmod "$1" "$ED$2" || die; }
systemd_dounit() { install -Dm0644 "$1" "$ED/usr/lib/systemd/system/$(basename "$1")" || die; }

source "$ebuild" || fail 'Could not load ebuild.'
[[ " $RDEPEND " == *app-admin/logrotate* ]] || fail "$PF does not depend on logrotate."
src_install || fail "$PF src_install failed."
cmp contrib/logrotate/"$PN" "$ED/etc/logrotate.d/$PN" || fail 'Packaged logrotate rule is missing or altered.'
[[ $(stat -c %a "$ED/etc/logrotate.d/$PN") == 644 ]] || fail 'Logrotate rule is not mode 0644.'
[[ -x $ED/etc/init.d/$PN && -s $ED/etc/conf.d/$PN ]] || fail 'OpenRC service or settings are missing.'
[[ -x $ED/usr/bin/$PN ]] || fail 'Executable is missing from /usr/bin.'
[[ -s $ED/etc/$PN/$PN.env ]] || fail 'systemd environment file is missing.'
unit="$ED/usr/lib/systemd/system/$PN.service"
grep -Eq "^ExecStart=(\"/usr/bin/$PN\"|/usr/bin/$PN)$" "$unit" || fail 'systemd executable is not under /usr/bin.'
for setting in StandardOutput=journal StandardError=journal "SyslogIdentifier=$PN"; do
	grep -qx "$setting" "$unit" || fail "Packaged systemd unit is missing $setting."
done
printf '%s: staged binary, OpenRC, logrotate, and journald checks passed.\n' "$PF"
