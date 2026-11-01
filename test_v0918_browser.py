"""Browser-based v0.9.18 regression: Arteta identity, pitch dark rectangle and career."""
import json
import unittest
from pathlib import Path
from unittest.mock import patch
import server
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parent

class Browser18(unittest.TestCase):
 def test_profile_search_and_clean_tactics_pitch_desktop_mobile(self):
  with patch.object(server,'get_json',side_effect=ConnectionError('offline')):
   arteta=server.send_data('/api/profile',{'id':['p:mikel-arteta']})['profile']
  result=server.send_data('/api/search',{'q':['Mikel Arteta'],'kind':['all']})
  legacy=[x for x in server.CATALOG if x['id'] in ('p:mikel-arteta','c:mikel-arteta')]
  js=(ROOT/'app.js').read_text(encoding='utf-8').replace("const BACKEND=()=>['http:','https:'].includes(location.protocol);",'const BACKEND=()=>true;')
  css=(ROOT/'styles.css').read_text(encoding='utf-8')
  with sync_playwright() as p:
   browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
   for name,width,height in [('desktop',1440,950),('mobile',390,844)]:
    page=browser.new_page(viewport={'width':width,'height':height})
    exceptions=[]
    page.on('pageerror', lambda error:exceptions.append(str(error)))
    page.set_content('<!doctype html><html lang="az"><head><meta charset="utf-8"></head><body><div id="app"></div></body></html>')
    page.add_style_tag(content=css)
    page.evaluate('''(data)=>{
      const memory={};
      Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem:k=>memory[k]??null,setItem:(k,v)=>{memory[k]=String(v)},removeItem:k=>delete memory[k]}});
      window.ML_CATALOG=data.legacy;
      window.ML_FEATURED={};
      window.fetch=async input=>{
        const url=String(input);let d={items:[]};
        if(url.startsWith('/api/status'))d={ok:true,backend:true,world:{total:506207,counts:{players:437525,teams:43031,coaches:24120}},version:'0.9.18'};
        else if(url.startsWith('/api/search'))d=data.search;
        else if(url.startsWith('/api/profile'))d={profile:data.profile};
        else if(url.startsWith('/api/photos'))d={items:{}};
        else if(url.startsWith('/api/world/countries'))d={items:[]};
        return {ok:true,status:200,json:async()=>d};
      };
    }''',{'legacy':legacy,'search':result,'profile':arteta})
    page.add_script_tag(content=js)
    page.wait_for_function("document.querySelector('.connection')?.textContent.includes('Server işləyir')",timeout=12000)
    page.locator(('.mobilebar ' if name=='mobile' else '.sidebar ')+ '[data-page="search"]').first.click()
    page.locator('#search-input').fill('Mikel Arteta')
    page.locator('#main-search button').click()
    page.wait_for_function("document.querySelector('.entity .name')?.textContent.includes('Mikel Arteta')",timeout=12000)
    self.assertEqual(page.locator('.entity').count(),1)
    self.assertIn('Futbolçu / məşqçi',page.locator('.entity').first.inner_text())
    page.locator('.entity').first.click()
    page.wait_for_function("document.querySelector('.career-scroll')?.textContent.includes('Paris Saint-Germain')",timeout=12000)
    self.assertIn('Arsenal',page.locator('.career-scroll').inner_text())
    self.assertIn('Manchester City',page.locator('.timeline').first.inner_text())
    page.locator('[data-action="to-tactic-profile"]').click()
    self.assertEqual(page.locator('#pitch .player-dot').count(),11)
    self.assertEqual(page.locator('#pitch .player-dot[data-player="0"] .pname').inner_text(),'Qapıçı')
    self.assertEqual(page.locator('#pitch .player-dot[data-player="6"] .pname').inner_text(),'Mikel Arteta Amatriain')
    self.assertEqual(page.locator('#tactic-role').input_value(),'CM')
    north=page.locator('#pitch .area.pitch-north')
    self.assertEqual(north.count(),1)
    info=north.evaluate('''el=>{const s=getComputedStyle(el);return {background:s.backgroundColor,position:s.position,filter:s.backdropFilter}}''')
    self.assertEqual(info['background'],'rgba(0, 0, 0, 0)')
    self.assertEqual(info['position'],'absolute')
    self.assertEqual(info['filter'],'none')
    page.screenshot(path=str(ROOT/f'preview_v0918_tactic_{name}.png'),full_page=(name=='desktop'))
    self.assertEqual(exceptions,[])
    page.close()
   browser.close()

if __name__=='__main__':unittest.main(verbosity=2)
