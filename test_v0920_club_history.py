"""v0.9.20 offline fixture tests: no invented honours, rosters, images or links."""
import unittest
from pathlib import Path
from unittest.mock import patch
import club_history as club
import wikipedia_enrichment as wiki
import server

ROOT=Path(__file__).resolve().parent
WIKI='''{{Infobox football club|fullname=Example Athletic Club|nickname=The Stars|founded=1902|ground=Example Stadium|league=Example League}}
== Honours ==
=== Domestic ===
* [[Example League]]: Winners (12): 2001, 2002.
* [[Example Cup]] (4): 2010, 2011.
* Runners-up (8): 2012.
=== International ===
* [[Continental Cup]]: Champions (3).
== Players ==
=== Current squad ===
{{Fs player|no=1|pos=GK|name=[[Jane Keeper]]}}
{{Fs player|no=9|pos=FW|name=[[Alex Striker]]}}
{{Fs player|no=9|pos=FW|name=[[Alex Striker]]}}
=== Out on loan ===
{{Fs player|no=99|pos=FW|name=[[Loan Person]]}}
== Personnel ==
'''

class ClubHistory20(unittest.TestCase):
    def test_honours_exact_counts_only(self):
        h=club.parse_honours(WIKI)
        self.assertEqual([(x['name'],x['count']) for x in h],[('Example League',12),('Example Cup',4),('Continental Cup',3)])
        self.assertFalse(any('Runners-up' in x['name'] for x in h))

    def test_real_madrid_style_tabular_honours(self):
        table="""== Honours ==
{| class="wikitable sortable"
! Type !! Competition !! Titles !! Seasons
|-
| rowspan="2" | Domestic
| [[La Liga]]
| 36
| 1931–32, 2023–24
|-
| [[Copa del Rey]]
| 20
| 1905, 2022–23
|-
| Continental
| [[European Cup]] / [[UEFA Champions League]]
| 15
| 1955–56
|}
== Players ==
"""
        honours=club.parse_honours(table)
        self.assertEqual(len(honours),3)
        self.assertEqual([x['count'] for x in honours],[36,20,15])
        self.assertEqual(honours[0]['category'],'Domestic')
        self.assertEqual(honours[2]['category'],'Continental')

    def test_honours_unknown_is_not_zero(self):
        h=club.parse_honours('== Honours ==\n* [[Unspecified Trophy]]\n== Players ==')
        self.assertEqual(len(h),1)
        self.assertIsNone(h[0]['count'])
        self.assertEqual(club.parse_honours('== History ==\n* Fictional trophy\n'),[])

    def test_squad_only_from_verified_section_and_not_loans(self):
        squad=club.parse_squad(WIKI)
        self.assertEqual([x['name'] for x in squad],['Jane Keeper','Alex Striker'])
        self.assertEqual(squad[0]['number'],'1')
        self.assertEqual(club.parse_squad('== History ==\n{{Fs player|no=4|name=Name}}'),[])

    def test_stadium_image_requires_p115_license(self):
        stadium={'claims':{'P115':[{'mainsnak':{'datavalue':{'value':{'id':'Q500'}}}}]}}
        def get_json(url,ttl):
            if 'www.wikidata.org' in url:
                entity={'labels':{'en':{'value':'The Stadium'}},'claims':{'P18':[{'mainsnak':{'datavalue':{'value':'Example Stadium.jpg'}}}]}}
                return {'entities':{'Q500':entity}}
            return {'query':{'pages':[{'imageinfo':[{'thumburl':'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a9/x.jpg','descriptionurl':'https://commons.wikimedia.org/wiki/File:Example_Stadium.jpg','extmetadata':{'LicenseShortName':{'value':'CC BY-SA 4.0'},'LicenseUrl':{'value':'https://creativecommons.org/licenses/by-sa/4.0/'}}}]}]}}
        value=club.stadium_media(stadium,get_json)
        self.assertTrue(value['stadiumPhoto'].startswith('https://upload.wikimedia.org/'))
        self.assertEqual(value['stadiumQid'],'Q500')
        self.assertEqual(value['stadiumPhotoLicense'],'CC BY-SA 4.0')

    def test_stadium_nonfree_is_rejected(self):
        stadium={'claims':{'P115':[{'mainsnak':{'datavalue':{'value':{'id':'Q500'}}}}]}}
        def bad(url,ttl):
            if 'www.wikidata.org' in url:
                entity={'claims':{'P18':[{'mainsnak':{'datavalue':{'value':'Example.jpg'}}}]}}
                return {'entities':{'Q500':entity}}
            return {'query':{'pages':[{'imageinfo':[{'thumburl':'https://upload.wikimedia.org/x.jpg','extmetadata':{'NonFree':{'value':'true'},'LicenseShortName':{'value':'CC BY 4.0'},'LicenseUrl':{'value':'https://creativecommons.org/licenses/by/4.0/'}}}]}]}}
        self.assertEqual(club.stadium_media(stadium,bad),{})

    def test_stadium_no_unverified_qid_photo(self):
        self.assertEqual(club.stadium_media({'claims':{}},lambda *_:None),{})

    def test_historical_links_only_curated_and_distinct_kinds(self):
        seed={
          'Q100':{'name':'Former Player','clubs':[{'id':'Q500','name':'Example Athletic Club','from':1990,'to':1999}]},
          'Q200':{'name':'Former Coach','coached':[{'name':'Example Athletic Club','from':2000,'to':2002}]},
          'Q300':{'name':'Other Person','clubs':[{'name':'Other Club','from':2001}]},
          'foo':{'name':'Unverified Person','clubs':[{'name':'Example Athletic Club'}]},
        }
        rel=club.historical_links('Example Athletic Club',seed,'Q500')
        self.assertEqual([x['id'] for x in rel['players']],['Q100'])
        self.assertEqual([x['id'] for x in rel['coaches']],['Q200'])

    def test_remote_verified_page_extracts_honours_roster(self):
        qid='Q8682'
        def get_json(url,ttl):
            if 'wbgetentities' in url and 'ids=Q8682' in url:
                return {'entities':{qid:{'sitelinks':{'enwiki':{'title':'Example Athletic Club'}},'claims':{'P571':[{'mainsnak':{'datavalue':{'value':{'time':'+1902-01-01T00:00:00Z'}}}}]}}}}
            if 'pageprops' in url:return {'query':{'pages':[{'ns':0,'pageprops':{'wikibase_item':qid},'extract':'Example is a club.'}]}}
            if 'rest.php' in url:return {'source':WIKI}
            return {'entities':{},'query':{'pages':[]}}
        info=wiki.remote_enrich(qid,get_json,'teams')
        self.assertEqual(info['honours'][0]['count'],12)
        self.assertEqual(len(info['squadSnapshot']),2)
        self.assertTrue(info['wikiMatch'])
        self.assertEqual(info['clubDataVersion'],2)

    def test_unverified_page_never_supplies_roster(self):
        def get_json(url,ttl):
            if 'wbgetentities' in url:return {'entities':{'Q8682':{'sitelinks':{'enwiki':{'title':'Example Club'}},'claims':{}}}}
            if 'pageprops' in url:return {'query':{'pages':[{'ns':0,'pageprops':{'wikibase_item':'Q999'},'extract':'Wrong club.'}]}}
            raise AssertionError('Wikitext must not be read without QID match')
        info=wiki.remote_enrich('Q8682',get_json,'teams')
        self.assertNotIn('squadSnapshot',info)
        self.assertNotIn('honours',info)
        self.assertFalse(info['wikiMatch'])

    def test_wiki_merging_new_fields(self):
        profile=wiki.with_wikipedia({'id':'Q8682','kind':'teams'}, {'honours':[{'name':'Cup','count':3}],'squadSnapshot':[{'name':'Keeper'}],'stadiumPhoto':'https://upload.wikimedia.org/x.jpg','colorHexes':['#FFFFFF'],'clubDataVersion':2,'wikiMatch':True})
        self.assertEqual(profile['honours'][0]['count'],3)
        self.assertEqual(profile['squadSnapshot'][0]['name'],'Keeper')

    def test_frontend_has_four_sections_and_prefs(self):
        js=(ROOT/'app.js').read_text(encoding='utf-8')
        for name in ('clubHonoursBlock','clubStadiumBlock','clubSquadBlock','clubHistoryBlock','data-club-pref','showClubHonours','showClubStadium','showClubHistory'):
            self.assertIn(name,js)
        self.assertIn('squadChecked',js)
        self.assertIn('stadiumPhotoLicense',js)

    def test_old_arteta_identity_unchanged(self):
        with patch.object(server,'get_json',side_effect=ConnectionError('offline')):
            p=server.send_data('/api/profile',{'id':['p:mikel-arteta']})['profile']
        self.assertEqual(p['wikidataId'],'Q185572')
        self.assertGreaterEqual(len(p.get('coached',[])),2)

if __name__=='__main__':unittest.main()
