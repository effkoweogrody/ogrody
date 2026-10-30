import unittest,subprocess,tempfile,os,shutil
from pathlib import Path
class LeadTests(unittest.TestCase):
 def test_lead_storage(self):
  php=shutil.which('php')
  if not php:self.skipTest('PHP runtime not available')
  with tempfile.TemporaryDirectory() as directory:
   env=dict(os.environ,CONTACT_PRIVATE_DIR=directory)
   result=subprocess.run([php,'-d','zend.assertions=1','-d','assert.exception=1',str(Path(__file__).with_suffix('.php'))],capture_output=True,text=True,env=env)
   self.assertEqual(result.returncode,0,result.stdout+result.stderr)
