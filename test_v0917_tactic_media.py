"""Playwright: a QID-identified footballer can be placed on tactics pitch with a photo."""
import base64
import unittest
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parent
PNG=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jZxoAAAAASUVORK5CYII=')

class TacticMedia17(unittest.TestCase):
 def test_profile_to_pitch_and_exportable_identity(self):
  with sync_playwright() as p:
   browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
   page=browser.new_page(viewport={'width':1280,'height':900})
   page.route('https://commons.wikimedia.org/**',lambda route:route.fulfill(status=200,body=PNG,content_type='image/png'))
   page.set_content('<html><head><meta charset="utf-8"></head><body><div id="app"></div></body></html>')
   page.add_style_tag(content=(ROOT/'styles.css').read_text(encoding='utf-8'))
   page.evaluate('''() => {
      const memory={};Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem:k=>memory[k]??null,setItem:(k,v)=>{memory[k]=String(v)},removeItem:k=>{delete memory[k]}}});
      window.ML_CATALOG=[{id:'Q5705',qid:'Q5705',kind:'players',name:'Example Star',country:'Azerbaijan',image:'https://commons.wikimedia.org/wiki/Special:FilePath/Example_star.jpg?width=280'}];
      window.ML_FEATURED={};
      window.fetch=async (input)=>{let url=String(input);let d={items:[]};
       if(url.startsWith('/api/status'))d={ok:true,backend:true,world:{total:506207,counts:{players:437525,teams:43031,coaches:24120}}};
       else if(url.startsWith('/api/profile'))d={profile:{id:'Q5705',qid:'Q5705',kind:'players',name:'Example Star',image:'https://commons.wikimedia.org/wiki/Special:FilePath/Example_star.jpg?width=280'}};
       else if(url.startsWith('/api/search'))d={items:window.ML_CATALOG,worldInstalled:true,nextOffset:null};
       return {ok:true,status:200,json:async()=>d};
      };
    }''')
   script=(ROOT/'app.js').read_text(encoding='utf8').replace("const BACKEND=()=>['http:','https:'].includes(location.protocol);",'const BACKEND=()=>true;')
   page.add_script_tag(content=script)
   page.locator('[data-id="Q5705"]').first.click(timeout=9000)
   page.locator('[data-action="to-tactic-profile"]').click(timeout=9000)
   page.locator('#pitch .player-dot').first.wait_for(timeout=9000)
   self.assertEqual(page.locator('#pitch .player-dot').count(),11)
   self.assertEqual(page.locator('#pitch .tactic-portrait').count(),1)
   self.assertIn('Example Star',page.locator('#pitch .player-dot').first.inner_text())
   saved=page.evaluate("JSON.parse(localStorage.getItem('matchlab_v08_pitchPlayers')||'[]')")
   self.assertEqual(saved[0]['profileId'],'Q5705')
   self.assertEqual(saved[0]['name'],'Example Star')
   self.assertTrue(saved[0]['image'].startswith('https://commons.wikimedia.org/'))
   browser.close()

if __name__=='__main__':unittest.main(verbosity=2)
