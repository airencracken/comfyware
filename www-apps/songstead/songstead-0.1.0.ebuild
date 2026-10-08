# Copyright 2026 Marcus J. Hildum
# SPDX-License-Identifier: AGPL-3.0-or-later

EAPI=8

inherit go-module systemd

DESCRIPTION="A quiet music recommendation shelf for friends and family"
HOMEPAGE="https://github.com/airencracken/songstead"
SRC_URI="
	https://github.com/airencracken/songstead/releases/download/v${PV}/${PN}_${PV}_source.tar.gz
	https://github.com/airencracken/comfyware/releases/download/${P}/${P}-deps.tar.xz
"
S="${WORKDIR}/${PN}_${PV}_source"

# Songstead uses AGPL-3.0-or-later. The remaining entries cover the linked
# Go dependencies, their bundled code, and the embedded HTMX asset.
LICENSE="AGPL-3+ 0BSD BSD BSD-2 MIT public-domain"
SLOT="0"
KEYWORDS="~amd64 ~arm64"
IUSE="test"
RESTRICT="!test? ( test )"
DOCS=( README.md THIRD_PARTY.md )

RDEPEND="
	acct-group/songstead
	acct-user/songstead
	app-admin/logrotate
	app-misc/ca-certificates
"
BDEPEND+="
	>=dev-lang/go-1.26.0
	acct-group/songstead
	acct-user/songstead
	test? ( app-admin/logrotate )
"

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
	elog "Configure /etc/conf.d/songstead (OpenRC) or /etc/songstead/songstead.env (systemd)."
	elog "The native service listens on 127.0.0.1:8083 and uses /var/lib/songstead."
	elog "Provision accounts before starting; see docs/deployment.md."
	elog "Both guides are in /usr/share/doc/${PF}/docs/ and at"
	elog "https://github.com/airencracken/songstead/tree/v${PV}/docs"
	elog "Startup applies migrations; back up the data directory before starting a new binary."
	elog "Back up the full data directory before upgrades; schema upgrades prevent downgrades."
}
