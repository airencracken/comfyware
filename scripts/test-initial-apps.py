#!/usr/bin/env python3
"""Initial-app release/live, service-account, build and documentation contracts."""
from pathlib import Path
import importlib.util
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('recipes',ROOT/'scripts/test-recipes.py')
recipes=importlib.util.module_from_spec(spec);spec.loader.exec_module(recipes)

class InitialAppTests(unittest.TestCase):
    def test_native_recipes_match_and_stamp_versions(self):
        for app,version in (('folkweave','0.3.4'),('tidings','0.5.4')):
            package=ROOT/'www-apps'/app
            text=(package/f'{app}-{version}.ebuild').read_text()
            self.assertEqual(recipes.recipe_errors(text),[])
            self.assertEqual((package/f'{app}-9999.ebuild').read_text(),recipes.live_equivalent(text,app))
            args=recipes.compile_arguments(package/f'{app}-{version}.ebuild',app,version)
            self.assertIn('main.version='+version,' '.join(args))
            self.assertIn('./cmd/'+app,args)
            for expected in ('acct-user/'+app,'acct-group/'+app,'fperms 0700 /var/lib/'+app,
                             'fperms 0600 /etc/conf.d/'+app,'deploy/systemd/'+app+'.service',
                             'deploy/openrc/'+app+'.conf','deploy/logrotate/'+app):
                self.assertIn(expected,text)
            for category in ('acct-user','acct-group'):
                account=(ROOT/category/app/f'{app}-0.ebuild').read_text()
                self.assertIn('ID=-1',account)
            self.assertIn('www-apps/'+app,(ROOT/'README.md').read_text())

if __name__=='__main__':unittest.main(verbosity=2)
