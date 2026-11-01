"""Real localhost HTTP integration tests (stdlib server, no outside APIs)."""
import json
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from hosting_server import PublicHandler
from server import Handler

class HttpV0915(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.local=ThreadingHTTPServer(('127.0.0.1',0),Handler)
  cls.public=ThreadingHTTPServer(('127.0.0.1',0),PublicHandler)
  for obj in [cls.local,cls.public]:threading.Thread(target=obj.serve_forever,daemon=True).start()
 @classmethod
 def tearDownClass(cls):
  for obj in [cls.local,cls.public]:obj.shutdown();obj.server_close()
 def request(self,handler,path):
  port=self.local.server_port if handler=='local' else self.public.server_port
  url=f'http://127.0.0.1:{port}'+path
  try:
   with urllib.request.urlopen(url,timeout=5) as r:return r.status,r.read()
  except urllib.error.HTTPError as err:return err.code,err.read()
 def test_local_status_and_assets(self):
  status,body=self.request('local','/api/status')
  self.assertEqual(status,200)
  data=json.loads(body)
  self.assertEqual(data['version'],'0.9.21-local')
  self.assertEqual(data['world']['total'],506207)
  for p in ['/','/index.html','/app.js?v=0916','/styles.css?v=0916','/catalog.js','/assets/icon.svg']:
   self.assertEqual(self.request('local',p)[0],200,p)
 def test_public_health_and_private_assets(self):
  status,body=self.request('public','/healthz')
  self.assertEqual(status,200)
  self.assertTrue(json.loads(body)['ok'])
  self.assertEqual(json.loads(body)['version'],'0.9.20')
  for p in ['/server.py','/world_football.sqlite','/wikipedia_profiles.sqlite','/api/wikipedia-refresh?id=Q5705']:
   self.assertIn(self.request('public',p)[0],(403,404),p)
 def test_public_profile_lookup_by_invalid_id(self):
  status,body=self.request('public','/api/profile?id=Q0')
  self.assertEqual(status,200)
  self.assertIsNone(json.loads(body)['profile'])

if __name__=='__main__':unittest.main(verbosity=2)
