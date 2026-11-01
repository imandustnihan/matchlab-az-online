"""v0.9.18: conservative QID unification, documented careers, tactics visuals."""
import json
import re
import unittest
from pathlib import Path
from unittest.mock import patch
import identity_unification as people
import server
import wikipedia_enrichment as wiki

ROOT=Path(__file__).resolve().parent

class IdentityCareer18(unittest.TestCase):
    def test_arteta_legacy_aliases_have_verified_qid(self):
        self.assertEqual(people.qid_of({'id':'p:mikel-arteta','kind':'players'}),'Q185572')
        self.assertEqual(people.qid_of({'id':'c:mikel-arteta','kind':'coaches'}),'Q185572')

    def test_arteta_search_one_person(self):
        result=server.send_data('/api/search',{'q':['Mikel Arteta'],'kind':['all']})
        matching=[x for x in result['items'] if people.qid_of(x)=='Q185572']
        self.assertEqual(len(matching),1,matching)
        self.assertEqual(set(matching[0]['roles']),{'players','coaches'})
        self.assertTrue(matching[0]['id'].startswith('rc'))

    def test_arteta_both_filters_stay_available(self):
        for role in ('players','coaches'):
            result=server.send_data('/api/search',{'q':['Mikel Arteta'],'kind':[role]})
            matching=[x for x in result['items'] if people.qid_of(x)=='Q185572']
            self.assertEqual(len(matching),1,(role,matching))

    def test_same_name_different_qids_never_merge(self):
        rows=[{'id':'rpfoo111111','name':'A. Example','kind':'players','qid':'Q123'},
              {'id':'rcbar111111','name':'A. Example','kind':'coaches','qid':'Q456'}]
        self.assertEqual(len(people.unify(rows)),2)

    def test_same_qid_across_player_and_coach_merges(self):
        rows=[{'id':'rpabc123456','name':'Ex','kind':'players','qid':'Q123'},
              {'id':'rcdef123456','name':'Ex','kind':'coaches','qid':'Q123'}]
        result=people.unify(rows)
        self.assertEqual(len(result),1)
        self.assertEqual(set(result[0]['roles']),{'players','coaches'})

    def test_names_without_qids_never_merge(self):
        rows=[{'id':'rpabc123456','name':'A Same','kind':'players','qid':''},
              {'id':'rcdef123456','name':'A Same','kind':'coaches','qid':''}]
        self.assertEqual(len(people.unify(rows)),2)

    def test_arteta_legacy_profile_resolves_to_one_registry_person(self):
        for identifier in ('p:mikel-arteta','c:mikel-arteta','rc47c64951da111e'):
            with patch.object(server,'get_json',side_effect=ConnectionError('offline')):
                p=server.send_data('/api/profile',{'id':[identifier]})['profile']
            self.assertEqual(p['wikidataId'],'Q185572')
            self.assertEqual(p['id'],'rc47c64951da111e')
            self.assertIn('coaches',p['roles'])
            self.assertIn('players',p['roles'])
            self.assertEqual(p['otherRoles'],[])
            self.assertGreaterEqual(len(p['clubs']),6)
            self.assertGreaterEqual(len(p['coached']),2)
            self.assertTrue(p.get('careerUrl','').startswith('https://en.wikipedia.org/'))

    def test_wikipedia_11_language_fallback(self):
        self.assertEqual(wiki.wiki_title({'sitelinks':{'plwiki':{'title':'Pilkarz Test'}}}),('pl','Pilkarz Test'))
        self.assertIn('es',wiki.verified_language_links({'sitelinks':{'eswiki':{'title':'Jugador'}}}))

    def test_wikipedia_assists_only_when_explicit(self):
        markup='{{Infobox football biography|years1=2010–2012|clubs1=Sample FC|caps1=35|goals1=7|assists1=4|years2=2012–2014|clubs2=Other FC|caps2=55|goals2=8}}'
        p=wiki.parse_football_infobox(markup)
        self.assertEqual(p['clubs'][0]['assists'],4)
        self.assertIsNone(p['clubs'][1]['assists'])

    def test_tactics_field_not_styled_as_top_navigation(self):
        src=(ROOT/'app.js').read_text()
        css=(ROOT/'styles.css').read_text()
        self.assertIn('class="area pitch-north"',src)
        self.assertIn('class="goal pitch-north"',src)
        self.assertNotIn('class="area top"',src)
        self.assertIn('.pitch .area.pitch-north',css)
        self.assertIn('background:transparent',css)

    def test_tactics_photo_from_coach_who_used_to_play(self):
        src=(ROOT/'app.js').read_text()
        self.assertIn("source.kind!=='players'&&!(source.roles||[]).includes('players')",src)

    def test_assist_absent_marked_unknown_in_ui(self):
        src=(ROOT/'app.js').read_text()
        self.assertIn("assists??'Məlumat yoxdur'",src)

if __name__=='__main__':unittest.main()
