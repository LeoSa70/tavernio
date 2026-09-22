"""Prüfungen für Tavernio.

Aufruf aus dem Projektordner:
    python -m unittest discover -s tests -t .
"""
import contextlib
import io as _io
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import build


class Grundlage(unittest.TestCase):
    """Jede Prüfung bekommt einen eigenen Ordner mit eigenem Vorrat."""

    def setUp(self):
        self.ordner = tempfile.mkdtemp()
        self.rezepte = os.path.join(self.ordner, 'rezepte')
        os.makedirs(self.rezepte)
        self.alt = (build.VORRAT, build.REZEPTE, build.ZIEL)
        build.VORRAT = os.path.join(self.ordner, 'vorrat.md')
        build.REZEPTE = self.rezepte
        build.ZIEL = os.path.join(self.ordner, 'dist')
        self.vorrat_schreiben([
            ('Linsen', 'Hülsenfrüchte', 'reichlich', ''),
            ('Fenchel', 'Gemüse', 'alle', ''),
            ('Olivenöl', 'Fett', 'knapp', 'natives extra'),
        ])

    def tearDown(self):
        build.VORRAT, build.REZEPTE, build.ZIEL = self.alt
        shutil.rmtree(self.ordner, ignore_errors=True)

    def vorrat_schreiben(self, zeilen, vorspann=''):
        text = [vorspann, '| Lebensmittel | Gruppe | Stufe | Notiz |',
                '|---|---|---|---|']
        for name, gruppe, stufe, notiz in zeilen:
            text.append(f'| {name} | {gruppe} | {stufe} | {notiz} |')
        with open(build.VORRAT, 'w', encoding='utf-8') as f:
            f.write('\n'.join(text) + '\n')

    def rezept_schreiben(self, name, kopf, rumpf='Text.'):
        with open(os.path.join(self.rezepte, name), 'w',
                  encoding='utf-8') as f:
            f.write(f'---\n{kopf}\n---\n\n{rumpf}\n')


class VorratLesen(Grundlage):

    def test_die_zeilen_werden_gelesen(self):
        m = []
        v = build.vorrat_lesen(m)
        self.assertEqual(len(v), 3)
        self.assertEqual(v['linsen']['stufe'], 'reichlich')
        self.assertEqual(v['olivenoel']['notiz'], 'natives extra')
        self.assertEqual(m, [])

    def test_die_zweispaltige_erklaerung_wird_uebergangen(self):
        """In vorrat.md steht oben eine Tabelle, die die Stufen erklärt.
        Würde sie mitgelesen, stünde „reichlich" als Lebensmittel da."""
        self.vorrat_schreiben(
            [('Linsen', 'Hülsenfrüchte', 'reichlich', '')],
            vorspann='| Stufe | heißt |\n|---|---|\n'
                     '| reichlich | ist da |\n| alle | fehlt |\n')
        v = build.vorrat_lesen([])
        self.assertEqual(list(v), ['linsen'])

    def test_eine_unbekannte_stufe_wird_gemeldet_und_gilt_als_alle(self):
        """Stillschweigend zu raten wäre schlimmer: Das Lebensmittel
        verschwände vom Zettel, ohne dass es jemand merkt."""
        self.vorrat_schreiben([('Linsen', 'Hülsenfrüchte', 'halbvoll', '')])
        m = []
        v = build.vorrat_lesen(m)
        self.assertEqual(v['linsen']['stufe'], 'alle')
        self.assertEqual(len(m), 1)
        self.assertIn('halbvoll', m[0])

    def test_ohne_tabelle_bricht_der_bau_ab(self):
        with open(build.VORRAT, 'w', encoding='utf-8') as f:
            f.write('# Vorrat\n\nNoch nichts.\n')
        with self.assertRaises(SystemExit):
            build.vorrat_lesen([])


class Zutaten(Grundlage):

    def test_die_menge_steht_hinter_dem_gedankenstrich(self):
        self.assertEqual(build.zutat_zerlegen('Linsen – 250 g'),
                         ('Linsen', '250 g'))
        self.assertEqual(build.zutat_zerlegen('Linsen - 250 g'),
                         ('Linsen', '250 g'))

    def test_ohne_menge_bleibt_der_name_stehen(self):
        self.assertEqual(build.zutat_zerlegen('  Salz  '), ('Salz', ''))

    def test_der_bindestrich_im_namen_trennt_nicht(self):
        """„Creme-fraiche" ist ein Name, keine Menge – getrennt wird nur
        am Gedankenstrich mit Leerzeichen ringsum."""
        self.assertEqual(build.zutat_zerlegen('Creme-fraiche'),
                         ('Creme-fraiche', ''))

    def test_eine_unbekannte_zutat_wird_gemeldet(self):
        self.rezept_schreiben('x.md', 'titel: X\nzutaten:\n  - Trüffel')
        m = []
        r = build.rezepte_lesen(build.vorrat_lesen([]), m)
        self.assertEqual(len(r), 1)
        self.assertTrue(any('Trüffel' in x for x in m))

    def test_gross_und_kleinschreibung_trennt_nicht(self):
        self.rezept_schreiben('x.md', 'titel: X\nzutaten:\n  - linsen')
        m = []
        build.rezepte_lesen(build.vorrat_lesen([]), m)
        self.assertEqual(m, [])


