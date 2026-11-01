"""Desktop/mobile browser regression with deterministic club data (not live Wikipedia)."""
import unittest
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parent

class ClubBrowser20(unittest.TestCase):
 def test_four_features_desktop_mobile_and_settings(self):
  js=(ROOT/'app.js').read_text(encoding='utf8').replace("const BACKEND=()=>['http:','https:'].includes(location.protocol);",'const BACKEND=()=>true;')
  css=(ROOT/'styles.css').read_text(encoding='utf8')
  with sync_playwright() as playwright:
   b=playwright.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
   for label,width,height in [('desktop',1440,950),('mobile',390,844)]:
    page=b.new_page(viewport={'width':width,'height':height});errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.set_content('<html lang="az"><head><meta charset="utf-8"></head><body><div id="app"></div></body></html>')
    page.add_style_tag(content=css)
    page.evaluate('''()=>{
      const saved={};Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem:k=>saved[k]??null,setItem:(k,v)=>{saved[k]=String(v)},removeItem:k=>delete saved[k]}});
      window.ML_CATALOG=[{id:'Q8682',name:'Example Club',kind:'teams',country:'Spain',image:''},{id:'Q5705',name:'Example Star',kind:'players',country:'Spain',clubs:['Example Club']}];window.ML_FEATURED={};
      const club={id:'Q8682',qid:'Q8682',name:'Example Club',kind:'teams',country:'Spain',foundedYear:1902,city:'Madrid',stadium:'Example Stadium',stadiumCapacity:83186,league:'La Liga',colors:'White',honours:[{name:'La Liga',count:36,category:'Domestic'},{name:'UEFA Champions League',count:15,category:'International'}],squadSnapshot:[{name:'Example Keeper',number:'1',position:'GK'},{name:'Example Forward',number:'9',position:'FW'}],squadChecked:'2026-11-01',wikiUrl:'https://en.wikipedia.org/wiki/Example_Club',historicalConnections:{players:[{id:'Q5705',name:'Example Star',kind:'players',career:[{name:'Example Club',from:2001,to:2008}]}],coaches:[{id:'Q185572',name:'Example Coach',kind:'coaches'}]},stadiumPhoto:'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a9/example.jpg',stadiumPhotoPage:'https://commons.wikimedia.org/wiki/File:Example.jpg',stadiumPhotoLicense:'CC BY-SA 4.0',stadiumPhotoLicenseUrl:'https://creativecommons.org/licenses/by-sa/4.0/',colorHexes:['#FFFFFF','#0000FF'],source:'Test fixture'};
      window.fetch=async input=>{const url=String(input);let data={items:[]};
       if(url.startsWith('/api/status'))data={ok:true,backend:true,world:{total:506207,counts:{players:437525,teams:43031,coaches:24120}},version:'0.9.20'};
       else if(url.startsWith('/api/profile?id=Q8682'))data={profile:club};
       else if(url.startsWith('/api/profile?id=Q5705'))data={profile:{id:'Q5705',name:'Example Star',kind:'players',clubs:[{name:'Example Club',from:2001,to:2008}],source:'Test fixture'}};
       else if(url.startsWith('/api/world/countries'))data={items:[]};
       else if(url.startsWith('/api/photos'))data={items:{}};
       return {ok:true,status:200,json:async()=>data};
      };
    }''')
    page.add_script_tag(content=js)
    page.wait_for_function("document.querySelector('.connection')?.textContent.includes('Server işləyir')",timeout=15000)
    page.locator('[data-id="Q8682"]').first.click()
    page.wait_for_selector('#club-honours .honour-item',timeout=10000)
    self.assertIn('36 dəfə',page.locator('#club-honours').inner_text())
    self.assertIn('15 dəfə',page.locator('#club-honours').inner_text())
    self.assertEqual(page.locator('#club-squad .club-squad-row').count(),2)
    self.assertIn('rəsmi cari heyət deyil',page.locator('#club-squad').inner_text().lower())
    self.assertEqual(page.locator('#club-stadium .club-stadium-image img').count(),1)
    self.assertEqual(page.locator('#club-stadium .club-swatch').count(),2)
    self.assertEqual(page.locator('#club-history [data-id="Q5705"]').count(),1)
    page.screenshot(path=str(ROOT/f'preview_v0920_club_{label}.png'),full_page=True)
    page.locator(('.mobilebar ' if label=='mobile' else '.sidebar ')+'[data-page="settings"]').first.click()
    opt=page.locator('[data-club-pref="showClubHonours"]')
    self.assertTrue(opt.is_checked())
    opt.uncheck()
    page.locator(('.mobilebar ' if label=='mobile' else '.sidebar ')+'[data-page="home"]').first.click()
    page.locator('[data-id="Q8682"]').first.click()
    page.wait_for_selector('#club-stadium')
    self.assertEqual(page.locator('#club-honours').count(),0)
    self.assertEqual(errors,[])
    page.close()
   b.close()

if __name__=='__main__':unittest.main(verbosity=2)
