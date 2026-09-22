#!/usr/bin/env python3
"""Baut aus `vorrat.md` und `rezepte/` die Seiten in `dist/`.

Aufruf:  python build.py              baut
         python build.py --pruefen    prüft nur, schreibt nichts

Keine Fremdbibliotheken. Alles, was hier gebraucht wird, ist Teil von
Python — dasselbe Versprechen wie bei der Friedensgruppe, und aus
demselben Grund: Ein Werkzeug, das in fünf Jahren noch laufen soll,
darf nicht an einer Abhängigkeit hängen, die es dann nicht mehr gibt.
"""
import html
import os
import re
import sys
import unicodedata
from datetime import date

# Die Windows-Konsole spricht von Haus aus cp1252 und bricht über dem
# ersten Pfeil ab. Dieselbe Zeile steht aus demselben Grund in build.py
# der Friedensgruppe.
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

HIER = os.path.dirname(os.path.abspath(__file__))
VORRAT = os.path.join(HIER, 'vorrat.md')
REZEPTE = os.path.join(HIER, 'rezepte')
VORLAGEN = os.path.join(HIER, 'vorlagen')
ZIEL = os.path.join(HIER, 'dist')

# Die drei Stufen. Mehr wären eine Scheingenauigkeit: Wer zwischen
# „reichlich" und „eher reichlich" unterscheiden soll, pflegt nach drei
# Wochen gar nichts mehr.
STUFEN = ('reichlich', 'knapp', 'alle')
FEHLT = ('knapp', 'alle')

MONATE = ('Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli',
          'August', 'September', 'Oktober', 'November', 'Dezember')

# Die Reihenfolge der Gruppen auf dem Einkaufszettel. Sie folgt grob dem
# Weg durch den Laden – Frisches zuerst, Haltbares zuletzt –, damit man
# nicht dreimal durch denselben Gang läuft.
GRUPPEN_FOLGE = ('Gemüse', 'Kräuter', 'Obst', 'Fisch', 'Milchprodukte',
                 'Getreide', 'Hülsenfrüchte', 'Konserven', 'Nüsse',
                 'Fett', 'Säure', 'Gewürze')


# ================================================================
#  Lesen
# ================================================================

def slug(text):
    """Dateiname aus einem Titel. Umlaute vor dem Zerlegen ersetzen,
    sonst zerfällt „ü" in u + Pünktchen und wird zu „u"."""
    text = (text.replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue')
                .replace('Ä', 'Ae').replace('Ö', 'Oe').replace('Ü', 'Ue')
                .replace('ß', 'ss'))
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(z for z in text if not unicodedata.combining(z))
    text = re.sub(r'[^A-Za-z0-9]+', '-', text).strip('-').lower()
    return text or 'ohne-namen'


def schluessel(name):
    """Womit eine Zutat und ein Vorratseintrag verglichen werden.

    Groß- und Kleinschreibung und Leerzeichen sollen nicht darüber
    entscheiden, ob „Dosentomaten" gefunden wird.
    """
    return slug(name.strip())


def vorrat_lesen(meldungen):
    """Liest alle vierspaltigen Tabellen aus `vorrat.md`.

    **Vier Spalten sind das Erkennungszeichen.** Die Datei erklärt oben
    die Stufen in einer zweispaltigen Tabelle; würde die mitgelesen,
    stünde „reichlich" als Lebensmittel im Vorrat.
    """
    if not os.path.exists(VORRAT):
        sys.exit(f'{VORRAT} fehlt. Ohne Vorrat gibt es nichts zu bauen.')
    with open(VORRAT, encoding='utf-8') as f:
        zeilen = f.read().split('\n')

    vorrat = {}
    for nr, zeile in enumerate(zeilen, 1):
        roh = zeile.strip()
        if not roh.startswith('|') or not roh.endswith('|'):
            continue
        zellen = [z.strip() for z in roh[1:-1].split('|')]
        if len(zellen) != 4:
            continue
        if set(''.join(zellen)) <= set('-: '):
            continue                      # die Trennzeile unter dem Kopf
        name, gruppe, stufe, notiz = zellen
        if name.lower() == 'lebensmittel':
            continue                      # die Kopfzeile selbst
        if not name:
            continue

        if stufe.lower() not in STUFEN:
            meldungen.append(
                f'vorrat.md, Zeile {nr}: „{stufe}" ist keine Stufe. '
                f'Erlaubt sind {", ".join(STUFEN)}. Der Eintrag '
                f'„{name}" wird als „alle" behandelt.')
            stufe = 'alle'

        k = schluessel(name)
        if k in vorrat:
            meldungen.append(
                f'vorrat.md, Zeile {nr}: „{name}" steht schon weiter '
                'oben. Die zweite Zeile gewinnt – gemeint ist das '
                'selten.')
        vorrat[k] = {'name': name, 'gruppe': gruppe or 'Sonstiges',
                     'stufe': stufe.lower(), 'notiz': notiz, 'zeile': nr}
    if not vorrat:
        sys.exit('In vorrat.md steht keine Tabelle mit vier Spalten.')
    return vorrat


