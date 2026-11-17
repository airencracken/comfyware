# Copyright 2026 Marcus J. Hildum
# SPDX-License-Identifier: AGPL-3.0-or-later

EAPI=8

inherit go-module systemd

DESCRIPTION="Self-hosted bulletin board for friends and family"
HOMEPAGE="https://github.com/airencracken/witmoot"
SRC_URI="
	https://github.com/airencracken/witmoot/releases/download/v${PV}/${PN}_${PV}_source.tar.gz
	https://github.com/airencracken/comfyware/releases/download/${P}/${P}-deps.tar.xz
"
S="${WORKDIR}/${PN}_${PV}_source"

# Witmoot uses AGPL-3.0-or-later. The remaining entries cover the linked
# Go dependencies, their bundled code, and the embedded HTMX asset.
LICENSE="AGPL-3+ Apache-2.0 0BSD BSD BSD-2 MIT public-domain"
SLOT="0"
KEYWORDS="~amd64 ~arm64"
IUSE="bubblewrap test +zstd"
RESTRICT="!test? ( test )"
DOCS=( README.md THIRD_PARTY.md )

RDEPEND="
	zstd? ( app-arch/zstd )
	bubblewrap? ( >=sys-apps/bubblewrap-0.8[-suid(-)] )
	acct-group/witmoot
	acct-user/witmoot
	app-admin/logrotate
	app-misc/ca-certificates
"
BDEPEND+="
	>=dev-lang/go-1.26.11
	acct-group/witmoot
	acct-user/witmoot
	test? ( app-admin/logrotate )
"

src_configure() {
	go-module_src_configure
}

src_compile() {
	CGO_ENABLED=0 ego build -trimpath -ldflags "-X main.version=${PV}" -o witmoot ./cmd/witmoot
}

src_test() {
	ego test -count=1 ./...
}

src_install() {
	dobin witmoot
	einstalldocs
	dodoc -r docs
	docinto examples
	dodoc -r contrib/caddy contrib/nginx contrib/apache
	# The proxy examples are meant to be copied as they are.
	docompress -x "/usr/share/doc/${PF}/examples"

	keepdir /var/lib/witmoot
	fowners witmoot:witmoot /var/lib/witmoot
	fperms 0700 /var/lib/witmoot

	# Packages install into /usr, unlike the source-install default.
	sed 's|/usr/local/bin/witmoot|/usr/bin/witmoot|g' \
		contrib/openrc/witmoot > "${T}/witmoot.initd" || die
	newinitd "${T}/witmoot.initd" witmoot
	newconfd contrib/openrc/witmoot.confd witmoot
	fperms 0600 /etc/conf.d/witmoot
	insinto /etc/logrotate.d
	newins contrib/logrotate/witmoot witmoot

	sed 's|/usr/local/bin/witmoot|/usr/bin/witmoot|g' \
		contrib/systemd/witmoot.service > "${T}/witmoot.service" || die
	systemd_dounit "${T}/witmoot.service"
	insinto /etc/witmoot
	newins contrib/systemd/witmoot.env witmoot.env
	fperms 0600 /etc/witmoot/witmoot.env
}

pkg_postinst() {
	if [[ -n ${REPLACING_VERSIONS} ]]; then
		elog "Updated to ${PV}. What changed: https://github.com/airencracken/witmoot/releases/tag/v${PV}"
		return
	fi

	elog "Browser setup: start the service, then run witmoot setup for its private key."
	elog "Command-line owner: witmoot create-owner --username NAME"
	elog "Password recovery: witmoot set-password --username NAME"
	elog "Configure /etc/conf.d/witmoot (OpenRC) or /etc/witmoot/witmoot.env (systemd)."
	elog "The service listens on 127.0.0.1:8082 and keeps data in /var/lib/witmoot."
	elog "Put an HTTPS reverse proxy in front before inviting people."
	elog "Automatic backups are built in: the service makes one daily and keeps seven."
	elog "Check them in instance settings and copy them off-host; see docs/automatic-backups.md."
	elog "Guides: /usr/share/doc/${PF}/docs/ and"
	elog "https://github.com/airencracken/witmoot/tree/v${PV}/docs"
	if use bubblewrap; then
		elog "Bubblewrap confinement is optional; see docs/sandbox.md."
	fi
}
