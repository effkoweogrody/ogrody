# Panel Effkowe Ogrody

## Obsługa

Adres: https://panel.effkoweogrody.pl/ (także https://effkoweogrody.pl/admin/).
Login: ewa. Hasło startowe przekazywane osobno; przy pierwszym logowaniu trzeba ustawić własne.

1. Wybierz Projekty ogrodów albo Artykuły i kliknij Dodaj.
2. Uzupełnij tytuł i opis. Zdjęcia dodaj z komputera lub telefonu; panel zmniejsza je automatycznie.
3. W projekcie zaznacz okładkę, opcjonalnie rzut z góry, ustaw kolejność zdjęć i pozycję na liście.
4. W artykule dodawaj nagłówki, akapity, listy i zdjęcia.
5. Zapisz szkic. Sam zapis nie zmienia publicznej strony.
6. Sprawdź podgląd i kliknij Opublikuj. Poczekaj na zielone potwierdzenie zakończonej publikacji.
7. Archiwum ukrywa treść na stronie i zachowuje ją w panelu. Możesz przywrócić szkic i opublikować go ponownie.

Adres opublikowanej podstrony jest stały. Ułatwia to zachowanie linków i pozycji w Google.
Pola widoczności w Google są opcjonalne; domyślnie panel przygotowuje tytuł i opis.

## Utrzymanie

- Publiczna strona: GitHub Pages, repo effkoweogrody/ogrody, workflow cms-publish.yml.
- Panel: PHP 8.4 z curl, mbstring, GD i obsługą WebP na OVH.
- Pliki publiczne z cms-server/public wdrażane do /home/effkowv/www/panel.
- Konfiguracja, stan, sesje i zdjęcia szkiców: /home/effkowv/cms-private, poza katalogiem WWW.
- config.example.php pokazuje wymagane pola. Hasła i token nigdy nie trafiają do repozytorium.
- cms/published.json zawiera wyłącznie opublikowane treści. Szkice pozostają na OVH.
- Workflow buduje podstrony, metadane, sitemapę i publikuje tylko publiczny eksport.
- Nie nadpisuj state.json ani seed.json przy ponownym wdrożeniu istniejącego panelu.
- Edycje treści poza panelem wymagają synchronizacji rewizji; mechanizm odmawia nadpisania niespójnej wersji.
- Rotacja tokenu GitHub: podmień wyłącznie prywatny config.php na serwerze. Konto powinno mieć dostęp wyłącznie do repo klientki.
- Kopie bezpieczeństwa: repozytorium przechowuje historię publikacji, a state.json.bak poprzedni zapis panelu. Przed aktualizacją wykonaj osobną kopię katalogu prywatnego.
- Limit zdjęć szkiców jest kontrolowany. Przy zbliżeniu do limitu hostingu opiekun archiwizuje opublikowane pliki po potwierdzeniu ich dostępności na stronie; nie usuwaj zdjęć nieopublikowanych.

## Testy

python -m pip install -r scripts/requirements-cms.txt
python scripts/build_cms.py
python -m unittest discover -s tests -v
python scripts/build_seo.py --origin https://effkoweogrody.pl --output ../public-site --copy-assets --write-cname

Testy sprawdzają nowe projekty i artykuły, bezpieczne wyświetlanie tekstów, galerie, czyste adresy, sitemapę i metadane.
