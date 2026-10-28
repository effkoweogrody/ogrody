"""Build public projects and notebook articles from the CMS publication snapshot."""
from pathlib import Path
from bs4 import BeautifulSoup
import json,re,html,copy
ROOT=Path(__file__).resolve().parents[1]
E=lambda value:html.escape(str(value or ''),quote=True)
def soup(text):return BeautifulSoup(text,'html.parser')
def fragment(text):return soup(text)
def save(path,doc):path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(str(doc).encode('utf-8'))
def path(src):
 value=str(src or '').lstrip('/')
 if not re.fullmatch(r'(?:assets/[A-Za-z0-9_./-]+|[A-Za-z0-9_.-]+\.(?:webp|png|jpg|jpeg))',value) or '..' in value:raise ValueError('Invalid image path')
 return '/'+value

def validate(data):
 if data.get('version')!=1:raise ValueError('Unknown publication version')
 ids=set();slugs=set();numbers=set()
 for kind in ('projects','articles'):
  for item in data[kind]:
   if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',item['slug']):raise ValueError('Invalid slug')
   if item['id'] in ids or (kind,item['slug']) in slugs:raise ValueError('Duplicate record')
   ids.add(item['id']);slugs.add((kind,item['slug']))
   if kind=='projects':
    if item['number'] in numbers:raise ValueError('Duplicate project number')
    numbers.add(item['number']);path(item['cover'])
    if not item.get('images'):raise ValueError('Project without photos')
    for image in item['images']:path(image['src'])
   elif not item.get('blocks'):raise ValueError('Article without content')

def img_tag(image,alt):
 source=path(image.get('display') or image['src'])
 return f'<img src="{E(source)}" alt="{E(image.get("alt") or alt)}" loading="lazy" decoding="async" width="{int(image.get("width") or 1600)}" height="{int(image.get("height") or 1000)}">'

def project_page(item):
 doc=soup((ROOT/'cms/templates/project.html').read_text(encoding='utf-8'));doc.select_one('#page-title').string=item['name'];number=item['number'];facts=item.get('facts',{})
 doc.select_one('.case-facts').replace_with(fragment('<div class="case-facts">'+''.join(f'<p>{E(label)}<br><strong>{E(value)}</strong></p>' for label,value in [('Lokalizacja',facts.get('Lokalizacja') or item.get('place')),('Powierzchnia',item.get('area')),('Styl',facts.get('Styl'))] if value)+'</div>'))
 doc.select_one('.project-story-copy').clear()
 for paragraph in item.get('description',[]):doc.select_one('.project-story-copy').append(fragment('<p>'+E(paragraph)+'</p>'))
 elements=doc.select_one('.project-elements')
 if facts.get('Główne elementy'):elements.clear();elements.append(fragment('<strong>Główne elementy</strong><br>'+E(facts['Główne elementy'])))
 else:elements.decompose()
 top=next(((i,image) for i,image in enumerate(item['images']) if image.get('is_top')),None)
 if top:
  i,image=top;doc.select_one('.project-top-view').replace_with(fragment(f'<figure class="project-top-view"><a href="{E(path(image["src"]))}" data-gallery="{number}" data-index="{i}">{img_tag(image,item["name"]+" - widok z góry")}</a><figcaption>Widok z góry</figcaption></figure>'))
 else:doc.select_one('.project-top-view').decompose()
 gallery=doc.select_one('.client-gallery');gallery.clear()
 for i,image in enumerate(item['images']):
  if image.get('is_top'):continue
  gallery.append(fragment(f'<figure><a href="{E(path(image["src"]))}" data-gallery="{number}" data-index="{i}">{img_tag(image,item["name"]+" - ujęcie "+str(i+1))}</a></figure>'))
 for script in doc.find_all('script'):
  if script.string and 'window.projectGallery=' in script.string:
   images={str(number):[path(image['src']) for image in item['images']]}
   script.string='window.projectGallery='+json.dumps(images,ensure_ascii=False).replace('</','<\\/')+';window.projectGalleryNames='+json.dumps({str(number):item['name']},ensure_ascii=False).replace('</','<\\/')+';'
 save(ROOT/f'projekty/{item["slug"]}.html',doc)

def article_page(item):
 doc=soup((ROOT/'cms/templates/article.html').read_text(encoding='utf-8'));doc.select_one('h1').string=item['title'];doc.select_one('.notebook-paper p').string=item.get('summary','')
 for category in doc.select('.note-category'):category.string=item.get('category') or 'Ogrodowy notatnik'
 reader=doc.select_one('.notebook-sheets');reader.clear();reader.append(fragment('<p class="article-byline">Autorka: <a href="/#o-mnie">Ewa Katrycz</a> · projektantka ogrodów, Effkowe Ogrody</p>'))
 if item.get('cover'):reader.append(fragment('<figure class="cms-article-image"><img src="'+E(path(item['cover']))+'" alt="'+E(item['title'])+'" loading="lazy"></figure>'))
 sections=[];current=None
 for block in item['blocks']:
  if block['type']=='heading' or current is None:
   current={'title':block.get('text','') if block['type']=='heading' else item['title'],'blocks':[]};sections.append(current)
  if block['type']!='heading':current['blocks'].append(block)
 toc=doc.select_one('.notebook-toc nav');toc.clear()
 for i,section in enumerate(sections,1):
  content=f'<section class="note-sheet" id="notatka-{i}"><span class="sheet-number">NOTATKA / {i:02}</span><h2>{E(section["title"])}</h2>'
  for block in section['blocks']:
   if block['type']=='paragraph':content+='<p>'+E(block.get('text','')).replace('\n','<br>')+'</p>'
   elif block['type']=='list':content+='<ul>'+''.join('<li>'+E(line)+'</li>' for line in block.get('text','').splitlines() if line.strip())+'</ul>'
   elif block['type']=='image' and block.get('src'):content+='<figure class="cms-article-image"><img src="'+E(path(block['src']))+'" alt="'+E(block.get('alt',''))+'" loading="lazy"><figcaption>'+E(block.get('text',''))+'</figcaption></figure>'
  content+=f'<div class="sheet-footer"><span>Effkowe Ogrody / Ogrodowy notatnik</span><span>{i:02}</span></div></section>'
  reader.append(fragment(content));toc.append(fragment(f'<a href="#notatka-{i}"><span>{i:02}</span>{E(section["title"])}</a>'))
 save(ROOT/f'artykuly/{item["slug"]}.html',doc)