class Lage(Grundlage):

    def rezept(self, zutaten, geplant=False):
        kopf = 'titel: Topf\n'
        if geplant:
            kopf += 'geplant: ja\n'
        kopf += 'zutaten:\n' + '\n'.join(f'  - {z}' for z in zutaten)
        self.rezept_schreiben('topf.md', kopf)
        v = build.vorrat_lesen([])
        return build.rezepte_lesen(v, [])[0], v

    def test_was_alle_ist_fehlt(self):
        r, v = self.rezept(['Linsen', 'Fenchel'])
        fehlend, knapp = build.lage(r, v)
        self.assertEqual([z['name'] for z in fehlend], ['Fenchel'])
        self.assertEqual(knapp, [])

    def test_was_knapp_ist_fehlt_nicht(self):
        """Der ganze Zweck der drei Stufen: Knapp heißt, man kann heute
        noch kochen."""
        r, v = self.rezept(['Linsen', 'Olivenöl'])
        fehlend, knapp = build.lage(r, v)
        self.assertEqual(fehlend, [])
        self.assertEqual([z['name'] for z in knapp], ['Olivenöl'])

    def test_was_gar_nicht_im_vorrat_steht_fehlt(self):
        r, v = self.rezept(['Trüffel'])
        fehlend, _ = build.lage(r, v)
        self.assertEqual([z['name'] for z in fehlend], ['Trüffel'])


class Einkaufszettel(Grundlage):

    def zettel(self):
        v = build.vorrat_lesen([])
        r = build.rezepte_lesen(v, [])
        flach = {}
        for _, posten in build.einkaufszettel(v, r):
            for p in posten:
                flach[p['name']] = p
        return flach

    def test_knapp_und_alle_stehen_darauf_reichlich_nicht(self):
        z = self.zettel()
        self.assertIn('Fenchel', z)
        self.assertIn('Olivenöl', z)
        self.assertNotIn('Linsen', z)

    def test_der_grund_steht_dabei(self):
        z = self.zettel()
        self.assertIn('aufgebraucht', z['Fenchel']['gruende'])
        self.assertIn('geht zur Neige', z['Olivenöl']['gruende'])

    def test_ein_geplantes_rezept_bringt_seine_luecken_mit(self):
        self.rezept_schreiben(
            'topf.md', 'titel: Topf\ngeplant: ja\nzutaten:\n  - Fenchel')
        z = self.zettel()
        self.assertIn('für Topf', z['Fenchel']['gruende'])

    def test_ein_ungeplantes_rezept_bringt_nichts_mit(self):
        self.rezept_schreiben(
            'topf.md', 'titel: Topf\nzutaten:\n  - Trüffel')
        self.assertNotIn('Trüffel', self.zettel())

    def test_die_gruppen_stehen_in_der_reihenfolge_des_ladens(self):
        """Frisches zuerst, Haltbares zuletzt – sonst läuft man
        dreimal durch denselben Gang."""
        v = build.vorrat_lesen([])
        gruppen = [g for g, _ in build.einkaufszettel(v, [])]
        self.assertEqual(gruppen, ['Gemüse', 'Fett'])


class Bauen(Grundlage):

    def bauen_still(self, **kw):
        """Der Bau redet – in der Prüfungsausgabe stört das nur."""
        with contextlib.redirect_stdout(_io.StringIO()):
            return build.bauen(**kw)

    def test_der_bau_legt_die_seiten_an(self):
        self.rezept_schreiben(
            'topf.md', 'titel: Linsentopf\nzutaten:\n  - Linsen')
        self.bauen_still()
        for pfad in ('index.html', 'zettel.html', 'vorrat.html',
                     'rezepte.html', 'rezepte/linsentopf.html'):
            self.assertTrue(
                os.path.exists(os.path.join(build.ZIEL,
                                            pfad.replace('/', os.sep))),
                pfad)

    def test_pruefen_schreibt_nichts(self):
        self.bauen_still(pruefen_nur=True)
        self.assertFalse(os.path.exists(build.ZIEL))

    def test_ein_rezept_ohne_titel_wird_gemeldet_statt_gebaut(self):
        self.rezept_schreiben('ohne.md', 'zutaten:\n  - Linsen')
        m = []
        r = build.rezepte_lesen(build.vorrat_lesen([]), m)
        self.assertEqual(r, [])
        self.assertTrue(any('titel' in x for x in m))

    def test_die_liesmich_wird_kein_rezept(self):
        with open(os.path.join(self.rezepte, 'LIESMICH.md'), 'w',
                  encoding='utf-8') as f:
            f.write('# Rezepte\n\nErklärung.\n')
        self.assertEqual(build.rezepte_lesen(build.vorrat_lesen([]), []), [])


class Namen(unittest.TestCase):

    def test_umlaute_bleiben_lesbar(self):
        """Erst ersetzen, dann zerlegen – sonst zerfällt „ü" in u plus
        Pünktchen und wird zu „u"."""
        self.assertEqual(build.slug('Ofengemüse'), 'ofengemuese')
        self.assertEqual(build.slug('Weiße Bohnen'), 'weisse-bohnen')

    def test_aus_dem_titel_wird_ein_dateiname(self):
        self.assertEqual(build.slug('Pasta alla Puttanesca'),
                         'pasta-alla-puttanesca')


if __name__ == '__main__':
    unittest.main()
