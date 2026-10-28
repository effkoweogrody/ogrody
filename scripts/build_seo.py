"""Generate static SEO for the active host, or export a separate production site.
Uses Python's standard library. It never changes DNS or repository Pages settings.
"""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote, urljoin
import argparse
import html
import json
import re
import shutil
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ARCHIVES = ('qa.html', 'index.pre-premium.html', 'post-1.html', 'privacy.html')
NS = 'http://www.sitemaps.org/schemas/sitemap/0.9'
IMAGE_NS = 'http://www.google.com/schemas/sitemap-image/1.1'

class Facts(HTMLParser):
    def __init__(self):
        super().__init__(); self.main = False; self.h1 = False; self.title = []; self.images = []; self.attrs = {}
    def handle_starttag(self, tag, attrs):
        a = dict(attrs); self.attrs = a
        if tag == 'main': self.main = True
        if tag == 'h1': self.h1 = True
        if tag == 'img' and self.main and a.get('alt', '').strip(): self.images.append(a.get('src', ''))
    def handle_endtag(self, tag):
        if tag == 'main': self.main = False
        if tag == 'h1': self.h1 = False
    def handle_data(self, data):
        if self.h1: self.title.append(data)

def attrs(tag):
    p = Facts(); p.feed(tag); return p.attrs

def public_path(path):
    parts = urlsplit(path)
    filename = parts.path.lstrip('/')
    if filename == 'index.html': filename = ''
    elif filename.endswith('.html') and filename not in (*ARCHIVES, '404.html'):
        filename = filename[:-5] + '/'
    return filename + ('?' + parts.query if parts.query else '') + ('#' + parts.fragment if parts.fragment else '')


def absolute(origin, path=''):
    return origin.rstrip('/') + '/' + public_path(path)


def output_file(filename):
    return 'index.html' if filename == 'index.html' else filename[:-5] + '/index.html'


def rewrite_urls(source, filename, origin, config):
    # Keep resources relative to the site root so an extra route directory
    # does not change image, script, gallery or navigation destinations.
    prefix = urlsplit(origin).path.rstrip('/')
    preview_prefix = urlsplit(config['preview_url']).path.rstrip('/')
    hosts = {urlsplit(config[key]).netloc for key in ('preview_url', 'production_url')}
    def rewrite(value):
        value = html.unescape(value)
        if not value or value.startswith(('#', 'data:', 'mailto:', 'tel:', 'javascript:')): return value
        u = urlsplit(value)
        if u.scheme or u.netloc:
            if u.netloc not in hosts: return value
            path = u.path.lstrip('/')
        elif value.startswith('/'):
            path = u.path.lstrip('/')
        else:
            path = urlsplit(urljoin('https://local/' + filename, value)).path.lstrip('/')
        if preview_prefix and path.startswith(preview_prefix.lstrip('/') + '/'):
            path = path[len(preview_prefix.lstrip('/')) + 1:]
        path = public_path(path)
        return prefix + '/' + path + ('?' + u.query if u.query else '') + ('#' + u.fragment if u.fragment else '')
    def attribute(match):
        key, quote, value = match.groups()
        if key.lower() == 'srcset':
            value = ', '.join(' '.join([rewrite(item.split()[0]), *item.split()[1:]]) for item in value.split(',') if item.strip())
        else: value = rewrite(value)
        return key + '=' + quote + html.escape(value, quote=True) + quote
    source = re.sub(r'\b(href|src|srcset|poster)=([' + "\"'" + r'])(.*?)\2', attribute, source, flags=re.I)
    def inline_script(match):
        if 'src=' in match[1] or 'application/ld+json' in match[1]: return match[0]
        def resource(m):
            value = m[2]
            if value.startswith(('../', './', 'assets/', '/assets/', '/ogrody/assets/')) and re.search(r'\.(webp|png|jpe?g|svg|pdf|html)(?:[?#].*)?$', value, re.I):
                return m[1] + rewrite(value) + m[1]
            return m[0]
        return match[1] + re.sub(r'(["\'])([^"\'<>\n]+)\1', resource, match[2]) + '</script>'
    return re.sub(r'(<script\b[^>]*>)(.*?)</script>', inline_script, source, flags=re.S|re.I)


