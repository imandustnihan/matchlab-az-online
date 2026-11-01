"""v0.9.21 deterministic desktop/mobile tests (fake football API, real browser)."""
import unittest
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parent

class SeasonCompareBrowser21(unittest.TestCase):
    def test_compare_search_real_routes_and_season_assists(self):
        js=(ROOT/'app.js').read_text(encoding='utf8').replace("const BACKEND=()=>['http:','https:'].includes(location.protocol);",'const BACKEND=()=>true;')
        css=(ROOT/'styles.css').read_text(encoding='utf8')
        with sync_playwright() as pw:
            b=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
            for device,w,h in [('desktop',1400,900),('mobile',390,844)]:
                page=b.new_page(viewport={'width':w,'height':h})
                errors=[]
                page.on('pageerror',lambda e:errors.append(str(e)))
                page.set_content('<html lang="az"><head><meta charset="utf-8"></head><body><div id="app"></div></body></html>')
                page.add_style_tag(content=css)
                page.evaluate('''()=>{
                  const saved={};Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem:k=>saved[k]??null,setItem:(k,v)=>{saved[k]=String(v)},removeItem:k=>delete saved[k]}});
                  window.ML_CATALOG=[
                   {id:'Q5705',name:'Lionel Messi',kind:'players',country:'Argentina',birth:'1987-06-24'},
                   {id:'Q11571',name:'Cristiano Ronaldo',kind:'players',country:'Portugal',birth:'1985-02-05'}];
                  window.ML_FEATURED={};
                  window.fetch=async input=>{
                   let url=String(input);let data={items:[]};
                   if(url.startsWith('/api/status'))data={ok:true,backend:true,world:{total:506207,counts:{players:437525,teams:43031,coaches:24120}},version:'0.9.21'};
                   else if(url.startsWith('/api/search?kind=players&q=Kevin'))data={items:[{id:'rp1234567890',name:'Kevin De Bruyne',kind:'players',birth:'1991-06-28',country:'Belgium'}]};
                   else if(url.startsWith('/api/profile?id=')){
                     const id=new URL('https://example.com'+url).searchParams.get('id');
                     const base=id==='rp1234567890'?{id,name:'Kevin De Bruyne',country:'Belgium',birth:'1991-06-28'}:id==='Q5705'?{id,name:'Lionel Messi',country:'Argentina',birth:'1987-06-24'}:{id,name:'Cristiano Ronaldo',country:'Portugal',birth:'1985-02-05'};
                     data={profile:{...base,kind:'players',clubs:[{name:'Example FC',apps:100,goals:30,assists:null}]}};
                   }
                   else if(url.startsWith('/api/season-stats?id=')){
                     const id=new URL('https://example.com'+url).searchParams.get('id');
                     const as=id==='rp1234567890'?20:id==='Q5705'?8:7;
                     data={available:true,partial:true,identityVerified:true,source:'TheSportsDB V1 Free (məhdud)',sourceUrl:'https://www.thesportsdb.com/api/v1/json/123/lookupplayerstats.php?id=1',notice:'Pulsuz mənbə natamamdır.',items:[{season:'2025-2026',competition:'La Liga',team:'Demo',appearances:31,goals:11,assists:as,minutes:2400}]};
                   }
                   else if(url.startsWith('/api/world/countries'))data={items:[]};
                   return {ok:true,status:200,json:async()=>data};
                  };
                }''')
                page.add_script_tag(content=js)
                page.wait_for_function("document.querySelector('.connection')?.textContent.includes('Server işləyir')",timeout=10000)
                # Open compare using navigation for both desktop and mobile.
                if device=='desktop':page.locator('.sidebar [data-page="compare"]').click()
                else:page.locator('.mobilebar [data-page="compare"]').click()
                page.wait_for_selector('[data-compare-form="A"]',timeout=10000)
                page.wait_for_function("document.querySelectorAll('.career-table').length >= 2",timeout=12000)
                self.assertIn('Asist',page.locator('.page').inner_text())
                self.assertIn('8',page.locator('.page').inner_text())
                page.locator('[data-compare-form="A"] input').fill('Kevin')
                page.locator('[data-compare-form="A"] button[type=submit]').click()
                page.wait_for_selector('[data-compare-pick="A|rp1234567890"]')
                page.locator('[data-compare-pick="A|rp1234567890"]').click()
                page.wait_for_function("document.querySelector('.comparebox')?.textContent.includes('Kevin De Bruyne')",timeout=10000)
                page.wait_for_function("document.querySelector('.page')?.textContent.includes('20')",timeout=12000)
                self.assertIn('Mənbəli statistikalar',page.locator('.page').inner_text())
                self.assertEqual(errors,[],errors)
                page.close()
            b.close()

if __name__=='__main__':unittest.main()
