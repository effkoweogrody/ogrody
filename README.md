# Effkowe Ogrody — landing page

Statyczna strona HTML/CSS/JS przygotowana pod GitHub Pages.

## Pliki

- `index.html` — landing page
- `style.css` — wszystkie style, responsywność i podstrony
- `script.js` — sticky header, menu mobile, lightbox i formularz
- `blog/post-1.html` — przykładowy wpis blogowy
- `privacy.html` — placeholder polityki prywatności do zatwierdzenia
- `assets/logo/` — logo ciemne i jasne
- `assets/icons/` — favicon, apple touch icon, OG image

## 1. Formularz kontaktowy

1. Załóż formularz w Formspree.
2. W `script.js` podmień `https://formspree.io/f/TWOJ_ENDPOINT`.
3. W `index.html` podmień ten sam adres w `action` formularza.

## 2. Zdjęcia

Wersja demonstracyjna używa kilku publicznie dostępnych zdjęć/realizacji klientki z jej profilu Oferteo oraz grafik produktów z Naffy jako **zewnętrznych URL**.

Przed finalnym wdrożeniem najlepiej pobrać od klientki oryginalne pliki i wrzucić je lokalnie do `assets/img/`, a następnie podmienić adresy w HTML/CSS na ścieżki względne, np.:

```html
<img src="assets/img/realizacja-01.webp" ...>
```

Docelowo: WebP, jakość 78–82, hero < 250 KB, pozostałe < 150 KB.

## 3. Jak dodać wpis blogowy

1. Skopiuj `blog/post-1.html` do np. `blog/jak-zaprojektowac-rabate.html`.
2. Podmień `<title>`, `meta description`, canonical, H1, zdjęcie i treść.
3. Dodaj kafel prowadzący do wpisu w sekcji `#blog` w `index.html`.
4. Dopisz adres do `sitemap.xml`.

## 4. Domena i GitHub Pages

1. Wgraj repo na GitHub.
2. `Settings → Pages → Deploy from branch → main / root`.
3. Jeśli domena ma być własna, wpisz ją do pliku `CNAME` bez `https://`.
4. W panelu domeny ustaw rekordy DNS wskazane przez GitHub Pages.
5. W `index.html`, `robots.txt`, `sitemap.xml` oraz wpisach blogowych podmień `https://effkoweogrody.pl/`, jeśli domena będzie inna.

## 5. Treści do potwierdzenia przed publikacją

- ostateczny opis Ewy w sekcji „O mnie”
- ostateczny zakres usługi „projekt ogrodu”
- finalny tekst polityki prywatności
- własny endpoint Formspree
- docelowa domena
- zdjęcie portretowe Ewy (w obecnym projekcie sekcja używa realizacji ogrodu zamiast portretu)
- oryginalne zdjęcia realizacji bez kompresji z social mediów

## Kolory

- `#233A2C` — Forest
- `#8B9D82` — Sage
- `#F6F2E9` — Warm Sand
- `#7A5F47` — Bark
- `#17231C` — Ink

Fonty: Cormorant Garamond + Montserrat.
