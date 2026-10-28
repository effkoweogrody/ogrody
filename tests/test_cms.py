import unittest,tempfile,importlib.util,shutil,json,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('cms_builder',ROOT/'scripts/build_cms.py');cms=importlib.util.module_from_spec(spec);spec.loader.exec_module(cms)
class CMSTests(unittest.TestCase):
 def test_new_content_and_safe_render(self):
  with tempfile.TemporaryDirectory() as directory:
   target=Path(directory)
   for f in ['index.html','projekty.html','artykuly.html','seo-config.json','cms/published.json','cms/templates/project.html','cms/templates/article.html']:
    dest=target/f;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/f,dest)
   data=json.loads((target/'cms/published.json').read_text(encoding='utf-8'))
   project=copy.deepcopy(data['projects'][0]);project.update(id='project-test',number=12,slug='nowy-ogrod',name='Ogród <script>alert(1)</script>',legacy=False,display_order=-1)
   article=copy.deepcopy(data['articles'][0]);article.update(id='article-test',slug='nowa-notatka',title='Nowa <img onerror=alert(1)>',legacy=False,blocks=[{'type':'heading','text':'Plan ogrodu'},{'type':'paragraph','text':'Bezpieczny tekst <script>alert(1)</script>'},{'type':'list','text':'Pierwszy\nDrugi'},{'type':'image','src':project['cover'],'alt':'Ogród','text':'Podpis'}])
   data['projects'].append(project);data['articles'].append(article);(target/'cms/published.json').write_text(json.dumps(data),encoding='utf-8')
   old=cms.ROOT;cms.ROOT=target
   try:cms.build()
   finally:cms.ROOT=old
   p=cms.soup((target/'projekty/nowy-ogrod.html').read_text(encoding='utf-8'));a=cms.soup((target/'artykuly/nowa-notatka.html').read_text(encoding='utf-8'))
   self.assertEqual(p.select_one('h1').get_text(),project['name']);self.assertFalse(p.select('h1 script'));self.assertEqual(len(p.select('.client-gallery figure')),len([i for i in project['images'] if not i.get('is_top')]))
   self.assertFalse(a.select('h1 img'));self.assertIn('<script>',a.select_one('.note-sheet p').get_text());self.assertEqual(len(a.select('.cms-article-image')),1)
   home=cms.soup((target/'index.html').read_text(encoding='utf-8'));self.assertEqual(home.select_one('.carousel-card')['href'],'/projekty/nowy-ogrod/')
   self.assertEqual(len(json.loads((target/'projects-data.json').read_text(encoding='utf-8'))),12)
 def test_reject_image_traversal(self):
  for value in ['../../private.php','https://evil.test/a.jpg','assets/../secret.webp','javascript:alert(1)']:
   with self.subTest(value=value),self.assertRaises(ValueError):cms.path(value)
if __name__=='__main__':unittest.main()
