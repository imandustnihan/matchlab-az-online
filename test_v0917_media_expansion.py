"""v0.9.17: identity-safe, free-licensed, multilingual portrait/crest fallback tests."""
import json
import tempfile
import unittest
import urllib.parse
from pathlib import Path
from unittest.mock import patch
import media_expansion as media
import server

BASE='https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/'

def fake_upstream(qid2title, pictures, fail=None):
    calls=[]
    def handler(url,ttl=0):
        calls.append(url)
        parts=urllib.parse.urlsplit(url)
        qs=urllib.parse.parse_qs(parts.query)
        if parts.hostname=='www.wikidata.org':
            return {'entities':{qid:{'sitelinks':{'enwiki':{'title':title},'trwiki':{'title':'TR '+title}}} for qid,title in qid2title.items()}}
        if fail and parts.hostname==fail:raise ConnectionError('upstream unavailable')
        titles=qs.get('titles',[''])[0].split('|')
        pages=[]
        for title in titles:
            pic=pictures.get((parts.hostname,title))
            if pic:
                page_qid=pic.get('qid')
                pages.append({'ns':0,'title':title,'pageprops':{'wikibase_item':page_qid},
                              'pageimage':pic.get('filename',''),
                              'thumbnail':{'source':pic.get('url',BASE+'Test.jpg')}})
        return {'query':{'pages':pages}}
    return handler,calls