def legacy_redirect(source, origin, filename):
    destination = urlsplit(canonical(origin, filename)).path
    if filename == 'index.html':
        script = 'if(location.pathname.endsWith("/index.html"))location.replace(' + json.dumps(destination) + '+location.search+location.hash);'
        block = '<script>' + script + '</script>'
    else:
        script = 'location.replace(' + json.dumps(destination) + '+location.search+location.hash);'
        block = '<script>' + script + '</script><meta http-equiv="refresh" content="0;url=' + html.escape(destination, quote=True) + '">'
    return source.replace('</head>', '<!-- ROUTE:redirect -->' + block + '<!-- /ROUTE:redirect --></head>')

def canonical(origin, filename):
    return absolute(origin, '' if filename == 'index.html' else filename)

def clean_text(value):
    return ' '.join(html.unescape(re.sub('<[^>]+>', ' ', value)).split())

def load_pages(config):
    pages = dict(config['pages'])
    projects = json.loads((ROOT / 'projects-data.json').read_text(encoding='utf-8'))
    for project in projects:
        n = str(project['number'])
        project_slug=project.get('slug') or f'projekt-ogrodu-{int(n):02}'
        pages[f'projekty/{project_slug}.html'] = {
            'title': config['project_titles'][n], 'description': config['project_descriptions'][n],
            'label': project['name'], 'kind': 'project', 'project': project,
        }
    return pages, projects

def resource_file(filename, src):
    path = unquote(urlsplit(src).path)
    prefix = urlsplit(json.loads((ROOT / 'seo-config.json').read_text(encoding='utf-8'))['preview_url']).path.rstrip('/')
    if prefix and path.startswith(prefix + '/'): path = path[len(prefix):]
    return ROOT / path.lstrip('/') if path.startswith('/') else (ROOT / filename).parent / path


def page_images(filename, source):
    p = Facts(); p.feed(source); paths = []
    for src in p.images:
        if urlsplit(src).scheme: continue
        path = resource_file(filename, src)
        if path.name.startswith('card-'): continue
        full = path.with_name(path.name.replace('-display.webp', '.webp'))
        if full.is_file(): path = full
        if path.is_file(): paths.append(path.resolve().relative_to(ROOT).as_posix())
    match = re.search(r'window\.projectGallery\s*=\s*(\{.*?\});', source, re.S)
    if match:
        gallery_json=re.sub(r'([,{]\s*)(\d+)\s*:',r'\1"\2":',match.group(1))
        gallery_json=re.sub(r',\s*([}\]])',r'\1',gallery_json)
        for group in json.loads(gallery_json).values():
            for src in group:
                path = resource_file(filename, src).resolve()
                if path.is_file(): paths.append(path.relative_to(ROOT).as_posix())
    return list(dict.fromkeys(paths))

def common_graph(config, origin):
    b = config['business']; business_id = absolute(origin, '#business'); person_id = absolute(origin, '#ewa-katrycz')
    business = {
        '@type': 'LocalBusiness', '@id': business_id, 'name': b['name'],
        'url': absolute(origin), 'telephone': b['phone'], 'email': b['email'], 'taxID': b['tax_id'],
        'description': 'Indywidualne projektowanie ogrodów przydomowych we Wrocławiu i okolicach oraz współpraca zdalna.',
        'logo': {'@type': 'ImageObject', 'url': absolute(origin, 'logo-dark.png'), 'width': 217, 'height': 132},
        'image': absolute(origin, 'ewa-katrycz-2.webp'),
        'address': {'@type': 'PostalAddress', 'streetAddress': b['street'], 'postalCode': b['postal_code'],
                    'addressLocality': b['city'], 'addressRegion': b['region'], 'addressCountry': b['country']},
        'areaServed': [{'@type': 'City', 'name': 'Wrocław'}, {'@type': 'AdministrativeArea', 'name': 'województwo dolnośląskie'}, {'@type': 'Country', 'name': 'Polska'}],
        'sameAs': b['profiles'],
        'hasOfferCatalog': {'@type': 'OfferCatalog', 'name': 'Projektowanie ogrodów i konsultacje', 'itemListElement': [
            {'@type': 'Offer', 'itemOffered': {'@type': 'Service', '@id': absolute(origin, 'oferta.html#projekt-ogrodu'), 'name': 'Indywidualny projekt ogrodu', 'url': absolute(origin, 'oferta.html')}},
            {'@type': 'Offer', 'itemOffered': {'@type': 'Service', 'name': 'Konsultacja ogrodowa online', 'url': b['consultation_url']}},
        ]},
    }
    person = {'@type': 'Person', '@id': person_id, 'name': b['owner'], 'jobTitle': 'Projektantka ogrodów',
              'url': absolute(origin, '#o-mnie'), 'image': absolute(origin, 'ewa-katrycz-2.webp'), 'worksFor': {'@id': business_id}}
    website = {'@type': 'WebSite', '@id': absolute(origin, '#website'), 'url': absolute(origin), 'name': b['name'], 'inLanguage': 'pl-PL', 'publisher': {'@id': business_id}}
    return [business, person, website]

