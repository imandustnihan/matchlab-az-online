"""Regression: restored Wikipedia links never disappear due to empty summaries or v0.9.24 cache."""
import unittest
from unittest.mock import patch
from pathlib import Path
from playwright.sync_api import sync_playwright
import wikipedia_enrichment as wiki
import server

ROOT=Path(__file__).resolve().parent

class WikiLinks25(unittest.TestCase):
    def test_cached_wikidata_language_links_recovered_by_exact_qid(self):
        qid='Q185572'
        old={'wikiKind':'coaches','wikiMatch':True,'careerUrl':'https://en.wikipedia.org/wiki/Mikel_Arteta',
             'clubs':[{'name':'Everton','from':2005,'to':2011}]}
        calls=[]
        def source(url,ttl):
            calls.append(url)
            self.assertIn('ids=Q185572',url)
            self.assertIn('props=sitelinks',url)
            return {'entities':{qid:{'sitelinks':{
                'enwiki':{'title':'Mikel Arteta'},'trwiki':{'title':'Mikel Arteta'},
                'azwiki':{'title':'Mikel Arteta'}}}}}
        with patch.object(wiki,'cached',return_value=old),patch.object(wiki,'store'):
            result=wiki.enrich(qid,source,kind='coaches')
        self.assertIn('az.wikipedia.org',result['wikiPageLinks']['az'])
        self.assertIn('tr.wikipedia.org',result['wikiPageLinks']['tr'])
        self.assertEqual(result['clubs'][0]['name'],'Everton')
        self.assertEqual(len(calls),1)

    def test_offline_cache_preserves_old_article_link(self):
        qid='Q12345678'
        old={'wikiKind':'teams','clubDataVersion':2,'wikiUrl':'https://en.wikipedia.org/wiki/Example_FC','wikiMatch':True}
        with patch.object(wiki,'cached',return_value=old):
            info=wiki.enrich(qid,lambda *_: (_ for _ in ()).throw(ConnectionError('offline')),kind='teams')
        self.assertEqual(info['wikiPageLinks']['en'],old['wikiUrl'])
        self.assertTrue(info['wikiMatch'])

    def test_invalid_and_ambiguous_urls_not_trusted(self):
        data=wiki.restore_cached_article_links('Q185572',
            {'wikiUrl':'https://evil.example/wiki/Fake','careerUrl':'javascript:alert(1)'},
            lambda *_:{'entities':{'Q185572':{'sitelinks':{}}}})
        self.assertFalse(data.get('wikiPageLinks'))

    def test_arteta_profile_still_one_identity(self):
        from identity_unification import qid_of
        result=server.send_data('/api/search',{'q':['Mikel Arteta'],'kind':['all']})['items']
        self.assertEqual(len([x for x in result if qid_of(x)=='Q185572']),1)

    def test_desktop_and_mobile_restored_wikipedia_panel(self):
        js=(ROOT/'app.js').read_text(encoding='utf-8').replace(
            "const BACKEND=()=>['http:','https:'].includes(location.protocol);",'const BACKEND=()=>true;')
        css=(ROOT/'styles.css').read_text(encoding='utf-8')
        examples=[
            {'id':'Q185572','name':'Mikel Arteta','kind':'coaches',
             'wikiUrl':'https://en.wikipedia.org/wiki/Mikel_Arteta','wikidataId':'Q185572',
             'clubs':[{'name':'Everton','from':2005,'to':2011}]},
            {'id':'Q8682','name':'Example FC','kind':'teams',
             'wikiPageLinks':{'az':'https://az.wikipedia.org/wiki/Nümunə','en':'https://en.wikipedia.org/wiki/Example_FC'},
             'wikidataId':'Q8682'},
            {'id':'Q12345','name':'Unlinked Person','kind':'players','wikidataId':'Q12345'}]
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
            for label,width in (('desktop',1360),('mobile',390)):
                page=browser.new_page(viewport={'width':width,'height':850})
                errors=[]
                page.on('pageerror',lambda error:errors.append(str(error)))
                page.set_content('<html><head><meta charset="utf-8"></head><body><div id="app"></div></body></html>')
                page.add_style_tag(content=css)
                page.evaluate('''(profiles)=>{
                  window.ML_CATALOG=profiles;window.ML_FEATURED={};
                  let stored={};Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem:k=>stored[k]??null,setItem:(k,v)=>stored[k]=String(v),removeItem:k=>delete stored[k]}});
                  window.fetch=async input=>{
                    const path=String(input);let result={items:[]};
                    if(path.startsWith('/api/status'))result={ok:true,backend:true,publicHosting:true,world:{total:506207,counts:{players:437525,teams:43031,coaches:24120}}};
                    else if(path.startsWith('/api/profile'))result={profile:profiles.find(p=>path.includes(encodeURIComponent(p.id)))};
                    else if(path.startsWith('/api/search'))result={items:profiles};
                    return {ok:true,status:200,json:async()=>result};
                  };
                }''',examples)
                page.add_script_tag(content=js)
                page.wait_for_function("document.querySelector('.connection')?.textContent.includes('Server işləyir')",timeout=12000)
                page.locator(('.mobilebar ' if label=='mobile' else '.sidebar ')+'[data-page="search"]').first.click()
                for p in examples:
                    page.locator(f'[data-id="{p["id"]}"]').first.click()
                    page.wait_for_function("document.querySelector('#profile-wikipedia') !== null")
                    panel=page.locator('#profile-wikipedia')
                    self.assertIn('Wikipedia və mənbələr',panel.inner_text())
                    self.assertEqual(panel.locator(f'a[href="https://www.wikidata.org/wiki/{p["id"]}"]').count(),1)
                    self.assertEqual(panel.locator('a[href*="w/index.php?search="]').count(),1)
                    if p['id']=='Q185572':
                        self.assertEqual(panel.locator('a[href="https://en.wikipedia.org/wiki/Mikel_Arteta"]').count(),1)
                    if p['id']=='Q8682':
                        self.assertEqual(panel.locator('a[href^="https://az.wikipedia.org/wiki/"]').count(),1)
                    if p['id']=='Q12345':
                        self.assertEqual(panel.locator('a[href*="wikipedia.org/wiki/"]').count(),0)
                        self.assertIn('təsdiqlənməyib',panel.inner_text())
                    page.locator(('.mobilebar ' if label=='mobile' else '.sidebar ')+'[data-page="search"]').first.click()
                self.assertEqual(errors,[],(label,errors))
                page.close()
            browser.close()

if __name__=='__main__':unittest.main(verbosity=2)