class VerifiedMedia17(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.patch=patch.object(media,'CACHE_FILE',Path(self.tmp.name)/'media.sqlite')
        self.patch.start()
    def tearDown(self):
        self.patch.stop();self.tmp.cleanup()

    def test_two_verified_players_from_one_wikimedia_batch(self):
        titles={'Q10':'Player One','Q11':'Player Two'}
        imgs={('en.wikipedia.org','Player One'):{'qid':'Q10','filename':'Player-one.jpg'},
              ('en.wikipedia.org','Player Two'):{'qid':'Q11','filename':'Player-two.jpg'}}
        fake,calls=fake_upstream(titles,imgs)
        found,complete=media.verified_page_images(['Q10','Q11'],'players',fake)
        self.assertTrue(complete)
        self.assertEqual(set(found),{'Q10','Q11'})
        self.assertEqual(len(calls),2) # one Wikidata request + one batched enwiki request
        self.assertEqual(found['Q10']['verifiedQid'],'Q10')
        self.assertEqual(found['Q11']['wikiLanguage'],'en')
        self.assertIn('pilicense=free',calls[-1])
        self.assertEqual(len([x for x in found.values() if x['url']]),2)

    def test_wrong_person_not_accepted_even_if_title_matches(self):
        fake,_=fake_upstream({'Q10':'Namesake'},{('en.wikipedia.org','Namesake'):{'qid':'Q999','filename':'Other.jpg'}})
        found,complete=media.verified_page_images(['Q10'],'players',fake)
        self.assertTrue(complete)
        self.assertEqual(found,{})

    def test_club_accepts_logo_and_rejects_stadium(self):
        fake,_=fake_upstream({'Q20':'Club One','Q21':'Club Two'},{
            ('en.wikipedia.org','Club One'):{'qid':'Q20','filename':'FC_Club_One_logo.svg'},
            ('en.wikipedia.org','Club Two'):{'qid':'Q21','filename':'Club_Two_Stadium.jpg'}})
        found,complete=media.verified_page_images(['Q20','Q21'],'teams',fake)
        self.assertTrue(complete)
        self.assertEqual(set(found),{'Q20'})
        self.assertEqual(found['Q20']['mediaType'],'crest')

    def test_player_shirt_photo_not_considered_portrait(self):
        fake,_=fake_upstream({'Q45':'Player Five'},{('en.wikipedia.org','Player Five'):{'qid':'Q45','filename':'Player_Five_jersey.png'}})
        found,complete=media.verified_page_images(['Q45'],'players',fake)
        self.assertTrue(complete)
        self.assertEqual(found,{})

    def test_wrong_host_never_allowed(self):
        fake,_=fake_upstream({'Q30':'Player Three'},{('en.wikipedia.org','Player Three'):{'qid':'Q30','filename':'Portrait.jpg','url':'https://example.com/unsafe.jpg'}})
        found,_=media.verified_page_images(['Q30'],'players',fake)
        self.assertEqual(found,{})

    def test_network_error_not_negative_cached(self):
        fake,calls=fake_upstream({'Q40':'Player Four'},{},fail='en.wikipedia.org')
        found,complete=media.verified_page_images(['Q40'],'players',fake)
        self.assertFalse(complete)
        self.assertEqual(found,{})
        self.assertIsNone(media.cache_load('Q40','players'))

    def test_found_media_persisted_and_cache_avoids_remote(self):
        fake,_=fake_upstream({'Q10':'Player One'},{('en.wikipedia.org','Player One'):{'qid':'Q10','filename':'One.jpg'}})
        first,_=media.verified_page_images(['Q10'],'players',fake)
        def no_web(*args):raise AssertionError('cache should avoid new internet requests')
        second,complete=media.verified_page_images(['Q10'],'players',no_web)
        self.assertTrue(complete)
        self.assertEqual(first,second)
        self.assertEqual(media.cache_stats()['players']['found'],1)

    def test_server_batch_adds_confirmed_fallback_and_credits(self):
        fallback={'Q77':{'url':BASE+'Picture.jpg','source':'Wikipedia (en) · sərbəst pageimage','verifiedQid':'Q77','imagePage':'https://commons.wikimedia.org/wiki/File:Picture.jpg'}}
        with patch.object(server,'wd_entities',return_value={'Q77':{'claims':{}}}),patch.object(server.extra_media,'verified_page_images',return_value=(fallback,True)):
            res=server.send_data('/api/photos',{'qids':['Q77'],'kind':['players']})
        self.assertEqual(res['found'],1)
        self.assertEqual(res['items']['Q77'],BASE+'Picture.jpg')
        self.assertIn('imagePage',res['details']['Q77'])
        self.assertTrue(res['complete'])

    def test_single_profile_media_fallback(self):
        fallback={'Q77':{'url':BASE+'Picture.jpg','verifiedQid':'Q77','source':'Wikipedia en'}}
        with patch.object(server,'wd_entities',return_value={'Q77':{'claims':{}}}),patch.object(server.extra_media,'verified_page_images',return_value=(fallback,True)):
            res=server.send_data('/api/photo',{'qid':['Q77'],'kind':['players']})
        self.assertEqual(res['url'],fallback['Q77']['url'])

    def test_batch_does_not_mark_media_missing_when_fallback_offline(self):
        with patch.object(server,'wd_entities',return_value={'Q77':{'claims':{}}}),patch.object(server.extra_media,'verified_page_images',return_value=({},False)):
            res=server.send_data('/api/photos',{'qids':['Q77'],'kind':['players']})
        self.assertFalse(res['complete'])
        self.assertEqual(res['found'],0)

    def test_wikipedia_profile_requests_free_images(self):
        from wikipedia_enrichment import article_details
        def fake(url,ttl):
            self.assertIn('pilicense=free',url)
            return {'query':{'pages':[{'ns':0,'title':'Test','pageprops':{'wikibase_item':'Q999'},'thumbnail':{'source':BASE+'Free.jpg'}}]}}
        self.assertEqual(article_details('en','Test','Q999',fake)['wikiThumbnail'],BASE+'Free.jpg')

    def test_crest_regex_does_not_accept_team_jersey(self):
        self.assertTrue(media.crest_like('Real_Madrid_logo.svg'))
        self.assertFalse(media.crest_like('Real_Madrid_stadium.jpg'))
        self.assertFalse(media.crest_like('Real_Madrid_jersey.png'))

    def test_endpoint_status_includes_media_cache_metadata(self):
        self.assertIn('cached',server.send_data('/api/media-status',{}))
        self.assertEqual(server.send_data('/api/status',{})['version'],'0.9.26-local')

if __name__=='__main__':unittest.main(verbosity=2)