def frontmatter_lesen(text):
    """Trennt den Kopf vom Text. Kein YAML – nur `schlüssel: wert` und
    Listen als `- eintrag`."""
    if not text.startswith('---'):
        return {}, text
    ende = text.find('\n---', 3)
    if ende < 0:
        return {}, text
    kopf, rest = text[3:ende].strip('\n'), text[ende + 4:].lstrip('\n')

    daten, letzter = {}, None
    for zeile in kopf.split('\n'):
        if not zeile.strip() or zeile.lstrip().startswith('#'):
            continue
        if zeile.lstrip().startswith('- ') and letzter:
            daten.setdefault(letzter, [])
            if isinstance(daten[letzter], list):
                daten[letzter].append(zeile.lstrip()[2:].strip())
            continue
        if ':' not in zeile:
            continue
        letzter, wert = zeile.split(':', 1)
        letzter, wert = letzter.strip(), wert.strip()
        daten[letzter] = wert if wert else []
    return daten, rest


def zutat_zerlegen(eintrag):
    """`Linsen – 250 g` wird zu („Linsen", „250 g").

    Die Menge steht hinter einem Gedankenstrich und ist für den
    Abgleich mit dem Vorrat ohne Bedeutung: Ob 250 g Linsen da sind,
    weiß niemand, und es zu behaupten wäre schlimmer als die grobe
    Auskunft, dass Linsen da sind.
    """
    for trenner in (' – ', ' - ', ' — '):
        if trenner in eintrag:
            name, menge = eintrag.split(trenner, 1)
            return name.strip(), menge.strip()
    return eintrag.strip(), ''


def rezepte_lesen(vorrat, meldungen):
    if not os.path.isdir(REZEPTE):
        return []
    rezepte = []
    for datei in sorted(os.listdir(REZEPTE)):
        if not datei.endswith('.md') or datei.lower() == 'liesmich.md':
            continue
        pfad = os.path.join(REZEPTE, datei)
        with open(pfad, encoding='utf-8') as f:
            kopf, rumpf = frontmatter_lesen(f.read())

        titel = str(kopf.get('titel') or '').strip()
        if not titel:
            meldungen.append(f'rezepte/{datei}: kein `titel:` im Kopf. '
                             'Die Datei wird übergangen.')
            continue

        zutaten = []
        for eintrag in (kopf.get('zutaten') or []):
            name, menge = zutat_zerlegen(str(eintrag))
            if not name:
                continue
            k = schluessel(name)
            if k not in vorrat:
                meldungen.append(
                    f'rezepte/{datei}: „{name}" steht nicht in '
                    'vorrat.md. Solange nicht, gilt die Zutat als '
                    'fehlend und landet auf dem Zettel.')
            zutaten.append({'name': name, 'menge': menge, 'k': k})

        if not zutaten:
            meldungen.append(f'rezepte/{datei}: keine `zutaten:`. '
                             'Dann lässt sich nichts abgleichen.')

        rezepte.append({
            'titel': titel,
            'datei': datei,
            'adresse': f'rezepte/{slug(titel)}.html',
            'kurz': str(kopf.get('kurz') or '').strip(),
            'dauer': str(kopf.get('dauer') or '').strip(),
            'portionen': str(kopf.get('portionen') or '').strip(),
            'geplant': str(kopf.get('geplant') or '').lower() in ('ja', 'yes', '1'),
            'zutaten': zutaten,
            'rumpf': rumpf,
        })
    return rezepte


# ================================================================
#  Abgleich
# ================================================================

def lage(rezept, vorrat):
    """Was fehlt, was wird knapp.

    `alle` und unbekannt heißt fehlt; `knapp` heißt: reicht vielleicht,
    aber es wäre gut, daran zu denken. Die Unterscheidung ist der ganze
    Zweck der drei Stufen — ein Rezept, für das nur etwas knapp ist,
    kann man heute noch kochen.
    """
    fehlend, knapp = [], []
    for z in rezept['zutaten']:
        eintrag = vorrat.get(z['k'])
        if eintrag is None or eintrag['stufe'] == 'alle':
            fehlend.append(z)
        elif eintrag['stufe'] == 'knapp':
            knapp.append(z)
    return fehlend, knapp


