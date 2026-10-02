# Copyright 2026 Marcus J. Hildum
# SPDX-License-Identifier: AGPL-3.0-or-later
# Live ebuild for the master branch.

EAPI=8

inherit git-r3 go-module systemd

DESCRIPTION="Self-hosted photo and short clip library for friends and family"
HOMEPAGE="https://github.com/airencracken/imvault"
EGIT_REPO_URI="https://github.com/airencracken/imvault.git"
EGIT_BRANCH="master"

# Include the linked Go dependencies, bundled libc/SQLite code, and web assets.
LICENSE="AGPL-3+ Apache-2.0 0BSD BSD BSD-2 MIT public-domain"
SLOT="0"
# go-module_live_vendor refuses to run without this.
PROPERTIES="live"
IUSE="bubblewrap ffmpeg"

# ffmpeg is optional. Without it clips are still accepted, but they get a
# placeholder poster instead of a frame from the video, and the duration limit
# cannot be enforced.
RDEPEND="
	bubblewrap? ( sys-apps/bubblewrap[-suid(-)] )
	acct-group/imvault
	acct-user/imvault
	app-admin/logrotate
	app-misc/ca-certificates
	ffmpeg? ( media-video/ffmpeg )
"
# The eclass asks for the Go it knows about. go.mod asks for 1.26, so add that
# rather than replacing the eclass's line, which carries the slot operator and a
# packaging workaround of its own.
BDEPEND+="
	>=dev-lang/go-1.26
	acct-group/imvault
	acct-user/imvault
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
	# The SQLite driver is pure Go. Portage strips the binary itself, which
	# keeps FEATURES=splitdebug and nostrip working.
	CGO_ENABLED=0 ego build -trimpath -o imvault ./cmd/imvault
}

src_test() {
	ego test ./...
}

src_install() {
	dobin imvault
	einstalldocs
	dodoc -r docs
	docinto examples
	dodoc -r contrib/caddy contrib/nginx contrib/apache
	# The proxy examples are meant to be copied as they are.
	docompress -x "/usr/share/doc/${PF}/examples"

	# The database and the uploaded bytes live here.
	keepdir /var/lib/imvault
	fowners imvault:imvault /var/lib/imvault
	fperms 0750 /var/lib/imvault

	newinitd contrib/openrc/imvault imvault
	newconfd contrib/openrc/imvault.confd imvault
	fperms 0600 /etc/conf.d/imvault
	insinto /etc/logrotate.d
	newins contrib/logrotate/imvault imvault

	# Packages install into /usr, unlike the source-install default.
	sed 's|/usr/local/bin/imvault|/usr/bin/imvault|g' \
		contrib/systemd/imvault.service > "${T}/imvault.service" || die
	systemd_dounit "${T}/imvault.service"
	insinto /etc/imvault
	newins contrib/systemd/imvault.env imvault.env
	# Group-readable so commands run as the imvault user can find the service
	# settings, matching upstream's install instructions.
	fowners root:imvault /etc/imvault/imvault.env
	fperms 0640 /etc/imvault/imvault.env
}

pkg_postinst() {
	elog "Configure /etc/conf.d/imvault (OpenRC) or /etc/imvault/imvault.env (systemd)."
	elog "Provision an administrator before starting; see docs/deployment.md."
	elog "Bubblewrap confinement is optional; see docs/sandbox.md."
	elog "Both guides are in /usr/share/doc/${PF}/docs/ and at"
	elog "https://github.com/airencracken/imvault/tree/master/docs"
}
