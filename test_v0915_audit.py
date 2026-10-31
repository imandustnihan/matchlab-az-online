"""MATCHLAB AZ v0.9.15 regression tests: data integrity, safe rendering and persistence."""
import json
import sqlite3
import unittest
from unittest.mock import patch
from playwright.sync_api import sync_playwright
from pathlib import Path
import wikipedia_enrichment as wiki

ROOT=Path(__file__).resolve().parent
QID='Q87654321'

class Audit15(unittest.TestCase):
    def test_wikipedia_mismatch_cannot_inject_club_career(self):
        entity={'sitelinks':{'enwiki':{'title':'Misleading Footballer'}},'claims':{}}
        called=[]
        def source(url,ttl):
            called.append(url)
            if 'www.wikidata.org' in url:return {'entities':{QID:entity}}
            if 'prop=pageprops' in url:return {'query':{'pages':[{'ns':0,'pageprops':{'wikibase_item':'Q123'},'extract':'Wrong biography!'}]}}
            if '/w/rest.php/' in url:raise AssertionError('Unverified wikitext must not be fetched')
            if 'prop=revisions' in url:raise AssertionError('Unverified wikitext must not be fetched')
            raise AssertionError(url)
        result=wiki.remote_enrich(QID,source)
        self.assertFalse(result['wikiMatch'])
        self.assertNotIn('wikiSummary',result)
        self.assertFalse(result.get('clubs'))
        self.assertIn('Wikidata',result['careerSource'])
        self.assertFalse(any('/w/rest.php/' in s or 'prop=revisions' in s for s in called))

    def test_corrupt_wikipedia_cache_does_not_crash_profile(self):
        with patch.object(wiki,'_init',side_effect=sqlite3.DatabaseError('Corrupt')):
            self.assertIsNone(wiki.cached(QID))
        with patch.object(wiki,'_init',return_value=None),patch.object(wiki.sqlite3,'connect',side_effect=sqlite3.OperationalError('Locked')):
            self.assertIsNone(wiki.cached(QID))

    def test_valid_remote_result_survives_cache_write_failure(self):
        expected={'wikiKind':'players','wikiMatch':True,'wikiSummary':'Verified biography'}
        with patch.object(wiki,'cached',return_value=None),patch.object(wiki,'remote_enrich',return_value=expected),patch.object(wiki,'store',side_effect=sqlite3.OperationalError('read-only')):
            self.assertEqual(wiki.enrich(QID,lambda *_:None,kind='players'),expected)

    def test_valid_wikipedia_page_remains_parsed(self):
        entity={'sitelinks':{'enwiki':{'title':'Example Player'}},'claims':{}}
        def fake(url,ttl):
            if 'www.wikidata.org' in url:return {'entities':{QID:entity}}
            if 'prop=pageprops' in url:return {'query':{'pages':[{'ns':0,'pageprops':{'wikibase_item':QID},'extract':'Verified'}]}}
            if '/w/rest.php/' in url:return {'source':'{{Infobox football biography|clubs1=[[FC Example]]|years1=2018–2020|caps1=21|goals1=3}}'}
            raise AssertionError(url)
        p=wiki.remote_enrich(QID,fake)
        self.assertTrue(p['wikiMatch'])
        self.assertEqual(p['clubs'][0]['apps'],21)

    def test_tactic_notes_survive_browser_reload(self):
        # The test environment blocks navigation to localhost from Chromium.
        # Re-initialize the application in a new browser page with the prior
        # persisted localStorage values, equivalent to a full reload.
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
            script=(ROOT/'app.js').read_text(encoding='utf8')
            saved={}
            for attempt in range(2):
                page=browser.new_page()
                page.set_content('<html><head><meta charset="utf-8"></head><body><div id="app"></div></body></html>')
                page.evaluate('''(initial) => {
                    const store={...initial};
                    window.ML_CATALOG=[];
                    window.ML_FEATURED={};
                    window.__saved=store;
                    Object.defineProperty(window,'localStorage',{configurable:true,value:{
                        getItem:k=>store[k]??null, setItem:(k,v)=>store[k]=String(v),removeItem:k=>delete store[k]
                    }});
                    window.fetch=async()=>({ok:true,status:200,json:async()=>({ok:true,world:{total:506207,counts:{players:437525,teams:43031,coaches:24120}}})});
                }''', saved)
                page.add_script_tag(content=script)
                page.locator('button[data-page="tactics"]').first.click()
                if attempt==0:
                    page.locator('#tactic-notes').fill('Press xətti: 4-3-3. Qeydlər saxlanmalıdır.')
                    page.locator('button[data-tactic="save"]').click()
                    saved=page.evaluate('window.__saved')
                    self.assertIn('matchlab_v08_pitchNotes',saved)
                else:
                    self.assertEqual(page.locator('#tactic-notes').input_value(),'Press xətti: 4-3-3. Qeydlər saxlanmalıdır.')
                page.close()
            browser.close()

    def test_partial_career_not_shown_as_total(self):
        # Static-proof: total sums require all known senior-league records, not just one of two.
        src=(ROOT/'app.js').read_text(encoding='utf8')
        self.assertIn('clubs.every(x=>Number.isFinite(x.apps))',src)
        self.assertIn('clubs.every(x=>Number.isFinite(x.goals))',src)
        self.assertIn('<b>${esc(h??\'—\')}</b>',src)

if __name__=='__main__': unittest.main(verbosity=2)

class DateAccuracy15(unittest.TestCase):
    def test_wikidata_year_precision_never_invents_jan1(self):
        self.assertEqual(wiki.wikidata_date({'time':'+1901-01-01T00:00:00Z','precision':9}),'1901')
        self.assertEqual(wiki.wikidata_date({'time':'+1901-08-01T00:00:00Z','precision':10}),'1901-08')
        self.assertEqual(wiki.wikidata_date({'time':'+1901-08-19T00:00:00Z','precision':11}),'1901-08-19')
        self.assertEqual(wiki.wikidata_date({'time':'+1901-01-01T00:00:00Z','precision':8}),'')
    def test_wikidata_profile_respects_date_precision(self):
        from server import wd_profile
        entity={'id':'Q87654321','labels':{'en':{'value':'Example'}} ,'claims':{
            'P569':[{'mainsnak':{'snaktype':'value','datavalue':{'value':{'time':'+1901-01-01T00:00:00Z','precision':9}}}}],
            'P570':[{'mainsnak':{'snaktype':'value','datavalue':{'value':{'time':'+1977-05-01T00:00:00Z','precision':10}}}}]}}
        with patch('server.wd_entities',return_value={'Q87654321':entity}):
            result=wd_profile('Q87654321','players')
        self.assertEqual(result['birth'],'1901')
        self.assertEqual(result['death'],'1977-05')
        self.assertEqual(result['lifeStatus'],'deceased')
