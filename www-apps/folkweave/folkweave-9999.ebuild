# Copyright 2026 Marcus J. Hildum
# SPDX-License-Identifier: AGPL-3.0-or-later
# Live ebuild for the master branch.

EAPI=8

inherit git-r3 go-module systemd

DESCRIPTION="Private posts and photos for a small group"
HOMEPAGE="https://github.com/airencracken/folkweave"
EGIT_REPO_URI="https://github.com/airencracken/folkweave.git"
EGIT_BRANCH="master"

LICENSE="AGPL-3+ Apache-2.0 0BSD BSD BSD-2 MIT public-domain"
SLOT="0"
# go-module_live_vendor refuses to run without this.
PROPERTIES="live"
IUSE="test +zstd"
RESTRICT="!test? ( test )"
DOCS=( README.md THIRD_PARTY.md )

RDEPEND="
	acct-group/folkweave
	acct-user/folkweave
	app-admin/logrotate
	app-misc/ca-certificates
	zstd? ( app-arch/zstd )
"
BDEPEND+="
	>=dev-lang/go-1.26.11
	acct-group/folkweave
	acct-user/folkweave
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
	CGO_ENABLED=0 ego build -trimpath -ldflags "-X main.version=${PV}" -o folkweave ./cmd/folkweave
}

src_test() {
	ego test -count=1 ./...
}

src_install() {
	dobin folkweave
	einstalldocs
	dodoc -r docs
	docinto examples
	dodoc -r deploy/caddy deploy/nginx deploy/apache
	docompress -x "/usr/share/doc/${PF}/examples"
	keepdir /var/lib/folkweave
	fowners folkweave:folkweave /var/lib/folkweave
	fperms 0700 /var/lib/folkweave
	sed 's|/usr/local/bin/folkweave|/usr/bin/folkweave|g' deploy/openrc/folkweave > "${T}/folkweave.initd" || die
	newinitd "${T}/folkweave.initd" folkweave
	newconfd deploy/openrc/folkweave.conf folkweave
	fperms 0600 /etc/conf.d/folkweave
	insinto /etc/logrotate.d
	newins deploy/logrotate/folkweave folkweave
	sed 's|/usr/local/bin/folkweave|/usr/bin/folkweave|g' \
		deploy/systemd/folkweave.service > "${T}/folkweave.service" || die
	systemd_dounit "${T}/folkweave.service"
	insinto /etc/folkweave
	newins deploy/systemd/folkweave.env folkweave.env
	fperms 0600 /etc/folkweave/folkweave.env
}

pkg_postinst() {
	elog "Browser setup: start the service, then run folkweave setup for its private key."
	elog "Command-line owner: folkweave create-owner --username NAME"
	elog "Password recovery: folkweave set-password --username NAME"
	elog "Account commands prompt privately; --password-stdin and --password-file support automation."
	elog "Configure /etc/conf.d/folkweave or /etc/folkweave/folkweave.env and your HTTPS proxy."
	elog "Native defaults: 127.0.0.1:8084 and /var/lib/folkweave."
	elog "Installed administrative commands invoked as root use the service account."
	elog "Read /usr/share/doc/${PF}/docs/ for installation, backups and recovery."
	elog "The service creates verified compressed backups daily; copy them off-host."
	elog "Back up before upgrading; restore a pre-upgrade snapshot to roll back."
	elog "https://github.com/airencracken/folkweave/tree/master/docs"
}