def structured_data(config, origin, filename, page, source, images, projects):
    url = canonical(origin, filename); graph = common_graph(config, origin); kind = page['kind']
    facts = Facts(); facts.feed(source); heading = ' '.join(facts.title).strip() or page['label']
    web_type = {'contact': 'ContactPage', 'projects': 'CollectionPage', 'articles': 'CollectionPage', 'garden': 'CollectionPage'}.get(kind, 'WebPage')
    web = {'@type': web_type, '@id': url + '#webpage', 'url': url, 'name': page['title'], 'description': page['description'],
           'inLanguage': 'pl-PL', 'isPartOf': {'@id': absolute(origin, '#website')}, 'publisher': {'@id': absolute(origin, '#business')}, 'dateModified': config['modified']}
    graph.append(web)
    if filename != 'index.html':
        crumbs = [('Strona główna', absolute(origin))]
        if kind == 'project': crumbs.append(('Projekty', absolute(origin, 'projekty.html')))
        if kind == 'article': crumbs.append(('Artykuły', absolute(origin, 'artykuly.html')))
        crumbs.append((page['label'], url))
        breadcrumb_id = url + '#breadcrumb'; web['breadcrumb'] = {'@id': breadcrumb_id}
        graph.append({'@type': 'BreadcrumbList', '@id': breadcrumb_id, 'itemListElement': [
            {'@type': 'ListItem', 'position': i, 'name': name, 'item': item} for i, (name, item) in enumerate(crumbs, 1)]})
    if kind in ('home', 'projects'):
        item_id = url + '#projekty'; web['mainEntity'] = {'@id': item_id}
        graph.append({'@type': 'ItemList', '@id': item_id, 'name': 'Projekty i realizacje Effkowe Ogrody', 'itemListOrder': 'https://schema.org/ItemListOrderAscending',
                      'numberOfItems': len(projects), 'itemListElement': [
            {'@type': 'ListItem', 'position': i, 'name': p['name'], 'url': absolute(origin, 'projekty/' + (p.get('slug') or f'projekt-ogrodu-{p["number"]:02}') + '.html')}
            for i, p in enumerate(sorted(projects, key=lambda p: p['display_order']), 1)]})
    if kind == 'home':
        faqs = json.loads((ROOT / 'content.json').read_text(encoding='utf-8'))['faq']
        visible = clean_text(source)
        questions = [{'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in faqs if clean_text(q) in visible and clean_text(a) in visible]
        if questions:
            graph.append({'@type': 'FAQPage', '@id': url + '#faq', 'mainEntity': questions})
            web['hasPart'] = {'@id': url + '#faq'}
    if kind == 'offer':
        service_id = url + '#projekt-ogrodu'; web['mainEntity'] = {'@id': service_id}
        graph.append({'@type': 'Service', '@id': service_id, 'name': 'Indywidualny projekt ogrodu', 'serviceType': 'Projektowanie ogrodów przydomowych',
                      'description': page['description'], 'url': url, 'provider': {'@id': absolute(origin, '#business')},
                      'areaServed': graph[0]['areaServed']})
    if kind == 'contact': web['mainEntity'] = {'@id': absolute(origin, '#business')}
    if kind == 'project':
        project = page['project']; work_id = url + '#projekt'; web['mainEntity'] = {'@id': work_id}
        work = {'@type': 'CreativeWork', '@id': work_id, 'name': project['name'], 'description': page['description'], 'url': url,
                'creator': {'@id': absolute(origin, '#ewa-katrycz')}, 'inLanguage': 'pl-PL',
                'genre': 'Zdjęcia realizacji ogrodów' if project['number'] == 10 else 'Projekt ogrodu - wizualizacje',
                'image': [absolute(origin, i) for i in images[:8]]}
        if project['place']: work['contentLocation'] = {'@type': 'Place', 'name': project['place']}
        graph.append(work)
    if kind == 'article':
        article_id = url + '#article'; web['mainEntity'] = {'@id': article_id}
        graph.append({'@type': 'Article', '@id': article_id, 'headline': heading, 'description': page['description'], 'inLanguage': 'pl-PL',
                      'mainEntityOfPage': {'@id': url + '#webpage'}, 'author': {'@id': absolute(origin, '#ewa-katrycz')},
                      'publisher': {'@id': absolute(origin, '#business')}, 'dateModified': config['modified'], 'image': absolute(origin, 'og-image.jpg'), 'articleSection': 'Porady o projektowaniu ogrodów'})
    if kind == 'garden':
        gallery_id = url + '#ogrod-ewy'; web['mainEntity'] = {'@id': gallery_id}
        graph.append({'@type': 'ImageGallery', '@id': gallery_id, 'name': 'Ogród Ewy Katrycz we Wrocławiu', 'url': url,
                      'creator': {'@id': absolute(origin, '#ewa-katrycz')}, 'contentLocation': {'@type': 'Place', 'name': 'Wrocław'},
                      'image': [absolute(origin, i) for i in images if i.startswith('assets/my-garden/') and not Path(i).name.startswith('story-')]})
    return {'@context': 'https://schema.org', '@graph': graph}

def render_page(config, origin, filename, page, projects):
    source = (ROOT / filename).read_text(encoding='utf-8')
    source = re.sub(r'<!-- ROUTE:redirect -->.*?<!-- /ROUTE:redirect -->', '', source, flags=re.S)
    source = source.replace('href="../index.html', 'href="../').replace('href="index.html', 'href="./')
    source = re.sub(r'client-final\.css\?v=[^"\s>]+', 'client-final.css?v=20261027-form-social', source)
    source = re.sub(r'<!-- SEO:generated -->.*?<!-- /SEO:generated -->', '', source, flags=re.S)
    source = rewrite_urls(source, filename, origin, config)
    head_end = source.index('</head>'); head, body = source[:head_end], source[head_end:]
    head = re.sub(r'<title>.*?</title>', '', head, flags=re.S)
    def remove_meta(match):
        a = attrs(match.group()); key = (a.get('name') or a.get('property') or '').lower()
        return '' if key in ('description', 'robots', 'googlebot', 'bingbot') or key.startswith(('og:', 'twitter:', 'article:')) else match.group()
    head = re.sub(r'<meta\b[^>]*>', remove_meta, head, flags=re.I)
    head = re.sub(r'<link\b[^>]*>', lambda m: '' if attrs(m.group()).get('rel') == 'canonical' else m.group(), head, flags=re.I)
    images = page_images(filename, source)
    if page['kind'] in ('home', 'projects'): images += [p['cover'] for p in projects if p.get('cover')]
    if page['kind'] == 'project': images += [i['src'] for i in page['project']['images']]
    images = list(dict.fromkeys(images))
    url = canonical(origin, filename); image = page.get('project', {}).get('cover') or 'og-image.jpg'
    values = [f'<title>{html.escape(page["title"])}</title>', f'<link rel="canonical" href="{html.escape(url, quote=True)}">']
    def meta(key, value, property=False):
        values.append(f'<meta {"property" if property else "name"}="{key}" content="{html.escape(value, quote=True)}">')
    meta('description', page['description']); meta('robots', 'index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1' if page.get('index', True) else 'noindex,follow')
    for key, value in [('og:type', 'article' if page['kind'] == 'article' else 'website'), ('og:locale', 'pl_PL'), ('og:site_name', config['business']['name']), ('og:title', page['title']), ('og:description', page['description']), ('og:url', url), ('og:image', absolute(origin, image)), ('og:image:alt', page['label'] + ' - Effkowe Ogrody')]: meta(key, value, True)
    for key, value in [('twitter:card', 'summary_large_image'), ('twitter:title', page['title']), ('twitter:description', page['description']), ('twitter:image', absolute(origin, image)), ('twitter:image:alt', page['label'] + ' - Effkowe Ogrody')]: meta(key, value)
    data = structured_data(config, origin, filename, page, source, images, projects)
    values.append('<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/') + '</script>')
    block = '\n<!-- SEO:generated -->\n' + '\n'.join(values) + '\n<!-- /SEO:generated -->\n'
    return head.rstrip() + block + body, images

def robots(origin):
    prefix = urlsplit(origin).path.rstrip('/')
    paths = ['scripts/', 'tests/', 'download/', 'seo-config.json', 'SEO-MIGRACJA.md', 'SEO-MIGRACJA.html', 'README.md', 'README.html', 'PROMPTY-OBRAZY.md', 'index.bak']
    return 'User-agent: *\nAllow: /\n' + ''.join(f'Disallow: {prefix}/{p}\n' for p in paths) + '\nSitemap: ' + absolute(origin, 'sitemap.xml') + '\n'

def llms(config, origin, pages):
    b = config['business']
    text = f'# {b["name"]} - Ewa Katrycz\n\n> Projektowanie ogrodów przydomowych we Wrocławiu i okolicach oraz współpraca zdalna.\n\n'
    text += f'Ewa Katrycz jest projektantką ogrodów i tworzy Effkowe Ogrody. Zakres indywidualnego projektu ustalany jest w ofercie; wizualizacje 3D i projekt nawadniania są opcjonalne. Konsultacje ogrodowe online są dostępne przez odnośnik na stronie.\n\n'
    text += f'Kontakt: {b["phone"]}, {b["email"]}. Adres firmy: {b["street"]}, {b["postal_code"]} {b["city"]}, Polska.\n\n'
    text += 'Portfolio rozróżnia wizualizacje projektów od zdjęć wykonanych ogrodów. Lokalizacje i powierzchnie są podane na poszczególnych stronach. Termin i cena wymagają indywidualnych ustaleń.\n\n## Strony\n\n'
    for filename, page in pages.items():
        if page.get('index', True): text += f'- [{page["label"]}]({canonical(origin, filename)}): {page["description"]}\n'
    return text

def not_found(origin):
    return f'''<!doctype html><html lang="pl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,follow"><title>Nie znaleziono strony | Effkowe Ogrody</title><style>body{{margin:0;background:#f2e9e1;color:#294535;font:18px/1.7 Georgia,serif;display:grid;place-items:center;min-height:100svh}}main{{max-width:650px;padding:40px 24px}}h1{{font-size:clamp(36px,7vw,64px);line-height:1.15}}a{{color:inherit;text-underline-offset:5px}}nav{{display:flex;flex-wrap:wrap;gap:24px}}:focus-visible{{outline:2px solid #c96f7d;outline-offset:5px}}</style></head><body><main><p>EFFKOWE OGRODY · 404</p><h1>Nie znaleziono tej strony.</h1><p>Wróć do strony głównej lub zobacz projekty ogrodów.</p><nav aria-label="Przejdź dalej"><a href="{absolute(origin)}">Strona główna</a><a href="{absolute(origin,'projekty.html')}">Projekty</a><a href="{absolute(origin,'kontakt.html')}">Kontakt</a></nav></main></body></html>\n'''

def build(origin, output, copy_assets=False, write_cname=False):
    config = json.loads((ROOT / 'seo-config.json').read_text(encoding='utf-8'))
    parts = urlsplit(origin)
    if parts.scheme != 'https' or not parts.hostname or parts.query or parts.fragment or parts.username: raise ValueError('Origin must be an HTTPS URL without query, credentials or fragment.')
    origin = origin.rstrip('/'); output = Path(output).resolve()
    if copy_assets and (output == ROOT or ROOT in output.parents): raise ValueError('Export the production site outside the source repository.')
    if write_cname and (parts.path not in ('', '/') or origin != config['production_url']): raise ValueError('CNAME activation is supported only for the configured production domain.')
    output.mkdir(parents=True, exist_ok=True)
    if copy_assets:
        shutil.copytree(ROOT / 'assets', output / 'assets', dirs_exist_ok=True)
        allowed = {'.css', '.js', '.png', '.jpg', '.jpeg', '.webp', '.svg', '.ico', '.woff', '.woff2', '.pdf'}
        for path in ROOT.iterdir():
            if path.is_file() and path.suffix.lower() in allowed: shutil.copy2(path, output / path.name)
    pages, projects = load_pages(config); images_by_page = {}
    for filename, page in pages.items():
        source, images = render_page(config, origin, filename, page, projects)
        target = output / output_file(filename); target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(source.encode('utf-8'))
        legacy = output / filename; legacy.parent.mkdir(parents=True, exist_ok=True); legacy.write_bytes(legacy_redirect(source, origin, filename).encode('utf-8'))
        if page.get('index', True): images_by_page[filename] = images
    if output == ROOT:
        for filename in ARCHIVES:
            p = ROOT / filename
            if not p.exists(): continue
            source = p.read_text(encoding='utf-8')
            source = re.sub(r'<meta\b[^>]*>', lambda m: '' if attrs(m.group()).get('name', '').lower() == 'robots' else m.group(), source)
            source = source.replace('</head>', '<meta name="robots" content="noindex,follow"></head>')
            p.write_bytes(('\n'.join(line.rstrip() for line in source.splitlines())+'\n').encode('utf-8'))
    ET.register_namespace('', NS); ET.register_namespace('image', IMAGE_NS); sitemap = ET.Element(f'{{{NS}}}urlset')
    for filename, images in images_by_page.items():
        node = ET.SubElement(sitemap, f'{{{NS}}}url'); ET.SubElement(node, f'{{{NS}}}loc').text = canonical(origin, filename); ET.SubElement(node, f'{{{NS}}}lastmod').text = config['modified']
        for image in images:
            child = ET.SubElement(node, f'{{{IMAGE_NS}}}image'); ET.SubElement(child, f'{{{IMAGE_NS}}}loc').text = absolute(origin, image)
    ET.indent(sitemap, space='  '); (output / 'sitemap.xml').write_bytes(ET.tostring(sitemap,encoding='utf-8',xml_declaration=True)+b'\n')
    (output / 'robots.txt').write_bytes(robots(origin).encode('utf-8'))
    (output / 'adresy-do-indeksowania.txt').write_bytes(('\n'.join(canonical(origin, f) for f in images_by_page) + '\n').encode('utf-8'))
    (output / 'llms.txt').write_bytes(llms(config, origin, pages).encode('utf-8'))
    (output / '404.html').write_bytes(not_found(origin).encode('utf-8'))
    (output / '.nojekyll').write_bytes(b'')
    if write_cname: (output / 'CNAME').write_bytes((parts.hostname + '\n').encode('ascii'))
    return {'origin': origin, 'pages': len(pages), 'sitemap_urls': len(images_by_page), 'sitemap_images': sum(map(len, images_by_page.values())), 'output': str(output)}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--origin'); parser.add_argument('--output', type=Path, default=ROOT)
    parser.add_argument('--copy-assets', action='store_true'); parser.add_argument('--write-cname', action='store_true')
    args = parser.parse_args(); config = json.loads((ROOT / 'seo-config.json').read_text(encoding='utf-8'))
    cname = (ROOT / 'CNAME').read_text(encoding='utf-8').strip() if (ROOT / 'CNAME').exists() else ''
    origin = args.origin or ('https://' + cname if cname else config['preview_url'])
    print(json.dumps(build(origin, args.output, args.copy_assets, args.write_cname), ensure_ascii=False))

if __name__ == '__main__': main()
