"""MediaWiki/Wikidata safe supplemental careers; unified player-manager identities."""
import unittest
from unittest.mock import patch
import identity_unification as ids
import wikipedia_enrichment as wiki
import server

Q='Q987654321'
A='Q10011'
B='Q10012'

def statement(value, qualifiers=None, rank='normal'):
    return {'rank':rank,'mainsnak':{'datavalue':{'value':value}},'qualifiers':qualifiers or {}}

def timequal(year):
    return {'datavalue':{'value':{'time':f'+{year}-01-01T00:00:00Z','precision':9}}}

def input_source(article='{{Infobox person|name=Person Example}}', verified=True, with_teams=True):
    claims={'P54':[
      statement({'id':A},{'P580':[timequal(2003)],'P582':[timequal(2007)]}),
      statement({'id':B},{'P580':[timequal(2008)]}),
      statement({'id':A},{'P580':[timequal(2012)],'P582':[timequal(2014)]},rank='deprecated'),
      statement({'id':'not-QID'}),
    ]} if with_teams else {}
    entity={'sitelinks':{'enwiki':{'title':'Person Example'}},'claims':claims}
    def get_json(url,ttl):
        if 'www.wikidata.org' in url and 'props=labels' in url:
            return {'entities':{A:{'labels':{'en':{'value':'Club A'}}},B:{'labels':{'en':{'value':'Club B'}}}}}
        if 'www.wikidata.org' in url:return {'entities':{Q:entity}}
        if 'prop=pageprops' in url:return {'query':{'pages':[{'ns':0,'pageprops':{'wikibase_item':Q if verified else 'Q555'},'extract':'An article excerpt'}]}}
        if '/w/rest.php/' in url:return {'source':article}
        raise AssertionError(url)
    return get_json

class VerifiedExpandedCareers(unittest.TestCase):
    def test_team_fallback_years_and_no_invented_statistics(self):
        v=wiki.remote_enrich(Q,input_source())
        self.assertEqual([c['name'] for c in v['clubs']],['Club A','Club B'])
        self.assertEqual((v['clubs'][0]['from'],v['clubs'][0]['to']),(2003,2007))
        self.assertEqual(v['clubs'][1]['from'],2008)
        self.assertNotIn('to',v['clubs'][1])
        self.assertNotIn('apps',v['clubs'][0]);self.assertNotIn('goals',v['clubs'][0]);self.assertNotIn('assists',v['clubs'][0])
        self.assertIn('P54',v['careerSource'])
        self.assertEqual(v['statsScope'],'unspecified_membership')
        self.assertIn('komanda',v['statNotice'].casefold())

    def test_wikipedia_infobox_has_priority_over_wikidata_membership(self):
        text='{{Infobox football biography|clubs1=[[A Verified FC]]|years1=2010–2013|caps1=88|goals1=13}}'
        v=wiki.remote_enrich(Q,input_source(article=text))
        self.assertEqual(len(v['clubs']),1)
        self.assertEqual(v['clubs'][0]['apps'],88)
        self.assertIn('Wikipedia',v['careerSource'])

    def test_bad_wikipedia_qid_does_not_leak_infobox(self):
        text='{{Infobox football biography|clubs1=Wrong Club|years1=2010–2013|caps1=999}}'
        v=wiki.remote_enrich(Q,input_source(article=text,verified=False))
        self.assertNotIn('Wrong Club',[c['name'] for c in v['clubs']])
        self.assertIn('Wikidata',v['careerSource'])
        self.assertFalse(v['wikiMatch'])

    def test_no_wikidata_affiliations_no_unsupported_career(self):
        v=wiki.remote_enrich(Q,input_source(with_teams=False))
        self.assertFalse(v.get('clubs'))

    def test_mikel_arteta_appears_once_with_both_careers(self):
        rows=server.send_data('/api/search',{'q':['Mikel Arteta'],'kind':['all']})['items']
        matched=[r for r in rows if ids.qid_of(r)=='Q185572']
        self.assertEqual(len(matched),1)
        self.assertEqual(set(matched[0]['roles']),{'players','coaches'})
        with patch.object(server,'get_json',side_effect=ConnectionError('offline')):
            p=server.send_data('/api/profile',{'id':[matched[0]['id']]})['profile']
        self.assertGreaterEqual(len(p.get('clubs') or []),6)
        self.assertGreaterEqual(len(p.get('coached') or []),2)

    def test_wikidata_qid_without_wikipedia_article_can_show_team_membership(self):
        def only_wikidata(url,ttl):
            if 'props=labels' in url:
                return {'entities':{A:{'labels':{'en':{'value':'Verified United'}}}}}
            if 'www.wikidata.org' in url:
                return {'entities':{Q:{'sitelinks':{},'claims':{'P54':[
                    statement({'id':A},{'P580':[timequal(2011)]})]}}}}
            raise AssertionError('No Wikipedia API call expected')
        v=wiki.remote_enrich(Q,only_wikidata)
        self.assertEqual(v['clubs'][0]['name'],'Verified United')
        self.assertIn('Wikidata',v['careerSource'])
        self.assertFalse(v['wikiMatch'])
        self.assertNotIn('apps',v['clubs'][0])

    def test_no_article_no_team_history_remains_unavailable(self):
        def only_wikidata(url,ttl):return {'entities':{Q:{'sitelinks':{},'claims':{}}}}
        self.assertIsNone(wiki.remote_enrich(Q,only_wikidata))

    def test_homonyms_with_different_qids_must_remain_distinct(self):
        r=ids.unify([{'id':'p1','name':'A Test','kind':'players','qid':'Q111'},
                     {'id':'c1','name':'A Test','kind':'coaches','qid':'Q222'}])
        self.assertEqual(len(r),2)

if __name__=='__main__':unittest.main()
