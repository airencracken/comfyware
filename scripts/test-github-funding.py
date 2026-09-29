#!/usr/bin/env python3
"""Check funding configuration and, with --live, GitHub's public sidebars."""

import json
import subprocess
import sys
import unittest
import urllib.request

REPOSITORIES = ("comfyware", "comfyware_org", "imvault", "witmoot")
SUPPORT_URL = "https://ko-fi.com/airencracken"
LIVE = "--live" in sys.argv
if LIVE:
    sys.argv.remove("--live")


def funding_errors(repositories):
    errors = []
    for name in REPOSITORIES:
        repository = repositories.get(name)
        if not isinstance(repository, dict):
            errors.append(f"{name}: repository data missing")
            continue
        if repository.get("hasSponsorshipsEnabled") is not True:
            errors.append(f"{name}: Sponsorships disabled")
        links = repository.get("fundingLinks")
        if not isinstance(links, list) or not any(
            isinstance(link, dict) and link.get("platform") == "KO_FI"
            and link.get("url") == SUPPORT_URL for link in links
        ):
            errors.append(f"{name}: expected Ko-fi link missing")
    return errors


class FundingContractTests(unittest.TestCase):
    def fixture(self):
        return {name: {"hasSponsorshipsEnabled": True,
                       "fundingLinks": [{"platform": "KO_FI", "url": SUPPORT_URL}]}
                for name in REPOSITORIES}

    def test_enabled_setting_and_correct_destination_are_required(self):
        self.assertEqual(funding_errors(self.fixture()), [])
        for name in REPOSITORIES:
            for value in (False, None, 0, "true"):
                with self.subTest(repository=name, value=value):
                    fixture = self.fixture()
                    fixture[name]["hasSponsorshipsEnabled"] = value
                    self.assertEqual(funding_errors(fixture), [f"{name}: Sponsorships disabled"])

    def test_missing_or_misdirected_funding_is_rejected(self):
        for links in ([], None, [None], [{"platform": "KO_FI", "url": "https://example.com"}],
                      [{"platform": "CUSTOM", "url": SUPPORT_URL}]):
            with self.subTest(links=links):
                fixture = self.fixture()
                fixture["comfyware"]["fundingLinks"] = links
                self.assertEqual(funding_errors(fixture), ["comfyware: expected Ko-fi link missing"])

    def test_missing_repository_cannot_pass(self):
        fixture = self.fixture()
        del fixture["witmoot"]
        self.assertEqual(funding_errors(fixture), ["witmoot: repository data missing"])


@unittest.skipUnless(LIVE, "Pass --live to check GitHub using authenticated gh and public HTTPS")
class LiveFundingTests(unittest.TestCase):
    def test_github_recognizes_enabled_funding_for_every_repository(self):
        fields = "hasSponsorshipsEnabled fundingLinks{platform url}"
        query = "{" + " ".join(
            f'{name}:repository(owner:"airencracken",name:"{name}"){{{fields}}}'
            for name in REPOSITORIES
        ) + "}"
        result = subprocess.run(["gh", "api", "graphql", "-f", "query=" + query],
                                check=True, capture_output=True, text=True, timeout=30)
        payload = json.loads(result.stdout)
        self.assertFalse(payload.get("errors"), payload.get("errors"))
        self.assertEqual(funding_errors(payload["data"]), [])

    def test_public_sidebars_display_the_sponsor_section(self):
        for name in REPOSITORIES:
            with self.subTest(repository=name):
                request = urllib.request.Request(f"https://github.com/airencracken/{name}",
                                                 headers={"User-Agent": "comfyware-funding-check"})
                with urllib.request.urlopen(request, timeout=20) as response:
                    html = response.read().decode()
                self.assertTrue("Sponsor this project" in html, f"{name}: sponsor sidebar missing")
                self.assertTrue(SUPPORT_URL in html, f"{name}: Ko-fi destination missing")


if __name__ == "__main__":
    unittest.main(verbosity=2)
