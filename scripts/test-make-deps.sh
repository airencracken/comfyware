#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-or-later
cd "$(dirname "$0")/.." || exit 1
helper="$PWD/scripts/make-deps.sh"
work=$(mktemp -d) || exit 1
trap 'rm -rf "$work"' EXIT
trap 'exit 130' HUP INT TERM
fail() { printf '%s\n' "$*" >&2; exit 1; }
expect_failure() {
	local message=$1
	shift
	if bash "$helper" "$@" > "$work/result" 2>&1; then
		fail 'Invalid dependency-bundle request succeeded.'
	fi
	grep -Fq "$message" "$work/result" || { cat "$work/result" >&2; exit 1; }
}
expect_failure 'Choose imvault or witmoot.' unknown 0.1.0 "$work/source.tar.gz" "$work/output"
expect_failure 'Version must have the form X.Y.Z.' imvault '../../escape' "$work/source.tar.gz" "$work/output"
[[ ! -e $work/output ]] || fail 'Invalid arguments created an output directory.'
mkdir -p "$work/source" "$work/output" "$work/bin" || exit 1
printf 'module example.org/test\n\ngo 1.26.0\n' > "$work/source/go.mod" || exit 1
: > "$work/source/go.sum" || exit 1
tar -czf "$work/source.tar.gz" -C "$work" source || exit 1
printf 'existing published bytes\n' > "$work/output/imvault-0.5.0-deps.tar.xz" || exit 1
expect_failure 'Refusing to overwrite' imvault 0.5.0 "$work/source.tar.gz" "$work/output"
grep -qx 'existing published bytes' "$work/output/imvault-0.5.0-deps.tar.xz" || fail 'An existing bundle changed.'
# A failed Go download must never produce an archive that looks publishable.
cat > "$work/bin/go" <<'EOF'
#!/bin/sh
echo 'simulated dependency download failure' >&2
exit 1
EOF
if [[ $? != 0 ]]; then exit 1; fi
chmod 0755 "$work/bin/go" || exit 1
PATH="$work/bin:$PATH" expect_failure 'simulated dependency download failure' witmoot 0.1.0 "$work/source.tar.gz" "$work/output"
[[ ! -e $work/output/witmoot-0.1.0-deps.tar.xz ]] || fail 'Failed download left an output bundle.'
printf '%s\n' 'Dependency bundle input, immutability, and download-failure tests passed.'
