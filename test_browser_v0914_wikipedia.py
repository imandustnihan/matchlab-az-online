"""Browser smoke-test of the Wikipedia club profile screen with mocked APIs."""
import unittest
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parent

class BrowserWikiTest(unittest.TestCase):
 def test_verified_club_profile_and_license(self):
  with sync_playwright() as p:
   browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
   page=browser.new_page()
   page.set_content('<html><head><meta charset="utf-8"></head><body><div id="app"></div></body></html>')
   page.add_style_tag(content=(ROOT/'styles.css').read_text())
   page.evaluate('''() => {
     window.ML_CATALOG=[{id:'Q12345678',kind:'teams',name:'FC Example',country:'Example',image:''}];
     window.ML_FEATURED={};
     const store={};Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem:k=>store[k]??null,setItem:(k,v)=>store[k]=String(v),removeItem:k=>delete store[k]}});
     window.fetch=async (url)=>{
       const path=String(url);
       let result={items:[]};
       if(path.startsWith('/api/status'))result={ok:true,backend:true,publicHosting:true,world:{total:506207,counts:{players:437525,teams:43031,coaches:24120}}};
       if(path.startsWith('/api/search'))result={items:window.ML_CATALOG,worldInstalled:true,nextOffset:null};
       if(path.startsWith('/api/profile'))result={profile:{id:'Q12345678',kind:'teams',name:'FC Example',stadium:'Example Stadium',stadiumCapacity:45000,foundedYear:1907,wikiSummary:'A historic football club in Example City.',wikiUrl:'https://en.wikipedia.org/wiki/FC_Example',careerUrl:'https://en.wikipedia.org/wiki/FC_Example',wikiPageLinks:{en:'https://en.wikipedia.org/wiki/FC_Example',az:'https://az.wikipedia.org/wiki/FK_N%C3%BCmun%C9%99'},imagePage:'https://commons.wikimedia.org/wiki/File:Logo.svg'}};
       return {ok:true,status:200,json:async()=>result};
     };
   }''')
   js=(ROOT/'app.js').read_text().replace("const BACKEND=()=>['http:','https:'].includes(location.protocol);",'const BACKEND=()=>true;')
   page.add_script_tag(content=js)
   page.wait_for_function("document.querySelector('.connection')?.textContent.includes('Server işləyir')",timeout=12000)
   page.locator('.sidebar [data-page="search"]').click()
   page.locator('[data-id="Q12345678"]').first.click(timeout=8000)
   page.wait_for_function("document.body.textContent.includes('Example Stadium')",timeout=12000)
   self.assertIn('A historic football club',page.locator('.wiki-excerpt').inner_text())
   self.assertIn('1907',page.locator('#app').inner_text())
   self.assertEqual(page.locator('a[href="https://creativecommons.org/licenses/by-sa/4.0/"]').count(),1)
   self.assertEqual(page.locator('a[href="https://az.wikipedia.org/wiki/FK_N%C3%BCmun%C9%99"]').count(),1)
   self.assertEqual(page.locator('[data-action="refresh-wikipedia"]').count(),0)
   browser.close()
if __name__=='__main__':unittest.main(verbosity=2)