def einkaufszettel(vorrat, rezepte):
    """Was auf den Zettel gehört, und warum.

    Zwei Quellen: Was im Regal zur Neige geht, und was für die
    geplanten Rezepte fehlt. Der Grund wird mitgeführt — vor dem Regal
    stehend will man wissen, ob man das Glas Kapern für den Dienstag
    braucht oder nur, weil es fast leer ist.
    """
    posten = {}
    for k, e in vorrat.items():
        if e['stufe'] in FEHLT:
            posten[k] = {'name': e['name'], 'gruppe': e['gruppe'],
                         'stufe': e['stufe'], 'gruende': []}
            if e['stufe'] == 'alle':
                posten[k]['gruende'].append('aufgebraucht')
            else:
                posten[k]['gruende'].append('geht zur Neige')

    for r in rezepte:
        if not r['geplant']:
            continue
        fehlend, knapp = lage(r, vorrat)
        for z in fehlend + knapp:
            e = vorrat.get(z['k'])
            posten.setdefault(z['k'], {
                'name': z['name'],
                'gruppe': e['gruppe'] if e else 'Noch nicht im Vorrat',
                'stufe': e['stufe'] if e else 'alle',
                'gruende': []})
            posten[z['k']]['gruende'].append(f'für {r["titel"]}')

    nach_gruppe = {}
    for p in posten.values():
        nach_gruppe.setdefault(p['gruppe'], []).append(p)
    for liste in nach_gruppe.values():
        liste.sort(key=lambda p: p['name'].lower())

    def rang(gruppe):
        return (GRUPPEN_FOLGE.index(gruppe)
                if gruppe in GRUPPEN_FOLGE else len(GRUPPEN_FOLGE))
    return sorted(nach_gruppe.items(), key=lambda g: (rang(g[0]), g[0]))


# ================================================================
#  Markdown → HTML, so viel wie hier gebraucht wird
# ================================================================

def md_zu_html(text):
    aus, liste, absatz = [], False, []

    def absatz_schliessen():
        if absatz:
            aus.append('<p>' + inline(' '.join(absatz)) + '</p>')
            absatz.clear()

    def liste_schliessen():
        nonlocal liste
        if liste:
            aus.append('</ol>' if liste == 'ol' else '</ul>')
            liste = False

    for zeile in text.split('\n'):
        roh = zeile.strip()
        if not roh:
            absatz_schliessen()
            liste_schliessen()
            continue
        if roh.startswith('## '):
            absatz_schliessen()
            liste_schliessen()
            aus.append(f'<h2>{inline(roh[3:])}</h2>')
            continue
        nummer = re.match(r'(\d+)\.\s+(.*)', roh)
        if nummer:
            absatz_schliessen()
            if liste != 'ol':
                liste_schliessen()
                aus.append('<ol>')
                liste = 'ol'
            aus.append(f'<li>{inline(nummer.group(2))}</li>')
            continue
        if roh.startswith('- '):
            absatz_schliessen()
            if liste != 'ul':
                liste_schliessen()
                aus.append('<ul>')
                liste = 'ul'
            aus.append(f'<li>{inline(roh[2:])}</li>')
            continue
        liste_schliessen()
        absatz.append(roh)
    absatz_schliessen()
    liste_schliessen()
    return '\n'.join(aus)


