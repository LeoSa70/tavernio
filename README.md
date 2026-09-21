# Speisekammer

Vorrat, Einkauf und Rezepte für zwei Personen — mediterran gekocht.

Drei Fragen, drei Seiten: **Was ist da? Was muss gekauft werden? Was
koche ich heute daraus?**

## Loslegen

```
python build.py
```

Danach `dist/index.html` im Browser öffnen. Mehr braucht es nicht —
keine Installation, keine Pakete, kein Server.

## Der Alltag

**Etwas ist alle oder wird knapp** → in [`vorrat.md`](vorrat.md) die
Stufe ändern, neu bauen. Drei Stufen, mehr gibt es nicht:

| Stufe | heißt |
|---|---|
| `reichlich` | ist da, reicht eine Weile |
| `knapp` | geht zur Neige, beim nächsten Einkauf mitnehmen |
| `alle` | aufgebraucht, fehlt |

Gezählt wird nicht. Wer Gramm pflegen muss, pflegt nach drei Wochen gar
nichts mehr — und ein falscher Vorrat ist schlimmer als ein grober.

**Ein neues Rezept** → eine Datei in [`rezepte/`](rezepte/) anlegen.
Die Form steht in [`rezepte/LIESMICH.md`](rezepte/LIESMICH.md). Die
eine Regel, auf die es ankommt: Die Zutat muss genauso heißen wie in
`vorrat.md`, sonst findet der Abgleich sie nicht. Der Build sagt es,
wenn etwas nicht zusammenpasst.

**Kochen planen** → im Rezept `geplant: ja` setzen. Was dafür fehlt,
steht danach auf dem Einkaufszettel, mit dem Rezept als Grund dabei.

## Was die Seiten zeigen

**Heute** — alle Rezepte, sortiert danach, wie viel fehlt. Oben steht,
was sich ohne Einkauf kochen lässt.

**Einkauf** — was zur Neige geht und was für geplante Rezepte fehlt,
gruppiert in der Reihenfolge des Ladens: Frisches zuerst, Haltbares
zuletzt. Neben jedem Posten steht, warum er draufsteht.

**Vorrat** — der ganze Bestand nach Gruppen, mit einem Punkt für die
Stufe.

**Rezepte** — alle, mit dem Hinweis, ob alles da ist.

## Prüfen

```
python build.py --pruefen                   nur prüfen, nichts schreiben
python -m unittest discover -s tests -t .   die Prüfungen (23)
```

## Was noch fehlt

**Abhaken im Laden.** Der Zettel ist bisher eine Leseliste; zum
Abhaken auf dem Handy braucht es ein kleines PHP auf dem Webspace, das
zurückschreibt — wie Kommentare und Terminabstimmung bei der
Friedensgruppe.

**Hochladen.** `hochladen.py` lässt sich von dort übernehmen.

**Mindesthaltbarkeit für Frisches.** Absichtlich zurückgestellt: Erst
soll sich zeigen, ob die drei Stufen im Alltag durchhalten. Wenn
Gemüse regelmäßig verdirbt, weil nur „reichlich" dasteht, kommt das
Datum dazu.

## Ist kein Ernährungsratgeber

Warum Hülsenfrüchte gut sind und was an Olivenöl dran ist, steht im
**Mealcraft**-Tresor — mit Quelle, Stand und Sicherheitsgrad. Hier
steht, was im Schrank ist und wie es gekocht wird.
