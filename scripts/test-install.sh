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
# The sourced ebuild reads these Portage variables.
# shellcheck disable=SC2034
{
	PF=$(basename "$ebuild" .ebuild)
	PVR=${PF#"$PN"-}
	PV=${PVR%-r[0-9]*}
	P=$PN-$PV
}
work=$(mktemp -d) || exit 1
trap 'rm -rf "$work"' EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM
ED="$work/image"
T="$work/temp"
# shellcheck disable=SC2034
WORKDIR="$work"
mkdir -p "$ED" "$T" "$work/source" || exit 1
cp -R "$source_dir/contrib" "$work/source/" || exit 1
cd "$work/source" || exit 1
printf '#!/bin/sh\nexit 0\n' > "$PN" || exit 1
chmod 0755 "$PN" || exit 1

die() { fail "src_install failed${1:+: $*}"; }
inherit() { :; }
einstalldocs() { :; }
dodoc() { :; }
docinto() { :; }
docompress() {
	[[ $1 == -x ]] || die 'docompress without -x is unexpected here'
	shift
	printf '%s\n' "$@" >> "$work/docompress-skip" || die 'could not record docompress'
}
fowners() { :; } # Actual ownership requires the service accounts and Portage.
elog() { :; }
ego() { die "ego must not run during src_install: $*"; }
insinto() { install_dir=$1; }
newins() { install -Dm0644 "$1" "$ED$install_dir/$2" || die; }
newinitd() { install -Dm0755 "$1" "$ED/etc/init.d/$2" || die; }
newconfd() { install -Dm0644 "$1" "$ED/etc/conf.d/$2" || die; }
dobin() { install -Dm0755 "$1" "$ED/usr/bin/$(basename "$1")" || die; }
keepdir() { mkdir -p "$ED$1" || die; }
fperms() { chmod "$1" "$ED$2" || die; }
systemd_dounit() { install -Dm0644 "$1" "$ED/usr/lib/systemd/system/$(basename "$1")" || die; }

# shellcheck source=/dev/null
source "$ebuild" || fail 'Could not load ebuild.'
[[ " $RDEPEND " == *app-admin/logrotate* ]] || fail "$PF does not depend on logrotate."
[[ " $RDEPEND " == *app-misc/ca-certificates* ]] || fail "$PF needs system CA certificates for outbound HTTPS and TLS mail."
if [[ " ${IUSE:-} " == *" bubblewrap "* ]]; then
	[[ " $RDEPEND " == *'bubblewrap? ( sys-apps/bubblewrap[-suid(-)] )'* ]] || fail 'Optional Bubblewrap dependency must reject setuid builds.'
fi
src_install || fail "$PF src_install failed."
cmp contrib/logrotate/"$PN" "$ED/etc/logrotate.d/$PN" || fail 'Packaged logrotate rule is missing or altered.'
[[ $(stat -c %a "$ED/etc/logrotate.d/$PN") == 644 ]] || fail 'Logrotate rule is not mode 0644.'
[[ -x $ED/etc/init.d/$PN && -s $ED/etc/conf.d/$PN ]] || fail 'OpenRC service or settings are missing.'
[[ $(stat -c %a "$ED/etc/conf.d/$PN") == 600 ]] || fail "OpenRC configuration must be mode 0600 to protect credentials."
# The init script must start the packaged binary, whatever upstream's
# source-install default is.
initd="$ED/etc/init.d/$PN"
grep -q '/usr/local/bin' "$initd" && fail 'OpenRC service still refers to /usr/local/bin.'
grep -Eq "^: \"\\\$\{[A-Z]+_BIN:=/usr/bin/$PN\}\"$" "$initd" || fail 'OpenRC service does not default to /usr/bin.'
[[ -x $ED/usr/bin/$PN ]] || fail 'Executable is missing from /usr/bin.'
env_file="$ED/etc/$PN/$PN.env"
[[ -s $env_file ]] || fail 'systemd environment file is missing.'
case $(stat -c %a "$env_file") in
600|640) ;;
*) fail 'systemd environment file must not be world-readable; it can hold SMTP credentials.' ;;
esac
grep -qx "/usr/share/doc/$PF/examples" "$work/docompress-skip" 2>/dev/null || fail 'Proxy examples would be installed compressed.'
unit="$ED/usr/lib/systemd/system/$PN.service"
grep -Eq "^ExecStart=(\"/usr/bin/$PN\"|/usr/bin/$PN)$" "$unit" || fail 'systemd executable is not under /usr/bin.'
for setting in StandardOutput=journal StandardError=journal "SyslogIdentifier=$PN"; do
	grep -qx "$setting" "$unit" || fail "Packaged systemd unit is missing $setting."
done
printf '%s: staged binary, OpenRC, logrotate, and journald checks passed.\n' "$PF"
