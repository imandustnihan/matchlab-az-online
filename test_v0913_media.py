"""v0.9.13 tests: photograph identity binding, batched search images and cache safety.
Mocks are deterministic; a remote Wikimedia download is NOT asserted.
"""
import base64
import unittest
from pathlib import Path
from unittest.mock import patch
from playwright.sync_api import sync_playwright
import server

ROOT=Path(__file__).resolve().parent

class MediaTests(unittest.TestCase):
    def test_crest_is_not_portrait(self):
        def val(name):
            return {'rank':'normal','mainsnak':{'snaktype':'value','datavalue':{'value':name}}}
        club={'claims':{'P154':[val('Crest.svg')],'P18':[val('Stadium.jpg')]}}
        with patch.object(server,'wd_entities',return_value={'Q300':club}):
            crest=server.media_by_qid('Q300','teams',retry=True)
            self.assertIn('Crest.svg',crest['url'])
            self.assertNotIn('Stadium',crest['url'])
            portrait=server.media_by_qid('Q300','players',retry=True)
            self.assertEqual(portrait['url'],'')  # Club QID must never render as a person.
            self.assertIn('uyğun deyil',portrait['source'])

    def test_wrong_kind_not_returned(self):
        result=server.send_data('/api/photo',{'qid':['Q12345'],'kind':['not-a-kind']})
        self.assertEqual(result['url'],'')

    def test_all_visible_ids_are_batched_without_false_misses(self):
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
            page=browser.new_page()
            page.set_content('<html><head><meta charset="utf-8"></head><body><div id="app"></div></body></html>')
            page.add_style_tag(content=(ROOT/'styles.css').read_text())
            page.evaluate('''() => {
                const store={};Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem:k=>store[k]??null,setItem:(k,v)=>{store[k]=String(v)},removeItem:k=>{delete store[k]}}});
                window.ML_CATALOG=[];window.ML_FEATURED={};
                window.mediaCalls=[];
                window.fakePlayers=Array.from({length:65},(_,i)=>({id:'rp'+String(i).padStart(12,'0'),qid:'Q'+(50000+i),kind:'players',name:'Futbolcu '+i}));
                window.fetch=async function(input){const path=String(input),params=new URL('http://local'+path).searchParams;
                  let data={items:[]};
                  if(path.startsWith('/api/status'))data={ok:true,backend:true,world:{total:506207,counts:{players:437525,teams:43031,coaches:24120}}};
                  else if(path.startsWith('/api/search'))data={worldInstalled:true,items:window.fakePlayers,nextOffset:null};
                  else if(path.startsWith('/api/photos')){
                    const ids=params.get('qids').split(',');window.mediaCalls.push(ids);
                    data={items:Object.fromEntries(ids.map(id=>[id,'https://commons.wikimedia.org/wiki/Special:FilePath/'+id+'.png?width=240']))};
                  } else if(path.startsWith('/api/live'))data={items:[],available:false};
                  return {ok:true,status:200,json:async()=>data};
                };
            }''')
            js=(ROOT/'app.js').read_text().replace("const BACKEND=()=>['http:','https:'].includes(location.protocol);",'const BACKEND=()=>true;')
            page.add_script_tag(content=js)
            page.wait_for_function("document.querySelector('.connection')?.textContent.includes('Server işləyir')",timeout=12000)
            page.locator('.sidebar [data-page="search"]').click()
            page.wait_for_function('window.mediaCalls.flat().length>=65',timeout=12000)
            calls=page.evaluate('window.mediaCalls')
            all_ids=[id for batch in calls for id in batch]
            self.assertEqual(len(all_ids),65)
            self.assertEqual(len(set(all_ids)),65)
            self.assertEqual([len(batch) for batch in calls],[20,20,20,5])
            self.assertEqual(page.locator('.entity').count(),65)
            self.assertEqual(page.evaluate("Object.keys(JSON.parse(localStorage.getItem('matchlab_v08_photoCache')||'{}')).length"),65)
            browser.close()

if __name__=='__main__':unittest.main(verbosity=2)