def inline(text):
    text = html.escape(text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', text)
    return text


# ================================================================
#  Seiten
# ================================================================

def rahmen(titel, inhalt, hoch='', aktiv=''):
    def knopf(ziel, name, kennung):
        hier = ' class="hier"' if kennung == aktiv else ''
        return f'<a href="{hoch}{ziel}"{hier}>{name}</a>'

    navigation = ' '.join([
        knopf('index.html', 'Heute', 'heute'),
        knopf('zettel.html', 'Einkauf', 'zettel'),
        knopf('vorrat.html', 'Vorrat', 'vorrat'),
        knopf('rezepte.html', 'Rezepte', 'rezepte'),
    ])
    return f'''<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>{html.escape(titel)} – Tavernio</title>
<link rel="stylesheet" href="{hoch}stil.css">
</head>
<body>
<header><a class="marke" href="{hoch}index.html">Tavernio</a>
<nav>{navigation}</nav></header>
<main>
{inhalt}
</main>
<footer>Gebaut am {date.today().day}. {MONATE[date.today().month - 1]}
{date.today().year}</footer>
</body>
</html>
'''


def stufe_punkt(stufe):
    return f'<span class="punkt {stufe}" title="{stufe}"></span>'


def seite_heute(rezepte, vorrat):
    reihen = []
    for r in rezepte:
        fehlend, knapp = lage(r, vorrat)
        reihen.append((len(fehlend), len(knapp), r, fehlend, knapp))
    reihen.sort(key=lambda z: (z[0], z[1], z[2]['titel'].lower()))

    teile = ['<h1>Was geht heute?</h1>']
    geplant = [r for r in rezepte if r['geplant']]
    if geplant:
        teile.append('<p class="hinweis">Geplant: '
                     + ', '.join(f'<a href="{r["adresse"]}">'
                                 f'{html.escape(r["titel"])}</a>'
                                 for r in geplant) + '</p>')
    if not reihen:
        teile.append('<p class="leer">Noch kein Rezept da. '
                     'Die Vorlage liegt in <code>rezepte/</code>.</p>')
    teile.append('<ul class="rezeptliste">')
    for anzahl_fehlt, _, r, fehlend, knapp in reihen:
        if anzahl_fehlt == 0:
            lagebild = ('<span class="gut">alles da</span>' if not knapp
                        else '<span class="mittel">alles da, knapp wird: '
                             + ', '.join(html.escape(z['name']) for z in knapp)
                             + '</span>')
        else:
            lagebild = ('<span class="schlecht">es fehlt: '
                        + ', '.join(html.escape(z['name']) for z in fehlend)
                        + '</span>')
        dauer = f' · {html.escape(r["dauer"])} min' if r['dauer'] else ''
        teile.append(
            f'<li><a href="{r["adresse"]}">{html.escape(r["titel"])}</a>'
            f'<span class="neben">{dauer}</span><br>{lagebild}</li>')
    teile.append('</ul>')
    return rahmen('Heute', '\n'.join(teile), aktiv='heute')


def seite_zettel(zettel):
    teile = ['<h1>Einkaufszettel</h1>']
    if not zettel:
        teile.append('<p class="leer">Nichts zu kaufen. '
                     'Alles steht auf <em>reichlich</em>.</p>')
    for gruppe, posten in zettel:
        teile.append(f'<h2>{html.escape(gruppe)}</h2><ul class="zettel">')
        for p in posten:
            gruende = ' · '.join(dict.fromkeys(p['gruende']))
            teile.append(
                f'<li>{stufe_punkt(p["stufe"])}'
                f'<span class="was">{html.escape(p["name"])}</span>'
                f'<span class="warum">{html.escape(gruende)}</span></li>')
        teile.append('</ul>')
    teile.append('<p class="hinweis">Abhaken geht hier noch nicht – '
                 'dafür fehlt der Teil auf dem Server. Bis dahin: '
                 'Stufe in <code>vorrat.md</code> ändern und neu bauen.</p>')
    return rahmen('Einkauf', '\n'.join(teile), aktiv='zettel')


def seite_vorrat(vorrat):
    nach_gruppe = {}
    for e in vorrat.values():
        nach_gruppe.setdefault(e['gruppe'], []).append(e)

    def rang(gruppe):
        return (GRUPPEN_FOLGE.index(gruppe)
                if gruppe in GRUPPEN_FOLGE else len(GRUPPEN_FOLGE))

    teile = ['<h1>Vorrat</h1>']
    gezaehlt = {s: sum(1 for e in vorrat.values() if e['stufe'] == s)
                for s in STUFEN}
    teile.append(f'<p class="hinweis">{len(vorrat)} Dinge · '
                 f'{gezaehlt["reichlich"]} reichlich · '
                 f'{gezaehlt["knapp"]} knapp · {gezaehlt["alle"]} alle</p>')
    for gruppe, eintraege in sorted(nach_gruppe.items(),
                                    key=lambda g: (rang(g[0]), g[0])):
        teile.append(f'<h2>{html.escape(gruppe)}</h2><ul class="vorratsliste">')
        for e in sorted(eintraege, key=lambda e: e['name'].lower()):
            notiz = (f'<span class="warum">{html.escape(e["notiz"])}</span>'
                     if e['notiz'] else '')
            teile.append(f'<li>{stufe_punkt(e["stufe"])}'
                         f'<span class="was">{html.escape(e["name"])}</span>'
                         f'{notiz}</li>')
        teile.append('</ul>')
    return rahmen('Vorrat', '\n'.join(teile), aktiv='vorrat')


def seite_rezepte(rezepte, vorrat):
    teile = ['<h1>Rezepte</h1>']
    if not rezepte:
        teile.append('<p class="leer">Noch keines da.</p>')
    teile.append('<ul class="rezeptliste">')
    for r in sorted(rezepte, key=lambda r: r['titel'].lower()):
        fehlend, _ = lage(r, vorrat)
        marke = ('<span class="gut">alles da</span>' if not fehlend
                 else f'<span class="schlecht">{len(fehlend)} fehlt</span>')
        kurz = f'<br><span class="neben">{html.escape(r["kurz"])}</span>' if r['kurz'] else ''
        teile.append(f'<li><a href="{r["adresse"]}">'
                     f'{html.escape(r["titel"])}</a> {marke}{kurz}</li>')
    teile.append('</ul>')
    return rahmen('Rezepte', '\n'.join(teile), aktiv='rezepte')


def seite_rezept(r, vorrat):
    fehlend, knapp = lage(r, vorrat)
    fehlend_k = {z['k'] for z in fehlend}
    knapp_k = {z['k'] for z in knapp}

    teile = [f'<h1>{html.escape(r["titel"])}</h1>']
    angaben = []
    if r['dauer']:
        angaben.append(f'{html.escape(r["dauer"])} Minuten')
    if r['portionen']:
        angaben.append(f'{html.escape(r["portionen"])} Portionen')
    if r['geplant']:
        angaben.append('<strong>geplant</strong>')
    if angaben:
        teile.append('<p class="hinweis">' + ' · '.join(angaben) + '</p>')
    if r['kurz']:
        teile.append(f'<p class="kurz">{html.escape(r["kurz"])}</p>')

    teile.append('<h2>Zutaten</h2><ul class="zutaten">')
    for z in r['zutaten']:
        if z['k'] in fehlend_k:
            stufe, wort = 'alle', 'fehlt'
        elif z['k'] in knapp_k:
            stufe, wort = 'knapp', 'knapp'
        else:
            stufe, wort = 'reichlich', ''
        menge = f'<span class="menge">{html.escape(z["menge"])}</span>' if z['menge'] else ''
        marke = f'<span class="warum">{wort}</span>' if wort else ''
        teile.append(f'<li>{stufe_punkt(stufe)}'
                     f'<span class="was">{html.escape(z["name"])}</span>'
                     f'{menge}{marke}</li>')
    teile.append('</ul>')

    if fehlend:
        teile.append('<p class="schlecht">Zum Kochen fehlt: '
                     + ', '.join(html.escape(z['name']) for z in fehlend)
                     + '.</p>')
    else:
        teile.append('<p class="gut">Alles da.</p>')

    if r['rumpf'].strip():
        teile.append(md_zu_html(r['rumpf']))
    return rahmen(r['titel'], '\n'.join(teile), hoch='../', aktiv='rezepte')


# ================================================================
#  Bauen
# ================================================================

def schreiben(pfad, inhalt):
    voll = os.path.join(ZIEL, pfad.replace('/', os.sep))
    os.makedirs(os.path.dirname(voll), exist_ok=True)
    with open(voll, 'w', encoding='utf-8', newline='\n') as f:
        f.write(inhalt)


def bauen(pruefen_nur=False):
    meldungen = []
    vorrat = vorrat_lesen(meldungen)
    rezepte = rezepte_lesen(vorrat, meldungen)
    zettel = einkaufszettel(vorrat, rezepte)

    seiten = [
        ('index.html', seite_heute(rezepte, vorrat)),
        ('zettel.html', seite_zettel(zettel)),
        ('vorrat.html', seite_vorrat(vorrat)),
        ('rezepte.html', seite_rezepte(rezepte, vorrat)),
    ]
    for r in rezepte:
        seiten.append((r['adresse'], seite_rezept(r, vorrat)))

    if not pruefen_nur:
        for pfad, inhalt in seiten:
            schreiben(pfad, inhalt)
        quelle = os.path.join(VORLAGEN, 'stil.css')
        if os.path.exists(quelle):
            with open(quelle, encoding='utf-8') as f:
                schreiben('stil.css', f.read())

    if meldungen:
        print('Anmerkungen:')
        for m in meldungen:
            print(f'  ⚠️  {m}')
    posten = sum(len(p) for _, p in zettel)
    if pruefen_nur:
        print(f'Geprüft: {len(vorrat)} Vorratsdinge, {len(rezepte)} Rezepte, '
              f'{len(meldungen)} Anmerkungen.')
    else:
        print(f'Gebaut → dist/ ({len(seiten)} Seiten)')
        print(f'  {len(vorrat)} Vorratsdinge, {len(rezepte)} Rezepte, '
              f'{posten} auf dem Zettel')
    return 0


if __name__ == '__main__':
    sys.exit(bauen('--pruefen' in sys.argv))
