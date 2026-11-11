# Copyright 2026 Marcus J. Hildum
# SPDX-License-Identifier: AGPL-3.0-or-later
# Live ebuild for the master branch.

EAPI=8

inherit git-r3 go-module systemd

DESCRIPTION="A quiet self-hosted RSS and Atom reader"
HOMEPAGE="https://github.com/airencracken/tidings"
EGIT_REPO_URI="https://github.com/airencracken/tidings.git"
EGIT_BRANCH="master"

LICENSE="AGPL-3+ Apache-2.0 0BSD BSD BSD-2 MIT public-domain"
SLOT="0"
# go-module_live_vendor refuses to run without this.
PROPERTIES="live"
IUSE="test +zstd"
RESTRICT="!test? ( test )"
DOCS=( README.md THIRD_PARTY.md )

RDEPEND="
	acct-group/tidings
	acct-user/tidings
	app-admin/logrotate
	app-misc/ca-certificates
	zstd? ( app-arch/zstd )
"
BDEPEND+="
	>=dev-lang/go-1.26.11
	acct-group/tidings
	acct-user/tidings
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
	CGO_ENABLED=0 ego build -trimpath -ldflags "-X main.version=${PV}" -o tidings ./cmd/tidings
}

src_test() {
	ego test -count=1 ./...
}

src_install() {
	dobin tidings
	einstalldocs
	dodoc -r docs
	docinto examples
	dodoc -r deploy/caddy deploy/nginx deploy/apache
	docompress -x "/usr/share/doc/${PF}/examples"
	keepdir /var/lib/tidings
	fowners tidings:tidings /var/lib/tidings
	fperms 0700 /var/lib/tidings
	sed 's|/usr/local/bin/tidings|/usr/bin/tidings|g' deploy/openrc/tidings > "${T}/tidings.initd" || die
	newinitd "${T}/tidings.initd" tidings
	newconfd deploy/openrc/tidings.conf tidings
	fperms 0600 /etc/conf.d/tidings
	insinto /etc/logrotate.d
	newins deploy/logrotate/tidings tidings
	sed 's|/usr/local/bin/tidings|/usr/bin/tidings|g' deploy/systemd/tidings.service > "${T}/tidings.service" || die
	systemd_dounit "${T}/tidings.service"
	insinto /etc/tidings
	newins deploy/systemd/tidings.env tidings.env
	fperms 0600 /etc/tidings/tidings.env
}

pkg_postinst() {
	elog "Browser setup: start the service, then run tidings setup for its private key."
	elog "Command-line owner: tidings create-owner --username NAME"
	elog "Password recovery: tidings set-password --username NAME"
	elog "Account commands prompt privately; --password-stdin and --password-file support automation."
	elog "Configure /etc/conf.d/tidings or /etc/tidings/tidings.env and your HTTPS proxy."
	elog "Native defaults: 127.0.0.1:8085 and /var/lib/tidings."
	elog "Installed administrative commands invoked as root use the service account."
	elog "Read /usr/share/doc/${PF}/docs/ for installation, backups and recovery."
	elog "The service creates verified compressed backups daily; copy them off-host."
	elog "Back up before upgrading; restore a pre-upgrade snapshot to roll back."
	elog "https://github.com/airencracken/tidings/tree/master/docs"
}
