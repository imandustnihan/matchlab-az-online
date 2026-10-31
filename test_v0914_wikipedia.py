"""No network calls. Test Wikipedia/Wikidata identity verification and profile enrichment."""
import unittest
from unittest.mock import patch
import wikipedia_enrichment as wiki
import server

CLUB_QID='Q12345678'
PLAYER_QID='Q87654321'

def claim(value):
    return {'rank':'normal','mainsnak':{'datavalue':{'value':value}}}

class Wiki14Tests(unittest.TestCase):
    def test_club_infobox(self):
        box='''{{Infobox football club
| clubname = FC Example
| founded = {{Start date and age|1907|2|16}}
| ground = [[Example Stadium]]
| capacity = 45,000
| city = Example City
| manager = [[Example Manager]]
| league = [[Premier League]]
| nickname = The Blues
}}'''
        r=wiki.parse_club_infobox(box)
        self.assertEqual(r['foundedYear'],1907)
        self.assertEqual(r['stadium'],'Example Stadium')
        self.assertEqual(r['stadiumCapacity'],45000)
        self.assertEqual(r['manager'],'Example Manager')
        self.assertEqual(r['league'],'Premier League')
        self.assertEqual(r['nickname'],'The Blues')

    def test_identity_mismatch_rejects_summary(self):
        fake={'query':{'pages':[{'ns':0,'pageprops':{'wikibase_item':'Q42'},'extract':'Wrong person!'}]}}
        r=wiki.article_details('en','Example',PLAYER_QID,lambda *_:fake)
        self.assertFalse(r)

    def test_disambiguation_rejected(self):
        fake={'query':{'pages':[{'ns':0,'pageprops':{'wikibase_item':PLAYER_QID,'disambiguation':''},'extract':'Not verified!'}]}}
        self.assertFalse(wiki.article_details('en','Example',PLAYER_QID,lambda *_:fake))

    def test_club_verified_summary_and_crest(self):
        entity={'sitelinks':{'enwiki':{'title':'FC Example'},'azwiki':{'title':'FK Nümunə'}},
                'claims':{'P154':[claim('Example crest.svg')],'P18':[claim('Stadium.jpg')],
                          'P571':[claim({'time':'+1907-02-16T00:00:00Z'})]}}
        box='{{Infobox football club|founded = 1907|ground = Example Stadium|capacity = 40,000}}'
        def fake(url,ttl):
            if 'www.wikidata.org' in url:return {'entities':{CLUB_QID:entity}}
            if '/w/rest.php/' in url:return {'source':box}
            if 'prop=pageprops' in url:return {'query':{'pages':[{'ns':0,'pageprops':{'wikibase_item':CLUB_QID},'extract':'A historic football club in Example City.','thumbnail':{'source':'https://upload.wikimedia.org/stadium.jpg'}}]}}
            raise AssertionError(url)
        profile=wiki.with_wikipedia({'id':'club1','kind':'teams','name':'Example','image':'','country':'Example'},wiki.remote_enrich(CLUB_QID,fake,kind='teams'))
        self.assertEqual(profile['foundedYear'],1907)
        self.assertEqual(profile['stadium'],'Example Stadium')
        self.assertEqual(profile['wikiSummary'],'A historic football club in Example City.')
        self.assertIn('Example%20crest.svg',profile['image'])
        self.assertNotIn('Stadium.jpg',profile['image'])
        self.assertIn('az.wikipedia.org',profile['wikiPageLinks']['az'])
        self.assertNotIn('death',profile)

    def test_player_date_and_image_with_source(self):
        entity={'sitelinks':{'enwiki':{'title':'Player Example'}},'claims':{'P18':[claim('Player.jpg')],
                'P569':[claim({'time':'+1985-04-02T00:00:00Z'})],
                'P570':[claim({'time':'+2020-01-03T00:00:00Z'})]}}
        box='{{Infobox football biography|clubs1=[[FC Example]]|years1=2003–2007|caps1=10|goals1=2}}'
        def fake(url,ttl):
            if 'www.wikidata.org' in url:return {'entities':{PLAYER_QID:entity}}
            if '/w/rest.php/' in url:return {'source':box}
            if 'prop=pageprops' in url:return {'query':{'pages':[{'ns':0,'pageprops':{'wikibase_item':PLAYER_QID},'extract':'A well-known player.'}]}}
            raise AssertionError(url)
        p=wiki.with_wikipedia({'id':'person','kind':'players'},wiki.remote_enrich(PLAYER_QID,fake))
        self.assertEqual(p['birth'],'1985-04-02');self.assertEqual(p['death'],'2020-01-03')
        self.assertEqual(p['lifeStatus'],'deceased');self.assertEqual(p['clubs'][0]['apps'],10)
        self.assertEqual(p['clubs'][0]['goals'],2)
        self.assertEqual(p['wikiSummary'],'A well-known player.')

    def test_server_club_enrichment_and_seed_not_skipped(self):
        club={'id':'re-club','kind':'teams','name':'FC Example','wikidataId':CLUB_QID}
        enriched={'wikiSummary':'Verified club','stadium':'Example Stadium','wikiKind':'teams'}
        with patch.object(server.world_db,'profile',return_value=club),patch.object(server,'wd_profile',return_value={}),patch.object(wiki,'enrich',return_value=enriched) as mock_enrich:
            result=server.send_data('/api/profile',{'id':['re-club']})
        self.assertEqual(result['profile']['stadium'],'Example Stadium')
        mock_enrich.assert_called_once()
        self.assertEqual(mock_enrich.call_args.kwargs['kind'],'teams')

    def test_still_no_all_wikipedia_bulk_import(self):
        self.assertNotIn('wikipedia-dump',str(server.send_data('/api/status',{})))

if __name__=='__main__':unittest.main(verbosity=2)
