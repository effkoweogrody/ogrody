# SEO i podpięcie effkoweogrody.pl

## Aktualny stan

- 21 aktywnych podstron ma indywidualne metadane i statyczne JSON-LD.
- 20 stron jest przeznaczonych do indeksowania. Robocza polityka prywatności oraz strony archiwalne/testowe mają `noindex,follow`.
- Sitemap zawiera adresy stron i zdjęć; daty `lastmod` oznaczają rzeczywistą zmianę treści/metadanych, nie każde uruchomienie skryptu.
- Canonicale, Open Graph, JSON-LD, robots.txt, llms.txt i linki 404 korzystają z jednego adresu bazowego.
- Podgląd nadal działa na GitHub Pages. Plik CNAME pozostaje pusty, dopóki nie uruchamiamy domeny.
- Dnia 27.10.2026 domena docelowa nie rozwiązywała się w sprawdzanym DNS. Samo przygotowanie plików nie podpina domeny ani nie weryfikuje Search Console.

## Generowanie

Python 3, bez dodatkowych bibliotek:

```
python scripts/build_seo.py
```

Domyślnie skrypt odczyta host z CNAME, a przy pustym CNAME użyje aktualnego adresu podglądu. Konfiguracja treści i danych firmy: `seo-config.json`.

Pełna osobna wersja produkcyjna, bez zmiany podglądu:

```
python scripts/build_seo.py --origin https://effkoweogrody.pl --output ../release-effkoweogrody-pl --copy-assets --write-cname
```

Folder zawiera komplet plików do hostowania: HTML, CSS, JavaScript, fotografie, dokumenty, sitemap.xml, robots.txt, llms.txt, 404.html i CNAME. Nie zawiera .git, kopii roboczych, skryptów, testów ani konfiguracji źródłowej. Skrypt nie usuwa istniejących folderów i nie zmienia DNS.

## Przełączenie w uzgodnionym momencie

1. Zapewnić dostęp właścicielki do domeny i panelu DNS. Jeśli pozostajemy na GitHub Pages, zweryfikować własność domeny w GitHub zgodnie z dokumentacją, przed podpięciem do repozytorium.
2. W oknie migracji przygotować wersję główną:

```
python scripts/build_seo.py --origin https://effkoweogrody.pl --write-cname
python -m unittest discover -s tests -v
```

3. Opublikować wynik i ustawić domenę niestandardową w GitHub Pages; w tym samym oknie ustawić DNS. GitHub zaleca dodanie domeny do Pages przed skierowaniem DNS na Pages. Nie wprowadzać rekordów wildcard.
4. Dla GitHub Pages rekordy `A` hosta `@`: `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`. Rekord `CNAME` hosta `www`: `effkoweogrody.github.io` (bez `/ogrody`). Zachować istniejące rekordy poczty MX/TXT; zmiany DNS trzeba dostosować do faktycznej konfiguracji panelu.
5. Sprawdzić HTTPS i wymuszanie HTTPS, przekierowanie www do wersji bez www, stary adres GitHub Pages i wewnętrzne linki. Po migracji preferowany adres główny: `https://effkoweogrody.pl/`, bez `/ogrody/`. Zweryfikować realne kody 301/308 hosta, nie zastępować ich wyłącznie przekierowaniem JavaScript.
6. Zweryfikować usługę domenową w Google Search Console oraz Bing Webmaster Tools (potrzebny dostęp do konta / kod TXT). Zgłosić `https://effkoweogrody.pl/sitemap.xml`, sprawdzić główną stronę, ofertę, kontakt i projekty we Wrocławiu przez Inspekcję URL.
7. Uzupełnić i zweryfikować Profil Firmy w Google, jeżeli właścicielka ma do niego dostęp; dane nazwy, telefonu i adresu powinny być zgodne. Nie dodawać niepotwierdzonych godzin, ocen, współrzędnych, cen ani osobnych fikcyjnych oddziałów. Nie zgłoszono automatycznie sitemapy, nie stworzono wizytówki i nie zgłoszono URL-i do IndexNow.
8. Potwierdzić warunki formularza, odbiór zapytania i politykę prywatności przed końcowym uruchomieniem. Brakujący rzut Teklinowa jest kwestią materiałów, a nie blokadą mapy strony.

## Zakres danych strukturalnych i AI

LocalBusiness, Person, WebSite, WebPage/CollectionPage/ContactPage, Service, BreadcrumbList, Article, CreativeWork i ImageGallery odpowiadają widocznym treściom. FAQPage obejmuje tylko pytania i odpowiedzi obecne na stronie; oznaczenie porządkuje semantykę pytań, natomiast Google wycofało wyniki rozszerzone FAQ w maju 2026 r. Nie dodano gwiazdek ani ocen agregowanych do własnych opinii.

Treści i linki są obecne w HTML bez JavaScript. Robots.txt nie blokuje publicznych podstron ani zasobów renderowania, więc reguła ogólna obejmuje także boty wyszukujące AI. Nie zmieniano odrębnie polityki treningu modeli. llms.txt to dodatkowy katalog informacji i linków, nie wymóg ani gwarancja widoczności w Google/ChatGPT/Copilot. SEO ułatwia odczyt i indeksowanie; nie gwarantuje pozycji ani cytowania przez AI.

Robots.txt projektu GitHub Pages jest pod `/ogrody/robots.txt`; reguły robotów są interpretowane z głównego katalogu hosta. Docelowo na własnej domenie plik będzie we właściwym miejscu: `/robots.txt`.

## Oficjalne źródła

- https://developers.google.com/search/docs/appearance/ai-features
- https://developers.google.com/search/docs/appearance/structured-data/local-business
- https://developers.google.com/search/updates
- https://schema.org/FAQPage
- https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap
- https://developers.openai.com/api/docs/bots
- https://blogs.bing.com/webmaster/2025/7/Keeping-Content-Discoverable-with-Sitemaps-in-AI-Powered-Search/
- https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site
