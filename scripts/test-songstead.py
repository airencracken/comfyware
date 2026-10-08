#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
from pathlib import Path
import importlib.util
import subprocess
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('recipes',ROOT/'scripts/test-recipes.py');recipes=importlib.util.module_from_spec(spec);spec.loader.exec_module(recipes)
class SongsteadRecipes(unittest.TestCase):
 def test_release_preparation_and_live_parity(self):
  release=(ROOT/'release-preparation/songstead-0.1.0.ebuild').read_text();live=(ROOT/'www-apps/songstead/songstead-9999.ebuild').read_text()
  self.assertEqual(recipes.recipe_errors(release),[]);self.assertEqual(recipes.recipe_errors(live),[])
  self.assertEqual(recipes.live_equivalent(release,'songstead'),live)
  self.assertIn('EGIT_BRANCH="master"',live);self.assertIn('LICENSE="AGPL-3+',live)
  self.assertNotIn('sandbox',live);self.assertIn('acct-user/songstead',live)
 def test_unpublished_recipe_is_not_enabled_with_fake_checksums(self):
  self.assertFalse((ROOT/'www-apps/songstead/songstead-0.1.0.ebuild').exists())
  self.assertFalse((ROOT/'www-apps/songstead/Manifest').exists())
 def test_compile_version_and_accounts(self):
  recipe=ROOT/'www-apps/songstead/songstead-9999.ebuild';args=recipes.compile_arguments(recipe,'songstead','9999');recipes.validate_compiled_version(args,'9999')
  self.assertEqual(args[-1],'./cmd/songstead')
  for path in (recipe,ROOT/'acct-user/songstead/songstead-0.ebuild',ROOT/'acct-group/songstead/songstead-0.ebuild'):
   subprocess.run(['bash','-n',str(path)],check=True)
if __name__=='__main__':unittest.main(verbosity=2)
