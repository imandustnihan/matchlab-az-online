"""Desktop/mobile smoke test for the originally empty Guardiola profile."""
import json, unittest
from pathlib import Path
from unittest.mock import patch
from playwright.sync_api import sync_playwright
import server

ROOT=Path(__file__).resolve().parent

class GuardiolaPage22(unittest.TestCase):
    def test_pep_renders_wikipedia_biography_and_player_manager_career(self):
        with patch.object(server,'get_json',side_effect=ConnectionError('offline')):
            profile=server.send_data('/api/profile',{'id':['c:pep-guardiola']})['profile']
        js=(ROOT/'app.js').read_text(encoding='utf8').replace("const BACKEND=()=>['http:','https:'].includes(location.protocol);",'const BACKEND=()=>true;')
        css=(ROOT/'styles.css').read_text(encoding='utf8')
        # Preserve actual local catalogue legacy IDs to exercise the user path.
        catalog=[r for r in server.CATALOG if r['id'] in ('c:pep-guardiola','p:pep-guardiola')]
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
            for device,width,height in [('desktop',1400,950),('mobile',390,844)]:
                page=browser.new_page(viewport={'width':width,'height':height})
                errs=[]
                page.on('pageerror',lambda error:errs.append(str(error)))
                page.set_content('<html lang="az"><head><meta charset="utf-8"></head><body><div id="app"></div></body></html>')
                page.add_style_tag(content=css)
                page.evaluate('''({catalog,profile})=>{
                  const local={};Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem:k=>local[k]??null,setItem:(k,v)=>{local[k]=String(v)},removeItem:k=>delete local[k]}});
                  window.ML_CATALOG=catalog;window.ML_FEATURED={};
                  window.fetch=async input=>{
                    const url=String(input);
                    let data={items:[]};
                    if(url.startsWith('/api/status'))data={ok:true,backend:true,world:{total:506207,counts:{players:437525,teams:43031,coaches:24120}},version:'0.9.22'};
                    else if(url.startsWith('/api/profile?'))data={profile};
                    else if(url.startsWith('/api/world/countries'))data={items:[]};
                    else if(url.startsWith('/api/search?'))data={items:[profile]};
                    else if(url.startsWith('/api/media-status'))data={};
                    else if(url.startsWith('/api/sources'))data={};
                    return {ok:true,status:200,json:async()=>data};
                  };
                }''',{'catalog':catalog,'profile':profile})
                page.add_script_tag(content=js)
                page.wait_for_function("document.querySelector('.connection')?.textContent.includes('Server işləyir')",timeout=10000)
                # Profile is a featured home entry; use click path, not direct string rendering.
                page.locator('[data-id="c:pep-guardiola"]').first.click(timeout=12000)
                page.wait_for_function("document.querySelector('.page')?.textContent.includes('Josep Guardiola Sala')",timeout=12000)
                body=page.locator('.page').inner_text()
                for label in ('1971-01-18','Barcelona B','Bayern Munich','Brescia','Dorados','Milli komanda karyerası','Məşqçilik karyerası','Santpedor','Müdafiəyönlü yarımmüdafiəçi'):
                    self.assertIn(label,body,(device,label))
                self.assertNotIn('Wikipedia-da bu profil üzrə təsdiqlənmiş klub statistikası yoxdur.',body)
                self.assertEqual(errs,[],(device,errs))
                page.screenshot(path=str(ROOT/f'preview_v0922_pep_{device}.png'),full_page=True)
                page.close()
            browser.close()

if __name__=='__main__': unittest.main()
