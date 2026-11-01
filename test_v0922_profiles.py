"""Regression coverage for verified legacy profile routing and Wikipedia snapshots."""
import unittest
from unittest.mock import patch
from pathlib import Path
import identity_unification as identities
import wikipedia_enrichment as wiki
import world_db
import server

ROOT=Path(__file__).resolve().parent

class Profile22(unittest.TestCase):
    def test_pep_both_aliases_one_qid(self):
        for old_id in ('p:pep-guardiola','c:pep-guardiola'):
            self.assertEqual(identities.qid_of({'id':old_id}), 'Q164038')

    def test_pep_all_profile_links_resolve_with_no_network(self):
        for old_id in ('p:pep-guardiola','c:pep-guardiola','rc957d61d7a00baf','Q164038'):
            with self.subTest(old_id=old_id):
                with patch.object(server, 'get_json',side_effect=ConnectionError('offline')):
                    p=server.send_data('/api/profile',{'id':[old_id]})['profile']
                self.assertEqual(p['qid'],'Q164038')
                self.assertEqual(p['birth'],'1971-01-18')
                self.assertEqual(p['fullName'],'Josep Guardiola Sala')
                self.assertEqual(p['birthPlace'],'Santpedor, Kataloniya, İspaniya')
                self.assertIn('yarımmüdafiəçi',p['position'])
                self.assertEqual(set(p['roles']),{'players','coaches'})
                self.assertEqual(len(p['clubs']),8)
                self.assertEqual(len(p['coached']),4)
                self.assertEqual(len(p['nationalTeams']),4)
                self.assertGreater(len(p['awards']),0)
                self.assertTrue(p['image'].startswith('https://commons.wikimedia.org/wiki/Special:FilePath/'))

    def test_pep_search_has_single_person(self):
        for kind in ('all','players','coaches'):
            items=server.send_data('/api/search',{'q':['Pep Guardiola'],'kind':[kind]})['items']
            qid_items=[p for p in items if identities.qid_of(p)=='Q164038']
            self.assertEqual(len(qid_items),1,(kind,items))
            self.assertEqual(set(qid_items[0]['roles']),{'players','coaches'})

    def test_only_unambiguous_same_country_links(self):
        self.assertEqual(world_db.unique_verified_identity('Pep Guardiola','Spain'),'Q164038')
        self.assertIsNone(world_db.unique_verified_identity('Pep Guardiola','Brazil'))
        self.assertIsNone(world_db.unique_verified_identity('Nonexistent Name','Spain'))

    def test_cache_missing_career_sections_can_use_verified_seed(self):
        seed=wiki.SEED['Q164038']
        with patch.object(wiki,'cached',return_value={'wikiKind':'coaches','wikiMatch':True,'coached':[{'name':'Barcelona','from':2008,'to':2012}]}):
            result=wiki.enrich('Q164038',lambda *_:None,kind='coaches')
        self.assertEqual(result['birth'],seed['birth'])
        self.assertEqual(len(result['clubs']),8)
        self.assertEqual(len(result['coached']),1) # live verified coaching rows take priority

    def test_infobox_extended_bio_fields(self):
        sample='{{Infobox football biography|fullname=Josep Guardiola Sala|birthplace=[[Santpedor]]|height=1.80 m|position=Defensive midfielder|years1=1990–2001|clubs1=Barcelona|caps1=263|goals1=6}}'
        p=wiki.parse_football_infobox(sample)
        self.assertEqual(p['fullName'],'Josep Guardiola Sala')
        self.assertEqual(p['birthPlace'],'Santpedor')
        self.assertEqual(p['height'],'1.80 m')
        self.assertEqual(p['clubs'][0]['apps'],263)

    def test_profile_ui_displays_club_and_national_history(self):
        src=(ROOT/'app.js').read_text()
        for s in ('Milli komanda karyerası','Doğum yeri','Tam adı','Boy','Məşqçi portreti','Əlavə təsdiq'):
            self.assertIn(s,src)

if __name__=='__main__':unittest.main()
