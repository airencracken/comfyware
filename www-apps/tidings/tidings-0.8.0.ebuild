# Copyright 2026 Marcus J. Hildum
# SPDX-License-Identifier: AGPL-3.0-or-later

EAPI=8

inherit go-module systemd

DESCRIPTION="Self-hosted RSS and Atom reader for friends and family"
HOMEPAGE="https://github.com/airencracken/tidings"
SRC_URI="
	https://github.com/airencracken/tidings/releases/download/v${PV}/${PN}_${PV}_source.tar.gz
	https://github.com/airencracken/comfyware/releases/download/${P}/${P}-deps.tar.xz
"
S="${WORKDIR}/${PN}_${PV}_source"

LICENSE="AGPL-3+ Apache-2.0 0BSD BSD BSD-2 MIT public-domain"
SLOT="0"
KEYWORDS="~amd64 ~arm64"
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
	if [[ -n ${REPLACING_VERSIONS} ]]; then
		elog "Updated to ${PV}. What changed: https://github.com/airencracken/tidings/releases/tag/v${PV}"
		return
	fi

	elog "Browser setup: start the service, then run tidings setup for its private key."
	elog "Command-line owner: tidings create-owner --username NAME"
	elog "Password recovery: tidings set-password --username NAME"
	elog "Configure /etc/conf.d/tidings (OpenRC) or /etc/tidings/tidings.env (systemd)."
	elog "The service listens on 127.0.0.1:8085 and keeps data in /var/lib/tidings."
	elog "Put an HTTPS reverse proxy in front before inviting people."
	elog "Automatic backups are built in: the service makes one daily and keeps seven."
	elog "Owners can check them in settings. Copy them off-host; see docs/automatic-backups.md."
	elog "Guides: /usr/share/doc/${PF}/docs/ and"
	elog "https://github.com/airencracken/tidings/tree/v${PV}/docs"
}
