"""MATCHLAB AZ v0.9.26: desktop/mobile end-to-end UI interactions against mocked sources."""
import unittest
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parent

JS_BOOT='''() => {
  window.ML_CATALOG=[]; window.ML_FEATURED={};
  const store={};Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem:k=>store[k]??null,setItem:(k,v)=>{store[k]=String(v)},removeItem:k=>delete store[k]}});
  window.__testLiveScore=0;
  window.fetch=async (input)=>{
    const p=String(input);let data={items:[]};
    if(p.startsWith('/api/status'))data={ok:true,backend:true,publicHosting:true,world:{total:506207,counts:{players:437525,teams:43031,coaches:24120}},version:'0.9.27'};
    else if(p.startsWith('/api/standings')){
      if(p.includes('jpn.1'))data={available:true,source:'ESPN (test fixture)',items:[{name:'Tokyo Test',rank:1,played:12,win:8,draw:2,loss:2,gf:28,ga:11,gd:17,points:26,form:'WWDLW',group:'East'}]};
      else data={available:false,source:'Sınaq məlumatı yoxdur',items:[]};
    }
    else if(p.startsWith('/api/live?'))data={available:true,stale:false,source:'Test mocked live',items:[
      {id:'espn:eng.1:123',eventId:'123',league:'eng.1',date:'2026-11-01',state:'live',minute:"44th",
       home:{name:'Arsenal',id:'100',image:''},away:{name:'Chelsea',id:'200',image:''},homeScore:window.__testLiveScore,awayScore:0,source:'ESPN (fixture)'}]};
    else if(p.startsWith('/api/world/countries'))data={items:[]};
    return {ok:true,status:200,json:async()=>data};
  };
}'''

class Browser26(unittest.TestCase):
    def test_coach_studio_and_standings_and_notification_settings(self):
        js=(ROOT/'app.js').read_text(encoding='utf-8').replace("const BACKEND=()=>['http:','https:'].includes(location.protocol);",'const BACKEND=()=>true;')
        css=(ROOT/'styles.css').read_text(encoding='utf-8')
        coach=(ROOT/'coach_tactics.js').read_text(encoding='utf-8')
        with sync_playwright() as pw:
            b=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
            for device,w in (('desktop',1366),('mobile',390)):
                with self.subTest(device=device):
                    page=b.new_page(viewport={'width':w,'height':880},accept_downloads=True)
                    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
                    page.set_content('<html lang="az"><head><meta charset="utf-8"></head><body><div id="app"></div></body></html>')
                    page.add_style_tag(content=css)
                    page.evaluate(JS_BOOT)
                    page.add_script_tag(content=coach)
                    page.add_script_tag(content=js)
                    page.wait_for_function("document.querySelector('.connection')?.textContent.includes('Server işləyir')",timeout=12000)
                    nav=('.mobilebar ' if device=='mobile' else '.sidebar ')
                    page.locator(nav+'[data-page="tactics"]').first.click()
                    self.assertEqual(page.locator('#coach-preset option').count(),6)
                    page.locator('#coach-preset').select_option('guardiola-city-2223')
                    page.locator('[data-tactic="coach-apply"]').click()
                    self.assertEqual(page.locator('#formation').input_value(),'3-2-4-1')
                    self.assertEqual(page.locator('#pitch .player-dot').count(),11)
                    page.locator('#tactic-opponent').check()
                    self.assertEqual(page.locator('#pitch .tactic-rival').count(),11)
                    page.locator('[data-tactic="corner"]').click()
                    self.assertIn('Künc zərbəsi',page.locator('#tactic-notes').input_value())
                    page.locator('[data-tactic="scene-add"]').click()
                    page.locator('[data-tactic="freekick"]').click()
                    page.locator('[data-tactic="scene-add"]').click()
                    self.assertIn('2/2',page.locator('#scene-status').inner_text())
                    page.locator('[data-tactic="scene-play"]').click()
                    page.locator('[data-tactic="scene-stop"]').click()
                    with page.expect_download(timeout=7000) as down:
                        page.locator('[data-tactic="export"]').click()
                    self.assertEqual(down.value.suggested_filename,'MATCHLAB_taktika.json')
                    page.screenshot(path=str(ROOT/f'preview_v0926_tactics_{device}.png'),full_page=True)
                    page.locator(nav+'[data-page="standings"]').first.click()
                    self.assertEqual(page.locator('#standings-league option').count(),68)
                    page.locator('#standings-league').select_option('jpn.1')
                    page.wait_for_function("document.querySelector('.standings-table')?.textContent.includes('Tokyo Test')")
                    self.assertIn('WWDLW',page.locator('.standings-table').inner_text())
                    self.assertIn('28',page.locator('.standings-table').inner_text())
                    page.screenshot(path=str(ROOT/f'preview_v0926_standings_{device}.png'),full_page=True)
                    page.locator('#standings-league').select_option('caf.champions')
                    page.wait_for_function("document.querySelector('.page')?.textContent.includes('təsdiqlənmiş cədvəli mövcud deyil')")
                    page.locator(nav+'[data-page="settings"]').first.click()
                    self.assertEqual(page.locator('[data-notify-pref]').count(),9)
                    self.assertEqual(page.locator('[data-sound-preview]').count(),7)
                    self.assertEqual(page.locator('.notify-panel details').count(),0)
                    page.locator('#notify-scope').select_option('all')
                    page.locator('[data-notify-pref="sound"]').check()
                    self.assertFalse(page.locator('#notify-volume').is_disabled())
                    page.locator('#notify-volume').evaluate('(el)=>{el.value="70";el.dispatchEvent(new Event("change",{bubbles:true}))}')
                    self.assertEqual(page.locator('#notify-volume').input_value(),'70')
                    page.locator('[data-action="notify-test"]').click()
                    self.assertIn('Sınaq qol bildirişi',page.locator('.notify-panel').inner_text())
                    self.assertFalse(page.locator('[data-notify-pref="enabled"]').is_checked())
                    page.locator('[data-notify-pref="enabled"]').check()
                    # Actual score transitions generate exactly one alert and do not repeat.
                    page.locator(nav+'[data-page="matches"]').first.click()
                    page.wait_for_function("document.querySelector('.page')?.textContent.includes('Arsenal')")
                    page.evaluate('window.__testLiveScore=1')
                    page.locator('[data-action="refresh-live"]').first.click()
                    page.wait_for_timeout(350)
                    page.locator('[data-action="refresh-live"]').first.click()
                    page.wait_for_timeout(350)
                    page.locator(nav+'[data-page="settings"]').first.click()
                    self.assertEqual(page.locator('.notify-panel details').count(),0)
                    self.assertNotIn('Bildiriş tarixçəsi',page.locator('.notify-panel').inner_text())
                    self.assertEqual(errors,[],(device,errors))
                    page.screenshot(path=str(ROOT/f'preview_v0926_settings_{device}.png'),full_page=True)
                    page.close()
            b.close()

if __name__=='__main__':unittest.main()
