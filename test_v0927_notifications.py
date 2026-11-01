"""MATCHLAB AZ v0.9.27: seven original audio signatures, previews, no visible history."""
import re
import unittest
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parent
SOUND_MOCK=r'''() => {
  window.__soundTrace=[];
  class MockAC {
    constructor(){this.currentTime=0;this.state='running';this.destination={};}
    createOscillator(){
      const item={wave:null,hz:null,glide:null,duration:null};
      window.__soundTrace.push(item);
      return {
        get type(){return item.wave},set type(x){item.wave=x},
        frequency:{setValueAtTime:(x)=>{item.hz=x},exponentialRampToValueAtTime:(x)=>{item.glide=x}},
        connect:()=>{},start:()=>{},stop:(x)=>{item.duration=x},disconnect:()=>{}
      };
    }
    createGain(){return {gain:{setValueAtTime:()=>{},linearRampToValueAtTime:()=>{},exponentialRampToValueAtTime:()=>{}},connect:()=>{},disconnect:()=>{}}}
    resume(){this.state='running';return Promise.resolve()}
  }
  window.AudioContext=MockAC;
  window.ML_CATALOG=[];window.ML_FEATURED={};
  let storage={matchlab_v08_alerts:JSON.stringify([{text:'legacy private history'}])};
  Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem:k=>storage[k]??null,setItem:(k,v)=>storage[k]=String(v),removeItem:k=>delete storage[k]}});
  window.fetch=async p=>({ok:true,status:200,json:async()=>{
   if(String(p).startsWith('/api/status'))return {ok:true,backend:true,publicHosting:true,world:{total:506207},version:'0.9.27'};
   if(String(p).startsWith('/api/world/countries'))return {items:[]};
   return {items:[],available:false};
  }});
}'''

class Notifications27(unittest.TestCase):
    def test_no_notification_history_in_source_and_7_individual_categories(self):
        js=(ROOT/'app.js').read_text('utf8')
        self.assertNotIn('notify-clear',js)
        self.assertNotIn('st.alerts',js)
        self.assertNotIn("save('alerts'",js)
        self.assertIn("localStorage.removeItem(KEY+'alerts')",js)
        self.assertIn('NOTIFY_SOUND_PATTERNS=Object.freeze',js)
        self.assertEqual(len(re.findall(r"\['(?:goal|kickoff|final|red|yellow|sub|var)','",js.split('const NOTIFY_SOUND_LABELS=')[1].split('const NOTIFY_SOUND_PATTERNS=')[0])),7)
        for category in ('goal','kickoff','final','red','yellow','sub','var'):
            self.assertIn(f"m,'{category}')",js) if category in ('goal','kickoff','final') else self.assertIn('m,category)',js)
        self.assertIn("'/coach_tactics.js'",(ROOT/'server.py').read_text('utf8'))

    def test_7_audio_signatures_are_distinct_and_previewable_on_mobile_desktop(self):
        app=(ROOT/'app.js').read_text('utf8').replace("const BACKEND=()=>['http:','https:'].includes(location.protocol);","const BACKEND=()=>true;")
        css=(ROOT/'styles.css').read_text('utf8')
        cats=['goal','kickoff','final','yellow','red','sub','var']
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
            for device,width in [('desktop',1350),('mobile',390)]:
                with self.subTest(device=device):
                    page=browser.new_page(viewport={'width':width,'height':850})
                    errs=[];page.on('pageerror',lambda e:errs.append(str(e)))
                    page.set_content('<!doctype html><html lang="az"><body><div id="app"></div></body></html>')
                    page.add_style_tag(content=css)
                    page.evaluate(SOUND_MOCK)
                    page.add_script_tag(content=app)
                    page.wait_for_function("document.querySelector('.connection')?.textContent.includes('Server işləyir')",timeout=12000)
                    nav='.mobilebar ' if device=='mobile' else '.sidebar '
                    page.locator(nav+'[data-page="settings"]').first.click()
                    self.assertEqual(page.locator('[data-notify-pref]').count(),9)
                    self.assertEqual(page.locator('[data-sound-preview]').count(),7)
                    self.assertEqual(page.locator('.notify-panel details').count(),0)
                    self.assertEqual(page.locator('[data-action="notify-clear"]').count(),0)
                    self.assertNotIn('tarixç',page.locator('.notify-panel').inner_text().lower())
                    self.assertIsNone(page.evaluate("localStorage.getItem('matchlab_v08_alerts')"))
                    sounds={}
                    for k in cats:
                        before=page.evaluate('window.__soundTrace.length')
                        page.locator(f'[data-sound-preview="{k}"]').click()
                        trace=page.evaluate(f'window.__soundTrace.slice({before})')
                        self.assertGreater(len(trace),1,k)
                        self.assertTrue(all(i['hz'] and i['wave'] for i in trace),k)
                        sounds[k]=tuple((i['hz'],i['wave']) for i in trace)
                    self.assertEqual(len(set(sounds.values())),7)
                    self.assertGreater(len(sounds['goal']),len(sounds['yellow']))
                    self.assertLess(max(x[0] for x in sounds['red']),min(x[0] for x in sounds['kickoff']))
                    self.assertEqual(errs,[])
                    page.screenshot(path=str(ROOT/f'preview_v0927_notification_sounds_{device}.png'),full_page=True)
                    page.close()
            browser.close()

if __name__=='__main__':unittest.main()
