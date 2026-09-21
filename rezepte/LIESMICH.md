# Rezepte

Eine Datei je Rezept. Diese hier wird nie zu einer Seite — der Build
überspringt jede `LIESMICH.md`.

## Der Kopf

```yaml
---
titel: Linsen-Fenchel-Topf
kurz: Ein Satz, der neugierig macht.
dauer: 40
portionen: 4
geplant: ja
zutaten:
  - Linsen – 250 g
  - Fenchel – 2 Knollen
  - Olivenöl
---
```

| Feld | wofür |
|---|---|
| `titel` | Überschrift, und der Dateiname der Seite kommt daraus |
| `kurz` | ein Satz für die Übersicht |
| `dauer` | Minuten, nur die Zahl |
| `portionen` | nur die Zahl |
| `geplant` | `ja` setzt das Rezept auf den Einkaufszettel |
| `zutaten` | eine je Zeile, Menge hinter einem Gedankenstrich |

## Die eine Regel, auf die es ankommt

**Der Name vor dem Gedankenstrich muss genauso in `vorrat.md` stehen.**
Daran hängt der ganze Abgleich. Steht im Rezept „Dosentomaten" und im
Vorrat „Tomaten aus der Dose", gelten sie als zwei Dinge, und das
Rezept sieht aus, als fehlte etwas.

Der Build sagt es, wenn eine Zutat unbekannt ist. Dann gibt es zwei
richtige Antworten: den Namen angleichen — oder das Lebensmittel in
`vorrat.md` aufnehmen, weil es dort fehlte.

Die **Menge** hinter dem Gedankenstrich ist nur für den Menschen. Für
den Abgleich zählt sie nicht: Ob 250 g Linsen da sind, weiß der Vorrat
nicht, und so zu tun als ob wäre schlimmer als die grobe Auskunft, dass
Linsen da sind.

## Der Text darunter

Was nach dem zweiten `---` steht, ist das Rezept selbst. `## Überschrift`,
nummerierte Schritte, Aufzählungen, `**fett**` und `*kursiv*` werden
umgesetzt — mehr nicht, und mehr braucht ein Rezept auch nicht.

## Was hier nicht hineingehört

**Ernährungswissen.** Warum Hülsenfrüchte gut sind, was an Olivenöl
dran ist, wie viel Eiweiß der Körper braucht — das steht im
Mealcraft-Tresor und hat dort seine Quellen und seinen Sicherheitsgrad.
Hier steht, wie es gekocht wird.

**Mengen, die niemand nachkocht.** Wenn eine Zutat nur in einem Rezept
vorkommt und sonst nie, gehört sie vielleicht trotzdem in `vorrat.md` —
aber dann als das, was sie ist: etwas, das man für dieses eine Gericht
kauft.
