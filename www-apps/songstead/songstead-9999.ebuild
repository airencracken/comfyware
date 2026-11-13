# Copyright 2026 Marcus J. Hildum
# SPDX-License-Identifier: AGPL-3.0-or-later
# Live ebuild for the master branch.

EAPI=8

inherit git-r3 go-module systemd

DESCRIPTION="Self-hosted music recommendation shelf for friends and family"
HOMEPAGE="https://github.com/airencracken/songstead"
EGIT_REPO_URI="https://github.com/airencracken/songstead.git"
EGIT_BRANCH="master"

# Songstead uses AGPL-3.0-or-later. The remaining entries cover the linked
# Go dependencies, their bundled code, and the embedded HTMX asset.
LICENSE="AGPL-3+ Apache-2.0 0BSD BSD BSD-2 MIT public-domain"
SLOT="0"
# go-module_live_vendor refuses to run without this.
PROPERTIES="live"
IUSE="bubblewrap test +zstd"
RESTRICT="!test? ( test )"
DOCS=( README.md THIRD_PARTY.md )

RDEPEND="
	zstd? ( app-arch/zstd )
	bubblewrap? ( >=sys-apps/bubblewrap-0.8[-suid(-)] )
	acct-group/songstead
	acct-user/songstead
	app-admin/logrotate
	app-misc/ca-certificates
"
BDEPEND+="
	>=dev-lang/go-1.26.11
	acct-group/songstead
	acct-user/songstead
	test? ( app-admin/logrotate )
"

src_unpack() {
	git-r3_src_unpack
	# Vendor the modules from go.mod so the build itself needs no network.
	go-module_live_vendor
}

src_configure() {
	go-module_src_configure
}

src_compile() {
	CGO_ENABLED=0 ego build -trimpath -ldflags "-X main.version=${PV}" -o songstead ./cmd/songstead
}

src_test() {
	ego test -count=1 ./...
}

src_install() {
	dobin songstead
	einstalldocs
	dodoc -r docs
	docinto examples
	dodoc -r contrib/caddy
	# The proxy examples are meant to be copied as they are.
	docinto examples/systemd
	sed 's|/usr/local/bin/songstead|/usr/bin/songstead|g' \
		contrib/systemd/songstead-sandbox.conf > "${T}/songstead-sandbox.conf" || die
	dodoc "${T}/songstead-sandbox.conf"
	docompress -x "/usr/share/doc/${PF}/examples"

	keepdir /var/lib/songstead
	fowners songstead:songstead /var/lib/songstead
	fperms 0700 /var/lib/songstead

	# Packages install into /usr, unlike the source-install default.
	sed 's|/usr/local/bin/songstead|/usr/bin/songstead|g' \
		contrib/openrc/songstead > "${T}/songstead.initd" || die
	newinitd "${T}/songstead.initd" songstead
	newconfd contrib/openrc/songstead.confd songstead
	fperms 0600 /etc/conf.d/songstead
	insinto /etc/logrotate.d
	newins contrib/logrotate/songstead songstead

	sed 's|/usr/local/bin/songstead|/usr/bin/songstead|g' \
		contrib/systemd/songstead.service > "${T}/songstead.service" || die
	systemd_dounit "${T}/songstead.service"
	insinto /etc/songstead
	newins contrib/systemd/songstead.env songstead.env
	fperms 0600 /etc/songstead/songstead.env
}

pkg_postinst() {
	if [[ -n ${REPLACING_VERSIONS} ]]; then
		elog "Updated to ${PV}. What changed: https://github.com/airencracken/songstead/commits/master"
		return
	fi

	elog "Browser setup: start the service, then run songstead setup for its private key."
	elog "Command-line owner: songstead create-owner --username NAME"
	elog "Password recovery: songstead set-password --username NAME"
	elog "Configure /etc/conf.d/songstead (OpenRC) or /etc/songstead/songstead.env (systemd)."
	elog "The service listens on 127.0.0.1:8083 and keeps data in /var/lib/songstead."
	elog "Put an HTTPS reverse proxy in front before inviting people."
	elog "Automatic backups are built in: the service makes one daily and keeps seven."
	elog "Check them in instance settings and copy them off-host; see docs/automatic-backups.md."
	elog "Guides: /usr/share/doc/${PF}/docs/ and"
	elog "https://github.com/airencracken/songstead/tree/master/docs"
	if use bubblewrap; then
		elog "Bubblewrap confinement is optional; see docs/sandbox.md and the packaged systemd drop-in."
	fi
}
