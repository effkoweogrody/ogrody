import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('build_seo',ROOT/'scripts/build_seo.py');seo=importlib.util.module_from_spec(spec);spec.loader.exec_module(seo)
CONFIG=json.loads((ROOT/'seo-config.json').read_text(encoding='utf-8'))

class Read(HTMLParser):
    def __init__(self):super().__init__();self.meta={};self.canonical=[];self.ld=False;self.data=[];self.names=[]
    def handle_starttag(self,t,a):
        a=dict(a)
        if t=='meta':self.meta[a.get('name',a.get('property'))]=a.get('content')
        if t=='link' and a.get('rel')=='canonical':self.canonical.append(a['href'])
        if t=='script' and a.get('type')=='application/ld+json':self.ld=True
    def handle_endtag(self,t):
        if t=='script':self.ld=False
    def handle_data(self,d):
        if self.ld:self.data.append(d)

class SEOTests(unittest.TestCase):
    def test_preview_and_production(self):
        pages,_=seo.load_pages(CONFIG)
        for origin in [CONFIG['preview_url'],CONFIG['production_url']]:
            with self.subTest(origin=origin),tempfile.TemporaryDirectory() as directory:
                target=Path(directory);result=seo.build(origin,target)
                self.assertEqual(result['pages'],21);self.assertEqual(result['sitemap_urls'],20)
                titles=set();descriptions=set();indexed=[]
                for filename,page in pages.items():
                    source=(target/filename).read_text(encoding='utf-8');p=Read();p.feed(source)
                    self.assertEqual(p.canonical,[seo.canonical(origin,filename)])
                    self.assertEqual(p.meta['og:url'],p.canonical[0]);self.assertTrue(p.meta['og:image'].startswith(origin+'/'))
                    self.assertEqual(p.meta['description'],page['description']);self.assertGreater(len(page['description']),90)
                    self.assertNotIn(page['title'],titles);titles.add(page['title'])
                    self.assertNotIn(page['description'],descriptions);descriptions.add(page['description'])
                    data=json.loads(''.join(p.data));self.assertEqual(data['@context'],'https://schema.org')
                    graph=data['@graph'];ids=[x['@id'] for x in graph];self.assertEqual(len(ids),len(set(ids)))
                    self.assertEqual(graph[0]['@type'],'LocalBusiness');self.assertEqual(graph[0]['address']['addressLocality'],'Wrocław')
                    self.assertNotIn('aggregateRating',json.dumps(data));self.assertNotIn('openingHours',json.dumps(data))
                    if page.get('index',True):self.assertTrue(p.meta['robots'].startswith('index,follow'));indexed.append(seo.canonical(origin,filename))
                    else:self.assertEqual(p.meta['robots'],'noindex,follow')
                    if origin==CONFIG['production_url']:self.assertNotIn('jakubskrzypiec.github.io/ogrody',source)
                xml=ET.parse(target/'sitemap.xml');urls=[n.text for n in xml.findall(f'.//{{{seo.NS}}}url/{{{seo.NS}}}loc')]
                self.assertCountEqual(urls,indexed)
                for node in xml.findall(f'.//{{{seo.IMAGE_NS}}}loc'):
                    self.assertTrue(node.text.startswith(origin+'/'));relative=node.text[len(origin)+1:];self.assertTrue((ROOT/relative).is_file(),relative)
                robots=(target/'robots.txt').read_text(encoding='utf-8');self.assertNotIn('Disallow: /projekty/',robots);self.assertNotIn('Disallow: /artykuly/',robots)
                self.assertIn('Sitemap: '+seo.absolute(origin,'sitemap.xml'),robots)
                self.assertNotIn('polityka-prywatnosci.html',(target/'llms.txt').read_text(encoding='utf-8'))
                first={f:(target/f).read_bytes() for f in pages};seo.build(origin,target)
                self.assertEqual(first,{f:(target/f).read_bytes() for f in pages})
    def test_domain_export_does_not_activate_source(self):
        previous=(ROOT/'CNAME').read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            seo.build(CONFIG['production_url'],directory,write_cname=True)
            self.assertEqual((Path(directory)/'CNAME').read_text().strip(),'effkoweogrody.pl')
        self.assertEqual((ROOT/'CNAME').read_bytes(),previous)
    def test_reject_bad_origins(self):
        for origin in ['http://example.com','https://example.com/?test=1','https://user:password@example.com']:
            with self.subTest(origin=origin),tempfile.TemporaryDirectory() as directory:
                with self.assertRaises(ValueError):seo.build(origin,directory)
    def test_visible_faq_and_real_project_order(self):
        pages,projects=seo.load_pages(CONFIG);source,_=seo.render_page(CONFIG,CONFIG['production_url'],'index.html',pages['index.html'],projects)
        p=Read();p.feed(source);graph=json.loads(''.join(p.data))['@graph']
        faq=next(x for x in graph if x['@type']=='FAQPage');self.assertEqual(len(faq['mainEntity']),9)
        listing=next(x for x in graph if x['@type']=='ItemList');self.assertEqual([x['url'].split('-')[-1].split('.')[0] for x in listing['itemListElement']],['11','02','03','05','06','07','08','09','04','01','10'])

if __name__=='__main__':unittest.main()
