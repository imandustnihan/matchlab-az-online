"""MATCHLAB AZ independent live-center UI checks with deterministic mock feeds.
Mock scores do not represent real live provider access."""
import unittest
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parent
class LiveCenter(unittest.TestCase):
 def test_matches_interactions_and_mobile(self):
  with sync_playwright() as p:
   browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
   for kind,w,h in [('desktop',1370,900),('mobile',390,844)]:
    page=browser.new_page(viewport={'width':w,'height':h});errors=[]
    page.on('pageerror', lambda e:errors.append(str(e)))
    page.set_content('<html><head><meta charset="utf-8"></head><body><div id="app"></div></body></html>')
    page.evaluate("""() => { const store={};Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem:k=>store[k]??null,setItem:(k,v)=>{store[k]=String(v)},removeItem:k=>{delete store[k]}}}); }""")
    page.add_style_tag(content=(ROOT/'styles.css').read_text())
    page.evaluate('''() => {
      window.ML_CATALOG=[];window.ML_FEATURED={};
      const mk=(league,n,state)=>({id:`espn:${league}:${n}`,eventId:String(n),league,home:{id:'10',name:league==='eng.1'?'Home FC':'Madrid FC',image:''},away:{id:'20',name:'Away FC',image:''},homeScore:state==='scheduled'?null:2,awayScore:state==='scheduled'?null:1,state,minute:state==='live'?"72'":'',date:'2026-10-31T19:00:00Z',source:'Local mock fixture',stale:false});
      window.feed=[mk('eng.1',760415,'live'),mk('esp.1',760416,'final'),mk('eng.1',760417,'scheduled')];
      window.fetch=async function(input){let path=String(input),data={};
        if(path.startsWith('/api/status'))data={ok:true,backend:true,world:{total:506207,counts:{players:437525,teams:43031,coaches:24120}},version:'0.9.12'};
        else if(path.startsWith('/api/live'))data={available:true,source:'Test fixture',checkedAt:new Date().toISOString(),coverage:{checked:12,available:2},items:window.feed};
        else if(path.startsWith('/api/match-detail'))data={available:true,source:'Test fixture',lineup:{home:{starters:[],substitutes:[]},away:{starters:[],substitutes:[]}},events:[{clock:"72'",text:'A test goal'}],statistics:[{name:'Shots',home:3,away:1}]};
        else data={items:[]}; return {ok:true,status:200,json:async()=>data};
      }
    }''')
    js=(ROOT/'app.js').read_text().replace("const BACKEND=()=>['http:','https:'].includes(location.protocol);", 'const BACKEND=()=>true;')
    page.add_script_tag(content=js)
    page.wait_for_function("document.querySelector('.connection')?.textContent.includes('Server işləyir')",timeout=10000)
    page.locator(('.mobilebar ' if kind=='mobile' else '.sidebar ')+ '[data-page="matches"]').first.click()
    page.wait_for_function("document.querySelectorAll('.ml-fixture').length===3",timeout=14000)
    self.assertEqual(page.locator('.ml-match-group').count(),2)
    self.assertEqual(page.locator('.ml-day').count(),7)
    self.assertEqual(page.locator('.ml-fixture.is-live').count(),1)
    self.assertEqual(page.locator('.ml-fixture').count(),3)
    self.assertIn('CANLI',page.locator('.ml-fixture.is-live').inner_text())
    # Independent favorite control, list filter, and persistent pinning.
    page.locator('.ml-fixture [data-fav]').first.click()
    self.assertEqual(page.locator('.ml-fixture .ml-fav.is-fav').count(),1)
    page.locator('[data-matchfilter="fav"]').first.click()
    self.assertEqual(page.locator('.ml-fixture').count(),1)
    page.locator('[data-matchfilter="live"]').first.click()
    self.assertEqual(page.locator('.ml-fixture').count(),1)
    page.locator('[data-matchfilter="all"]').first.click()
    # Favourite leagues can be toggled while keeping other UI.
    page.locator('[data-league-pin="ita.1"]').first.click()
    self.assertIn('ita.1',page.evaluate("JSON.parse(localStorage.getItem('matchlab_v08_starredLeagues'))"))
    page.screenshot(path=str(ROOT/f'preview_v0912_{kind}_live.png'),full_page=True)
    # open real match details, tab system and back preserves feed
    page.locator('.ml-fixture [data-match]').first.click()
    page.wait_for_selector('.ml-detail-tabs',timeout=12000)
    self.assertEqual(page.locator('.ml-detail-tab').count(),5)
    page.locator('[data-detail-tab="stats"]').click()
    self.assertGreater(page.locator('.match-stat-row').count(),0)
    page.locator('[data-detail-tab="events"]').click()
    self.assertGreater(page.locator('.match-event').count(),0)
    page.locator('[data-detail-tab="sources"]').click()
    self.assertEqual(page.locator('#source-sofa').count(),1)
    page.locator(('.mobilebar ' if kind=='mobile' else '.sidebar ')+ '[data-page="matches"]').first.click()
    page.wait_for_function("document.querySelectorAll('.ml-fixture').length===3",timeout=14000)
    # Date selection works without UTC shifts and remains visible
    before=page.locator('#date').input_value()
    page.locator('[data-match-date]').nth(4).click()
    page.wait_for_function('(prev)=>document.querySelector("#date")?.value!==prev',arg=before,timeout=15000)
    self.assertNotEqual(before,page.locator('#date').input_value())
    self.assertEqual(errors,[],f'{kind}: {errors}')
    if kind=='mobile':
     dims=page.evaluate('''() => ({doc:document.documentElement.scrollWidth,width:window.innerWidth})''')
     self.assertLessEqual(dims['doc'],dims['width']+2,repr(dims))
    print(f'{kind} live screen, tabs, favourites and date: OK')
    page.close()
   browser.close()
if __name__=='__main__':unittest.main(verbosity=2)
