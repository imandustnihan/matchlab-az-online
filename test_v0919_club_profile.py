import unittest
from pathlib import Path
import wikipedia_enrichment as wiki

ROOT=Path(__file__).resolve().parent

class ClubProfile19(unittest.TestCase):
    def test_club_infobox_parses_multiple_nicknames(self):
        markup='{{Infobox football club|fullname=Real Example Club|founded=1902|ground=Bernabéu|capacity=83,186|nickname={{hlist|Los Blancos|Los Merengues|Madridistas}}|league=La Liga|manager=Carlo Example}}'
        data=wiki.parse_club_infobox(markup)
        self.assertEqual(data['fullName'],'Real Example Club')
        self.assertEqual(data['foundedYear'],1902)
        self.assertEqual(data['stadium'],'Bernabéu')
        self.assertEqual(data['stadiumCapacity'],83186)
        self.assertEqual(data['nicknames'][:3],['Los Blancos','Los Merengues','Madridistas'])

    def test_with_wikipedia_applies_club_identity_fields(self):
        profile={'id':'rtdemo','name':'Demo FC','kind':'teams','source':'Reep CC0'}
        info={'country':'Spain','league':'La Liga','fullName':'Demo Fútbol Club','shortName':'Demo','manager':'Coach','chairman':'Chair','owner':'Owners','website':'https://example.com','colors':'White','nickname':'Los Demo','nicknames':['Los Demo','The Demos'],'wikiMatch':True,'wikiKind':'teams'}
        out=wiki.with_wikipedia(profile,info)
        self.assertEqual(out['country'],'Spain')
        self.assertEqual(out['fullName'],'Demo Fútbol Club')
        self.assertEqual(out['nicknames'][0],'Los Demo')
        self.assertTrue(out['source'].endswith('+ Wikipedia'))

    def test_profile_ui_contains_new_club_fields(self):
        src=(ROOT/'app.js').read_text(encoding='utf-8')
        self.assertIn('Sədr / prezident',src)
        self.assertIn('Klub rəngləri',src)
        self.assertIn('Tarixdə bu klubla əlaqəli məşqçilər',src)
        self.assertIn('badgeList(p.nicknames||p.nickname)',src)

    def test_compare_ui_mentions_assists(self):
        src=(ROOT/'app.js').read_text(encoding='utf-8')
        self.assertIn("['Asist',sumCareer(a,'assists'),sumCareer(b,'assists')]",src)

if __name__=='__main__':
    unittest.main()
