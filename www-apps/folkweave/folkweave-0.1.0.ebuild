# Copyright 2026 Marcus J. Hildum
# SPDX-License-Identifier: AGPL-3.0-or-later

EAPI=8

inherit go-module systemd

DESCRIPTION="Private posts and photos for a small group"
HOMEPAGE="https://github.com/airencracken/folkweave"
SRC_URI="
	https://github.com/airencracken/folkweave/releases/download/v${PV}/${PN}_${PV}_source.tar.gz
	https://github.com/airencracken/comfyware/releases/download/${P}/${P}-deps.tar.xz
"
S="${WORKDIR}/${PN}_${PV}_source"

LICENSE="AGPL-3+ 0BSD BSD BSD-2 MIT public-domain"
SLOT="0"
KEYWORDS="~amd64 ~arm64"
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
	elog "Configure /etc/conf.d/folkweave or /etc/folkweave/folkweave.env and your HTTPS proxy."
	elog "Native defaults: 127.0.0.1:8084 and /var/lib/folkweave."
	elog "Provision the owner before starting: folkweave init --username NAME"
	elog "Installed administrative commands invoked as root use the service account."
	elog "Read /usr/share/doc/${PF}/docs/ for installation, backups and recovery."
	elog "The service creates verified compressed backups daily; copy them off-host."
	elog "Back up before upgrading; restore a pre-upgrade snapshot to roll back."
	elog "https://github.com/airencracken/folkweave/tree/v${PV}/docs"
}