def card(item,kind):
 url='/projekty/'+item['slug']+'/';cover=next((x for x in item['images'] if x['src']==item['cover']),item['images'][0]);image=img_tag({**cover,'display':cover.get('card') or cover.get('display') or cover['src']},item['name']);facts=item.get('facts',{});style=facts.get('Styl','');area=item.get('area','');place=item.get('place','')
 if kind=='carousel':return fragment(f'<a class="carousel-card" href="{url}"><div class="carousel-image">{image}<span class="carousel-brand" aria-hidden="true">Zobacz projekt</span></div><div class="carousel-caption"><h3>{E(item["name"])}</h3><span>{E(place)} · {E(style)}</span><span class="project-area">{E(area)}</span></div></a>')
 return fragment(f'<a class="portfolio-tile reveal" href="{url}"><div class="portfolio-tile-image">{image}</div><div class="portfolio-tile-caption"><h3>{E(item["name"])}</h3><p class="project-card-character">{E(style)}</p><span>{E(place)} · {E(area)}</span></div></a>')

def build():
 data=json.loads((ROOT/'cms/published.json').read_text(encoding='utf-8'));validate(data);projects=sorted(data['projects'],key=lambda p:(p.get('display_order',999),p['number']));articles=data['articles'];config=json.loads((ROOT/'seo-config.json').read_text(encoding='utf-8'))
 for item in projects:
  if not item.get('legacy'):project_page(item)
 for item in articles:
  if not item.get('legacy'):article_page(item)
 for filename,selector,kind in [('index.html','.carousel-group','carousel'),('projekty.html','.portfolio-index-grid','portfolio')]:
  doc=soup((ROOT/filename).read_text(encoding='utf-8'));container=doc.select_one(selector);existing={a.get('href',''):copy.deepcopy(a) for a in container.select('a[href]') if a.get('class') and ('carousel-card' in a.get('class') or 'portfolio-tile' in a.get('class'))};container.clear()
  for item in projects:
   if kind=='carousel' and not item.get('featured',True):continue
   url='/projekty/'+item['slug']+'/'
   container.append(existing[url] if item.get('legacy') and url in existing else card(item,kind))
  save(ROOT/filename,doc)
 doc=soup((ROOT/'artykuly.html').read_text(encoding='utf-8'));container=doc.select_one('.notebook-library');existing={li.select_one('a.note-book').get('href'):copy.deepcopy(li) for li in container.select('li')};container.clear()
 for i,item in enumerate(articles):
  url='/artykuly/'+item['slug']+'/'
  if item.get('legacy') and url in existing:container.append(existing[url]);continue
  container.append(fragment(f'<li><a class="note-book note-book-{i%3} reveal" href="{url}"><div class="note-cover"><span class="note-category">{E(item.get("category") or "Ogrodowy notatnik")}</span><img class="note-logo" src="/logo-light.png" alt="" width="217" height="132"><h3>{E(item["title"])}</h3><span class="note-cover-bottom">Otwórz notatnik</span></div></a><p class="note-summary">{E(item.get("summary",""))}</p><a class="quiet-link" href="{url}">Przeczytaj artykuł</a></li>'))
 save(ROOT/'artykuly.html',doc)
 config['pages']={f:p for f,p in config['pages'].items() if p['kind']!='article'}
 for item in articles:config['pages']['artykuly/'+item['slug']+'.html']={'title':item.get('seoTitle') or item['title']+' | Effkowe Ogrody','description':item.get('seoDescription') or item.get('summary',''),'label':item['title'],'kind':'article'}
 config['project_titles']={str(p['number']):p.get('seoTitle') or p['name']+' | Effkowe Ogrody' for p in projects};config['project_descriptions']={str(p['number']):p.get('seoDescription') or ' '.join(p.get('description',[]))[:280] for p in projects}
 for p in projects:p['has_top']=any(i.get('is_top') for i in p['images'])
 (ROOT/'projects-data.json').write_bytes((json.dumps(projects,ensure_ascii=False,indent=2)+'\n').encode('utf-8'));(ROOT/'seo-config.json').write_bytes((json.dumps(config,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
 print(json.dumps({'projects':len(projects),'articles':len(articles),'revision':data['revision']}))
if __name__=='__main__':build()
