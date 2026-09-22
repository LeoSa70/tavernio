# Tavernio — Projektkontext für Claude Code

## Was das ist

Ein deutschsprachiges Werkzeug für **Vorrat → Einkauf → Rezepte**, für
zwei Personen im eigenen Haushalt. Es beantwortet drei Fragen:

1. Was ist da?
2. Was muss gekauft werden?
3. Was lässt sich heute daraus kochen?

Die Ernährungsform ist **mediterran** — das ist keine Beigabe, sondern
prägt Vorratsliste, Gruppen und Rezepte. Siehe unten.

**Machart wie die Friedensgruppe**: `build.py` erzeugt aus Textdateien
statische Seiten nach `dist/`, die später auf den Webspace wandern.
Nicht wie Spreehaus (eine HTML-Datei per Doppelklick) — der
Einkaufszettel muss im Laden aufs Handy.

## Bauen, Prüfen, Ausführen

```
python build.py              baut nach dist/
python build.py --pruefen    prüft nur, schreibt nichts
python -m unittest discover -s tests -t .   die Prüfungen (23)
```

`dist/index.html` im Browser öffnen. Kein Server nötig, solange nichts
zurückgeschrieben wird.

## Harte Regeln

- **Keine Fremdbibliotheken.** Alles ist Teil von Python. Ein Werkzeug,
  das in fünf Jahren noch laufen soll, darf nicht an einem Paket
  hängen, das es dann nicht mehr gibt. Dasselbe Versprechen wie bei der
  Friedensgruppe.
- **Alles auf Deutsch** — Funktionen, Felder, Variablen, Ausgaben. Auch
  im Code.
- **Textdateien sind die Wahrheit**, nicht eine Datenbank. `vorrat.md`
  und `rezepte/*.md` lassen sich in jedem Editor und in Obsidian öffnen
  und liegen in git.
- **`dist/` ist erzeugt**, wird nie von Hand bearbeitet.
- **Der Build meldet Probleme, statt sie zu verstecken.** Unbekannte
  Zutat, unbekannte Stufe, Rezept ohne Titel: Das kommt als Anmerkung
  auf die Konsole. Stillschweigend zu raten wäre schlimmer — ein
  Lebensmittel verschwände vom Zettel, ohne dass es jemand merkt.

## Die drei Stufen

`reichlich`, `knapp`, `alle`. **Mehr nicht, und keine Mengen.**

Das ist die wichtigste Entscheidung im ganzen Projekt. Wer Gramm
pflegen muss, pflegt nach drei Wochen gar nichts mehr, und dann ist der
Vorrat falsch — was schlimmer ist als grob. Bei Olivenöl, Linsen und
Dosentomaten zählt ohnehin nur, ob nachgekauft werden muss.

Daraus folgt: `knapp` heißt, man kann **heute noch kochen**. Nur `alle`
heißt fehlt. Diese Unterscheidung ist der ganze Zweck der drei Stufen.

Mengen in Rezepten (`Linsen – 250 g`) sind **nur für den Menschen**.
Für den Abgleich zählen sie nicht.

## Der Abgleich

Zutat und Vorratseintrag werden über `schluessel()` verglichen — klein
geschrieben, Umlaute ersetzt, Sonderzeichen weg. Deshalb trennt
Groß- und Kleinschreibung nicht, wohl aber ein anderer Name:
„Dosentomaten" und „Tomaten aus der Dose" sind zwei Dinge.

Steht eine Zutat nicht in `vorrat.md`, gilt sie als fehlend **und** der
Build meldet es. Dann gibt es zwei richtige Antworten: Namen angleichen
oder das Lebensmittel aufnehmen.

## Mediterran heißt hier

Das Muster, nicht einzelne Gerichte (Grundlage: `Mealcraft/formen/
Mediterrane Kost.md`):

- **Olivenöl** als hauptsächliches Fett
- viel **Gemüse, Hülsenfrüchte, Nüsse, Vollkorn**
- **Fisch** regelmäßig, **Geflügel** mäßig
- **rotes und verarbeitetes Fleisch** selten
- **Milchprodukte** mäßig, eher Käse und Joghurt
- wenig Zucker, wenig Hochverarbeitetes

Für neue Rezepte heißt das: Hülsenfrüchte und Gemüse tragen das
Gericht, Fleisch ist die Ausnahme. Kein Rezept braucht eine
Begründung — aber wenn zwanzig Rezepte da sind und fünfzehn haben
Fleisch als Hauptsache, stimmt etwas nicht.

## Verhältnis zu Mealcraft

**Getrennte Projekte, mit Absicht.** In `Mealcraft/LIESMICH.md` steht,
dass Rezepte „eine andere Sache" sind und einen zweiten Ordner bekommen.
Das hier ist dieser zweite.

- **Mealcraft** = Wissen. Was der Körper braucht, mit Quelle, `Stand:`
  und Sicherheitsgrad.
- **Tavernio** = Küche. Was da ist und wie es gekocht wird.

Kein Ernährungswissen in Rezepte schreiben. Wer wissen will, warum
Hülsenfrüchte gut sind, liest es dort — mit Quelle, nicht als
Behauptung in einem Kochtext.

## Aufbau

```
vorrat.md            Der Bestand. Die eine Datei, die oft angefasst wird.
rezepte/*.md         Eine Datei je Rezept, Form in rezepte/LIESMICH.md
vorlagen/stil.css    Das einzige Stylesheet
build.py             Baut dist/
tests/               unittest, ohne Fremdbibliotheken
dist/                Erzeugt. Nicht bearbeiten.
```

## Warum `vorrat.md` eine einzige Datei ist

Naheliegend wäre eine Datei je Lebensmittel, wie die Notizen in den
Tresoren. Für **Zustand, der sich wöchentlich ändert**, ist das falsch:
Vierzig Dateien zu öffnen, um Stufen zu setzen, macht niemand zweimal.
Eine Tabelle ist in Sekunden gepflegt und zeigt im git-Diff genau, was
sich geändert hat.

Rezepte sind das Gegenteil — sie sind Dokumente und ändern sich selten.
Deshalb dort eine Datei je Stück.

## Noch nicht gebaut

- **Abhaken auf dem Handy.** Dafür braucht es ein kleines PHP auf dem
  Webspace, das in eine Datei zurückschreibt — wie `kommentare/` und
  `abstimmung/` bei der Friedensgruppe. Bis dahin ist der Zettel eine
  Leseliste.
- **`hochladen.py`.** Kann von der Friedensgruppe übernommen werden
  (FTPS, `zugang.json`, Passwort aus der Umgebung).
- **Mindesthaltbarkeit für Frisches.** Bewusst zurückgestellt: erst
  soll sich zeigen, ob die drei Stufen im Alltag durchhalten.
