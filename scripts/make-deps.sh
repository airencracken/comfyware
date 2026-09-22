#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-or-later
# Build a go-module.eclass dependency archive from an upstream source release.
fail() { printf '%s\n' "$*" >&2; exit 1; }
[[ $# == 4 ]] || fail 'Usage: make-deps.sh APP VERSION SOURCE.tar.gz OUTPUT_DIRECTORY'
app=$1
version=$2
case "$app" in imvault|witmoot) ;; *) fail 'Choose imvault or witmoot.' ;; esac
[[ $version =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || fail 'Version must have the form X.Y.Z.'
source_archive=$(realpath "$3") || exit 1
mkdir -p "$4" || exit 1
output_dir=$(realpath "$4") || exit 1
output="$output_dir/$app-$version-deps.tar.xz"
[[ ! -e $output ]] || fail "Refusing to overwrite $output"
work=$(mktemp -d) || exit 1
trap 'rm -rf "$work"' EXIT
trap 'exit 130' HUP INT TERM
mkdir "$work/source" || exit 1
tar -xzf "$source_archive" -C "$work/source" --strip-components=1 || exit 1
cd "$work/source" || exit 1
[[ -f go.mod && -f go.sum ]] || fail 'Source archive must contain go.mod and go.sum.'
cp go.mod "$work/original.mod" || exit 1
cp go.sum "$work/original.sum" || exit 1
GOTOOLCHAIN=local GOMODCACHE="$work/go-mod" go mod download -modcacherw || exit 1
GOTOOLCHAIN=local GOMODCACHE="$work/go-mod" go mod verify || exit 1
cmp go.mod "$work/original.mod" || fail 'Dependency resolution changed go.mod.'
cmp go.sum "$work/original.sum" || fail 'Dependency resolution changed go.sum.'
# Normalize archive ownership and timestamps.
tar --sort=name --mtime=@0 --owner=0 --group=0 --numeric-owner --format=gnu \
	-cf "$work/deps.tar" -C "$work" go-mod || exit 1
xz -T2 -9 -c "$work/deps.tar" > "$work/deps.tar.xz" || exit 1
mv "$work/deps.tar.xz" "$output" || exit 1
printf 'Created %s\n' "$output"
