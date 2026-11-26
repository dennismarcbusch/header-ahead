"""Druckteile für Header Ahead, parametrisch mit build123d.

Jede Funktion liefert ein Teil-Objekt mit zwei Körpern:
  koerper  – das Teil mit 0,6 mm vertiefter Schrift (allein druckbar, einfarbig)
  schrift  – die Schrift als eigener Körper, der die Vertiefung füllt (zweite Farbe)
"""

from dataclasses import dataclass, field
from pathlib import Path

from build123d import (
    Align, Axis, Box, Circle, Cylinder, Part, Polygon, Pos, Rectangle,
    RectangleRounded, Rot, Text, chamfer, extrude, mirror, Plane,
)

from masse import *  # noqa: F401,F403

SCHRIFTDATEI = "/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-ExtraBold.ttf"
if not Path(SCHRIFTDATEI).exists():  # anderer Rechner: Schrift über den Namen suchen
    SCHRIFTDATEI = None

MIN3 = (Align.MIN, Align.MIN, Align.MIN)
MITTE = (Align.CENTER, Align.CENTER)


# --- Hilfen -------------------------------------------------------------------

def quader(x0, y0, z0, x1, y1, z1):
    return Pos(x0, y0, z0) * Box(x1 - x0, y1 - y0, z1 - z0, align=MIN3)


def rundquader(x0, y0, z0, x1, y1, z1, r):
    skizze = Pos((x0 + x1) / 2, (y0 + y1) / 2) * RectangleRounded(x1 - x0, y1 - y0, r)
    return Pos(0, 0, z0) * extrude(skizze, z1 - z0)


def schriftskizze(text, groesse, max_breite=None):
    def setze(g):
        if SCHRIFTDATEI:
            return Text(text, font_size=g, font_path=SCHRIFTDATEI, align=MITTE)
        return Text(text, font_size=g, font="JetBrains Mono", align=MITTE)

    skizze = setze(groesse)
    if max_breite:
        breite = skizze.bounding_box().size.X
        if breite > max_breite:
            skizze = setze(groesse * max_breite / breite)
    return skizze


@dataclass
class Teil:
    name: str
    koerper: Part
    schrift: Part | None = None
    farbe: str = "hellgrau"          # Filamentfarbe des Körpers
    schriftfarbe: str = "schwarz"
    anzahl: int = 1
    hinweis: str = ""
    kopfueber: bool = False          # mit der Oberseite nach unten drucken
    extra: dict = field(default_factory=dict)

    def beschrifte(self, text, x, y, z_oben, groesse, max_breite=None, drehung=0,
                   unten=False):
        """Legt Schrift bündig in die Fläche bei z_oben (oder in die Unterseite)."""
        skizze = schriftskizze(text, groesse, max_breite)
        if unten:
            skizze = mirror(skizze, Plane.YZ)
        if drehung:
            skizze = Rot(0, 0, drehung) * skizze
        z0 = z_oben if unten else z_oben - SCHRIFT_T
        koerper = extrude(Pos(x, y, z0) * skizze, SCHRIFT_T)
        self.koerper = self.koerper - koerper
        self.schrift = koerper if self.schrift is None else self.schrift + koerper
        return self

    def beschrifte_paar(self, gross, klein, x_mitte, y_mitte, z_oben, g_gross, g_klein, abstand=2.2):
        """Große Nummer links, kleinerer Name rechts daneben, beide auf einer Grundlinie."""
        b_gross = schriftskizze(gross, g_gross).bounding_box().size
        b_klein = schriftskizze(klein, g_klein).bounding_box().size
        x0 = x_mitte - (b_gross.X + abstand + b_klein.X) / 2
        y0 = y_mitte - b_gross.Y / 2
        self.beschrifte(gross, x0 + b_gross.X / 2, y0 + b_gross.Y / 2, z_oben, g_gross)
        self.beschrifte(klein, x0 + b_gross.X + abstand + b_klein.X / 2, y0 + b_klein.Y / 2, z_oben, g_klein)
        return self

    def beschrifte_zeilen(self, zeilen, x_mitte, y_oben, z_oben, groesse, zeilenabstand):
        """Mehrere Zeilen linksbündig untereinander, als Block um x_mitte zentriert."""
        breiten = [schriftskizze(z, groesse).bounding_box().size.X for z in zeilen]
        x_links = x_mitte - max(breiten) / 2
        for i, (zeile, breite) in enumerate(zip(zeilen, breiten)):
            self.beschrifte(zeile, x_links + breite / 2, y_oben - i * zeilenabstand, z_oben, groesse)
        return self


def fase_oben_unten(koerper, oben=0.5, unten=0.5):
    """Bricht die Kanten der Ober- und Unterseite. Schlägt die Fase fehl, bleibt das Teil kantig."""
    try:
        kanten = koerper.edges().group_by(Axis.Z)
        if unten:
            koerper = chamfer(kanten[0], unten)
        if oben:
            koerper = chamfer(koerper.edges().group_by(Axis.Z)[-1], oben)
    except Exception:
        pass
    return koerper


def fach(x0, y_kante, richtung, z_oben, laenge=FACH_L, breite=FACH_B):
    """Schnittkörper für ein Plättchenfach, das zur Außenseite hin offen ist.

    richtung -1: offen nach vorn (Außenfläche bei y_kante), +1: offen nach hinten.
    Eine niedrige Lippe hält das Plättchen, der Rest der Seite bleibt frei zum Greifen.
    """
    z_boden = z_oben - FACH_T
    if richtung < 0:
        tasche = quader(x0, y_kante + LIPPE_B, z_boden, x0 + laenge, y_kante + LIPPE_B + breite, z_oben + 1)
        maul = quader(x0, y_kante - 1, z_boden + LIPPE_H, x0 + laenge, y_kante + LIPPE_B + 0.01, z_oben + 1)
    else:
        tasche = quader(x0, y_kante - LIPPE_B - breite, z_boden, x0 + laenge, y_kante - LIPPE_B, z_oben + 1)
        maul = quader(x0, y_kante - LIPPE_B - 0.01, z_boden + LIPPE_H, x0 + laenge, y_kante + 1, z_oben + 1)
    return tasche + maul


# --- Steckverbindungen zwischen den Bausteinen ----------------------------------
# Form A (rund) verbindet Daten und Transport-Header, Form B (Schwalbenschwanz)
# Transport- und IP-Header. So passt nur die richtige Reihenfolge zusammen.

def zapfen(form, y_mitte, zugabe=0.0, hoehe=ZAPFEN_H):
    """Zapfen, der von der Fläche x=0 nach -X ragt. zugabe > 0 ergibt die Tasche."""
    if form == "A":
        hals = Pos(-2 + 0.5, y_mitte) * Rectangle(5, 7 + 2 * zugabe)
        kopf = Pos(-9, y_mitte) * Circle(6 + zugabe)
        skizze = hals + kopf
    else:
        a, b, tiefe = 4 + zugabe, 7.5 + zugabe, 10 + zugabe
        # Punkte gegen den Uhrzeigersinn, sonst zeigt die Fläche nach unten
        skizze = Polygon((1, y_mitte - a), (1, y_mitte + a), (-tiefe, y_mitte + b),
                         (-tiefe, y_mitte - b), align=None)
    return extrude(skizze, hoehe)


def tasche(form, x_flaeche, y_mitte):
    """Unten offene Tasche in der rechten Stirnfläche (bei x_flaeche) eines Bausteins."""
    koerper = zapfen(form, y_mitte, zugabe=SPIEL, hoehe=ZAPFEN_H + 0.4 + 1)
    return Pos(x_flaeche, 0, -1) * koerper


# --- Bausteine der Dateneinheit ---------------------------------------------------

def _kopf_grundkoerper(laenge):
    return fase_oben_unten(rundquader(0, 0, 0, laenge, BLOCK_B, BLOCK_H, 1.5), 0.5, BLOCK_FASE)


def header(name, titel, oben, unten, farbe, schriftfarbe, steckt_vorn, tasche_hinten, anzahl):
    """IP-, TCP- oder UDP-Header mit zwei Fächern (hinten = erstes Feld, vorn = zweites)."""
    k = _kopf_grundkoerper(KOPF_L)
    x_fach = (KOPF_L - FACH_L) / 2
    k -= fach(x_fach, 0, -1, BLOCK_H)
    k -= fach(x_fach, BLOCK_B, +1, BLOCK_H)
    if tasche_hinten:
        k -= tasche(tasche_hinten, KOPF_L, BLOCK_B / 2)
    if steckt_vorn:
        k += zapfen(steckt_vorn, BLOCK_B / 2)
    t = Teil(name, k, farbe=farbe, schriftfarbe=schriftfarbe, anzahl=anzahl)
    mx = KOPF_L / 2
    t.beschrifte(titel, mx, sum(TITEL_Y) / 2, BLOCK_H, 7.6, KOPF_L - 5)
    t.beschrifte(oben, mx, sum(TEXT_HINTEN_Y) / 2, BLOCK_H, 4.6, KOPF_L - 5)
    t.beschrifte(unten, mx, sum(TEXT_VORN_Y) / 2, BLOCK_H, 4.6, KOPF_L - 5)
    return t


def ip_header():
    return header("ip_header", "IP-HEADER", "QUELL-IP", "ZIEL-IP", "gruen", "weiss",
                  steckt_vorn=None, tasche_hinten="B", anzahl=3)


def tcp_header():
    return header("tcp_header", "TCP-HEADER", "QUELL-PORT", "ZIEL-PORT", "blau", "weiss",
                  steckt_vorn="B", tasche_hinten="A", anzahl=2)


def udp_header():
    return header("udp_header", "UDP-HEADER", "QUELL-PORT", "ZIEL-PORT", "hellblau", "schwarz",
                  steckt_vorn="B", tasche_hinten="A", anzahl=2)


def daten_block():
    k = _kopf_grundkoerper(DATEN_L)
    k -= fach((DATEN_L - FACH_L) / 2, 0, -1, BLOCK_H)
    k += zapfen("A", BLOCK_B / 2)
    t = Teil("daten_block", k, farbe="silber", schriftfarbe="schwarz", anzahl=3)
    mx = DATEN_L / 2
    t.beschrifte("DATEN", mx, sum(TITEL_Y) / 2, BLOCK_H, 8.5, DATEN_L - 6)
    t.beschrifte("PROTOKOLL", mx, sum(TEXT_VORN_Y) / 2, BLOCK_H, 4.6, DATEN_L - 6)
    # Der Block steht für die drei oberen OSI-Schichten. Bits gehören zu Schicht 1 und stehen hier nicht.
    t.beschrifte_zeilen(["7 ANWENDUNG", "6 DARSTELLUNG", "5 SITZUNG"], mx, 51.0, BLOCK_H, 4.8, 6.0)
    return t


def frame_schale():
    k = rundquader(0, 0, 0, SCHALE_L, SCHALE_B, BODEN, 1.5)
    k += rundquader(0, 0, 0, ETH_L, SCHALE_B, SCHALE_H, 1.5)                       # Ethernet-Header
    k += rundquader(ETH_L + MULDE_L, 0, 0, SCHALE_L, SCHALE_B, SCHALE_H, 1.5)       # FCS
    k += quader(ETH_L - 1, SCHALE_B - SCHIENE_B, 0, ETH_L + MULDE_L + 1, SCHALE_B, BODEN + SCHIENE_H)
    k += quader(ETH_L - 1, 0, 0, ETH_L + MULDE_L + 1, RAND_B, BODEN + RAND_H)
    k = fase_oben_unten(k, 0, 0.6)
    x_fach = (ETH_L - FACH_L) / 2
    k -= fach(x_fach, 0, -1, SCHALE_H)
    k -= fach(x_fach, SCHALE_B, +1, SCHALE_H)
    # FCS-Fach: quadratisch, offen zur rechten Stirnseite
    fx0 = SCHALE_L - LIPPE_B - (FCS_PL + 0.5)
    k -= quader(fx0, 4, SCHALE_H - FACH_T, SCHALE_L - LIPPE_B, 4 + FCS_PL + 0.5, SCHALE_H + 1)
    k -= quader(SCHALE_L - LIPPE_B - 0.01, 4, SCHALE_H - FACH_T + LIPPE_H, SCHALE_L + 1, 4 + FCS_PL + 0.5, SCHALE_H + 1)
    t = Teil("frame_schale", k, farbe="orange", schriftfarbe="schwarz", anzahl=3)
    mx = ETH_L / 2
    t.beschrifte("ETHERNET", mx, 34.6, SCHALE_H, 7.6, ETH_L - 5)
    t.beschrifte("HEADER", mx, 26.0, SCHALE_H, 7.6, ETH_L - 5)
    t.beschrifte("ZIEL-MAC", mx, 42.3, SCHALE_H, 4.6)
    t.beschrifte("QUELL-MAC", mx, 19.3, SCHALE_H, 4.6)
    t.beschrifte("FCS", SCHALE_L - FCS_L / 2, 31.0, SCHALE_H, 7.6, FCS_L - 4)
    return t


# --- Plättchen ----------------------------------------------------------------------

def plaettchen(text, x=0.0, y=0.0):
    k = fase_oben_unten(rundquader(0, 0, 0, PL_L, PL_B, PL_H, 1.5), 0.4, 0.4)
    t = Teil("plaettchen", k)
    if "\n" in text:
        # MAC-Adresse: oben klein der Herstellerteil, unten groß der Geräteteil
        klein, gross = text.split("\n")
        t.beschrifte(klein, PL_L / 2, 10.75, PL_H, 4.6, PL_L - 4.5)
        t.beschrifte(gross, PL_L / 2, 5.05, PL_H, 6.8, PL_L - 4.5)
    else:
        t.beschrifte(text, PL_L / 2, PL_B / 2, PL_H, 7.8, PL_L - 4.5)
    if x or y:
        t.koerper = Pos(x, y, 0) * t.koerper
        t.schrift = Pos(x, y, 0) * t.schrift
    return t


def plaettchen_bogen(name, eintraege, spalten=4):
    """Alle Plättchen einer Sorte nebeneinander auf einem Druckbett."""
    texte = [text for text, anzahl in eintraege for _ in range(anzahl)]
    koerper = schrift = None
    for i, text in enumerate(texte):
        p = plaettchen(text, (i % spalten) * (PL_L + 6), (i // spalten) * (PL_B + 6))
        koerper = p.koerper if koerper is None else koerper + p.koerper
        schrift = p.schrift if schrift is None else schrift + p.schrift
    return Teil(name, koerper, schrift, farbe="weiss", schriftfarbe="schwarz",
                anzahl=1, hinweis=f"ein Bogen mit {len(texte)} Plättchen",
                extra={"texte": texte, "spalten": spalten})


def fcs_plaettchen():
    k = fase_oben_unten(rundquader(0, 0, 0, FCS_PL, FCS_PL, PL_H, 1.5), 0.4, 0.4)
    t = Teil("fcs_plaettchen", k, farbe="gruen", schriftfarbe="weiss", anzahl=4,
             hinweis="Farbwechsel bei 2,5 mm: unten rot, oben grün")
    t.beschrifte("OK", FCS_PL / 2, FCS_PL / 2, PL_H, 7.0, FCS_PL - 3)
    t.beschrifte("X", FCS_PL / 2, FCS_PL / 2, 0, 9.0, unten=True)
    return t


def stoerungs_chip():
    k = fase_oben_unten(Pos(CHIP_D / 2, CHIP_D / 2, 0) * Cylinder(CHIP_D / 2, CHIP_H, align=(Align.CENTER, Align.CENTER, Align.MIN)), 0.4, 0.4)
    t = Teil("stoerungs_chip", k, farbe="rot", schriftfarbe="weiss", anzahl=6)
    t.beschrifte("!", CHIP_D / 2, CHIP_D / 2, CHIP_H, 18)
    return t


# --- Kabel und Anschlüsse -------------------------------------------------------------

def nase(zugabe=0.0, hoehe=BUCHT_T - 0.4):
    """Puzzle-Nase, die von x=0 nach -X ragt, mittig bei y=0."""
    hals = Pos(-NASE_HALS_L / 2 + 0.5, 0) * Rectangle(NASE_HALS_L + 1, NASE_HALS_B + 2 * zugabe)
    kopf = Pos(-(NASE_HALS_L + NASE_R - 1), 0) * Circle(NASE_R + zugabe)
    return extrude(hals + kopf, hoehe)


def anschluss(x, y, winkel):
    """Durchbruch im Buchtboden für eine Kabelnase. winkel: Richtung, in der das Kabel liegt."""
    schnitt = Pos(0, 0, -1) * nase(NASE_SPIEL, PLATTE_H + 2)
    # Die Nase ragt vom Kabelende in die Platte hinein, also entgegen der Kabelrichtung.
    # nase() zeigt nach -X; das passt zu einem Kabel, das nach +X wegführt (winkel 0).
    return Pos(x, y, 0) * Rot(0, 0, winkel) * schnitt


def kabel():
    breite = BUCHT_B + 2 * KABEL_RAND
    h = PLATTE_H - BUCHT_T          # Oberseite der Fahrbahn = Boden der Bucht
    k = quader(0, 0, 0, KABEL_L, breite, h)
    k += quader(0, 0, 0, KABEL_L, KABEL_RAND, PLATTE_H)
    k += quader(0, breite - KABEL_RAND, 0, KABEL_L, breite, PLATTE_H)
    k += Pos(0, breite / 2, 0) * nase(0, h)
    k += Pos(KABEL_L, breite / 2, 0) * mirror(nase(0, h), Plane.YZ)
    t = Teil("kabel", k, farbe="anthrazit", schriftfarbe="weiss", anzahl=6,
             hinweis="5 im Spiel, 1 Reserve")
    t.beschrifte("1", KABEL_L / 2, breite / 2 + 7, h, 20)
    t.beschrifte("BITÜBERTRAGUNG", KABEL_L / 2, breite / 2 - 13, h, 7.5, KABEL_L - 8)
    return t


# --- Stationsplatten --------------------------------------------------------------------

def _platte():
    return fase_oben_unten(rundquader(0, 0, 0, PLATTE_L, PLATTE_B, PLATTE_H, 4), 0.6, 0.6)


def _kartenfach(x0, y0):
    """Flache Vertiefung für eine Papierkarte mit Griffmulde an der Vorderkante."""
    l, b = KARTE_L + 1.6, KARTE_B + 1.6
    schnitt = quader(x0, y0, PLATTE_H - KARTENFACH_T, x0 + l, y0 + b, PLATTE_H + 1)
    mulde = Pos(x0 + l / 2, y0, PLATTE_H - 2.6) * Cylinder(9, 4, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return schnitt + mulde


def _bucht(x0, x1, y0):
    return quader(x0, y0, PLATTE_H - BUCHT_T, x1, y0 + BUCHT_B, PLATTE_H + 1)


def _federschlitze(positionen):
    """Schlitze, in die die Federn einer Blende gesteckt werden. (x, y, entlang 'x' oder 'y')"""
    schnitt = None
    for x, y, entlang in positionen:
        l, b = (FEDER_L + 0.4, BLENDE_WAND + 0.4) if entlang == "x" else (BLENDE_WAND + 0.4, FEDER_L + 0.4)
        s = quader(x - l / 2, y - b / 2, PLATTE_H - FEDER_T - 0.3, x + l / 2, y + b / 2, PLATTE_H + 1)
        schnitt = s if schnitt is None else schnitt + s
    return schnitt


# Zonen des Montageplatzes (X-Bereiche), wenn die Schale links in der Bucht anliegt
ZONE_ETH = (SCHALE_X0, SCHALE_X0 + ETH_L)
ZONE_IP = (ZONE_ETH[1], ZONE_ETH[1] + KOPF_L)
ZONE_TP = (ZONE_IP[1], ZONE_IP[1] + KOPF_L)
ZONE_DATEN = (ZONE_TP[1], ZONE_TP[1] + DATEN_L)
MONTAGE_X = (ZONE_IP[0] - 0.4, ZONE_ETH[1] + MULDE_L + 0.4)       # 50,3 … 207,9
DACH_X0 = ZONE_TP[0] + 0.3                                         # Router-Dach beginnt über dem TCP-Header
DACH_Y0 = MONTAGE_Y0 - BLENDE_WAND
DACH_Y1 = BUCHT_Y0 - 3.0
DACH_FEDERN = [(DACH_X0 + 14, DACH_Y0 + BLENDE_WAND / 2, "x"),
               (MONTAGE_X[1] - 14, DACH_Y0 + BLENDE_WAND / 2, "x"),
               (MONTAGE_X[1] + BLENDE_WAND / 2, MONTAGE_Y0 + 36, "y")]
TUNNEL_X = MONTAGE_X
TUNNEL_Y0 = SW_BUCHT_Y0 - 0.3 - BLENDE_WAND
TUNNEL_Y1 = SW_BUCHT_Y0 + BUCHT_B + 0.3 + BLENDE_WAND
TUNNEL_FEDERN = [(x, y, "x") for x in (TUNNEL_X[0] + 24, TUNNEL_X[1] - 24)
                 for y in (TUNNEL_Y0 + BLENDE_WAND / 2, TUNNEL_Y1 - BLENDE_WAND / 2)]


def _host_oder_router(name, titel, router):
    k = _platte()
    bucht_x1 = PLATTE_L + 1 if router else SCHALE_X0 + SCHALE_L + 0.7
    k -= _bucht(-1, bucht_x1, BUCHT_Y0)
    y_bucht = BUCHT_Y0 + BUCHT_B / 2
    k -= anschluss(0, y_bucht, 180)
    if router:
        k -= anschluss(PLATTE_L, y_bucht, 0)
    # Rand um den Montageplatz: Leiste vorn (mit Nummer und Name der Schicht), Stege links und rechts
    z1 = PLATTE_H + RAND_PLATTE_H
    leiste_x1 = DACH_X0 - 0.5 if router else MONTAGE_X[1] + 4
    k += quader(4, LEISTE_Y0, PLATTE_H - 0.1, leiste_x1, MONTAGE_Y0, z1)
    k += quader(MONTAGE_X[0] - 3.8, MONTAGE_Y0 - 0.1, PLATTE_H - 0.1, MONTAGE_X[0] - 0.2, MONTAGE_Y0 + 53, z1)
    if router:
        k -= _federschlitze(DACH_FEDERN)
    else:
        k += quader(MONTAGE_X[1] + 0.2, MONTAGE_Y0 - 0.1, PLATTE_H - 0.1, MONTAGE_X[1] + 4, MONTAGE_Y0 + 53, z1)
    k -= _kartenfach(6, 5)
    k -= _kartenfach(94, 5)
    t = Teil(name, k, farbe="hellgrau", schriftfarbe="schwarz", anzahl=1 if router else 4)
    y_leiste = (LEISTE_Y0 + MONTAGE_Y0) / 2
    schichten = [("2", "SICHERUNG", ZONE_ETH), ("3", "VERMITTLUNG", ZONE_IP)]
    if not router:
        schichten += [("4", "TRANSPORT", ZONE_TP), ("5–7", "ANWENDUNG", ZONE_DATEN)]
    for nummer, schichtname, zone in schichten:
        t.beschrifte_paar(nummer, schichtname, sum(zone) / 2, y_leiste, z1, 9, 5.4)
    t.beschrifte(titel, 208, 40, PLATTE_H, 11, 52)
    # Hinweise im Buchtboden: wo der Header liegt
    t.beschrifte("HEADER", 36.5, y_bucht, PLATTE_H - BUCHT_T, 6.2)
    t.beschrifte("FCS", SCHALE_X0 + SCHALE_L - 14, y_bucht, PLATTE_H - BUCHT_T, 6.2)
    if router:
        t.beschrifte("A", 22, 110, PLATTE_H, 16)
        t.beschrifte("←", 22, 92, PLATTE_H, 14)
        t.beschrifte("B", 226, 110, PLATTE_H, 16)
        t.beschrifte("→", 226, 92, PLATTE_H, 14)
    return t


def platte_host():
    return _host_oder_router("platte_host", "HOST", router=False)


def platte_router():
    return _host_oder_router("platte_router", "ROUTER", router=True)


SW_STUTZEN_X0 = (PLATTE_L - BUCHT_B) / 2
SW_STUTZEN_T = 28.0


def platte_switch():
    k = _platte()
    k -= _bucht(-1, PLATTE_L + 1, SW_BUCHT_Y0)
    y_bucht = PLATTE_B / 2
    k -= anschluss(0, y_bucht, 180)                 # Port 1 links
    k -= anschluss(PLATTE_L, y_bucht, 0)            # Port 3 rechts
    # Port 2 hinten und Port 4 vorn: kurze Stutzen auf Kabelhöhe
    x0, x1 = SW_STUTZEN_X0, SW_STUTZEN_X0 + BUCHT_B
    k -= quader(x0, PLATTE_B - SW_STUTZEN_T, PLATTE_H - BUCHT_T, x1, PLATTE_B + 1, PLATTE_H + 1)
    k -= quader(x0, -1, PLATTE_H - BUCHT_T, x1, SW_STUTZEN_T, PLATTE_H + 1)
    k -= anschluss(PLATTE_L / 2, PLATTE_B, 90)
    k -= anschluss(PLATTE_L / 2, 0, 270)
    k -= _federschlitze(TUNNEL_FEDERN)
    k -= _kartenfach(5, 6)
    t = Teil("platte_switch", k, farbe="hellgrau", schriftfarbe="schwarz", anzahl=1)
    t.beschrifte("SWITCH", 198, 46, PLATTE_H, 11, 56)
    # P1 und P3 stehen vor der Bucht, damit Schale und Tunnel sie nicht verdecken
    t.beschrifte("P1", 24, 64.3, PLATTE_H, 8)
    t.beschrifte("P3", 222, 64.3, PLATTE_H, 8)
    t.beschrifte("P2", 172, 186, PLATTE_H, 10)
    t.beschrifte("P4", 172, 14, PLATTE_H, 10)
    t.beschrifte("HEADER", 36.5, y_bucht, PLATTE_H - BUCHT_T, 6.2)
    return t


# --- Blenden ------------------------------------------------------------------------------

def _federn(positionen):
    koerper = None
    for x, y, entlang in positionen:
        l, b = (FEDER_L, BLENDE_WAND) if entlang == "x" else (BLENDE_WAND, FEDER_L)
        f = quader(x - l / 2, y - b / 2, PLATTE_H - FEDER_T, x + l / 2, y + b / 2, PLATTE_H + 0.1)
        koerper = f if koerper is None else koerper + f
    return koerper


def switch_tunnel():
    """Tunnel über der Bucht des Switches. Maße im Koordinatensystem der Switch-Platte."""
    z0, z1 = PLATTE_H, PLATTE_H + BLENDE_LICHT
    x0, x1 = TUNNEL_X
    k = quader(x0, TUNNEL_Y0, z0, x1, TUNNEL_Y0 + BLENDE_WAND, z1)
    k += quader(x0, TUNNEL_Y1 - BLENDE_WAND, z0, x1, TUNNEL_Y1, z1)
    k += rundquader(x0, TUNNEL_Y0, z1, x1, TUNNEL_Y1, z1 + BLENDE_DECKE, 1.5)
    k += _federn(TUNNEL_FEDERN)
    t = Teil("switch_tunnel", k, farbe="orange", schriftfarbe="schwarz", anzahl=1, kopfueber=True,
             hinweis="liegt in der STL-Datei kopfüber")
    mx, my, zt = (x0 + x1) / 2, (TUNNEL_Y0 + TUNNEL_Y1) / 2, z1 + BLENDE_DECKE
    t.beschrifte("NUTZLAST", mx, my + 12, zt, 17, x1 - x0 - 16)
    t.beschrifte("SCHICHT 3–7", mx, my - 6, zt, 8.5)
    t.beschrifte("DER SWITCH LIEST NUR SCHICHT 2", mx, my - 22, zt, 6.0, x1 - x0 - 12)
    return t


def router_dach():
    """Dach über TCP-Header und Daten auf dem Router. Maße im Koordinatensystem der Router-Platte."""
    z0, z1 = PLATTE_H, PLATTE_H + BLENDE_LICHT
    x0, x1 = DACH_X0, MONTAGE_X[1] + BLENDE_WAND
    k = quader(x0, DACH_Y0, z0, x1, MONTAGE_Y0, z1)                 # Wand vorn
    k += quader(MONTAGE_X[1], DACH_Y0, z0, x1, DACH_Y1, z1)         # Wand rechts
    k += rundquader(x0, DACH_Y0, z1, x1, DACH_Y1, z1 + BLENDE_DECKE, 1.5)
    k += _federn(DACH_FEDERN)
    t = Teil("router_dach", k, farbe="gruen", schriftfarbe="weiss", anzahl=1, kopfueber=True,
             hinweis="liegt in der STL-Datei kopfüber")
    mx, my, zt = (x0 + x1) / 2, (DACH_Y0 + DACH_Y1) / 2, z1 + BLENDE_DECKE
    t.beschrifte("SCHICHT 4–7", mx, my + 12, zt, 11, x1 - x0 - 12)
    t.beschrifte("BLEIBT ZU", mx, my - 3, zt, 8.5)
    t.beschrifte("DER ROUTER LIEST BIS SCHICHT 3", mx, my - 18, zt, 5.4, x1 - x0 - 10)
    return t


# --- Vorratskasten ------------------------------------------------------------------------

KASTEN_FACH_L, KASTEN_FACH_B = PL_L + 1.2, PL_B + 1.2
KASTEN_SPALTE = 2 + KASTEN_FACH_L + KASTEN_GASSE
KASTEN_ZEILE = KASTEN_FACH_B + 2
KASTEN_KOPF = 13.0
KASTEN_L = KASTEN_SPALTEN * KASTEN_SPALTE + 2
KASTEN_B = KASTEN_ZEILEN * KASTEN_ZEILE + 2 + KASTEN_KOPF
KASTEN_H = 2 + KASTEN_FACH_T + 2


def kasten_fach_position(spalte, zeile):
    """Linke vordere Ecke eines Fachs. Zeile 0 liegt hinten unter der Überschrift."""
    x = 2 + spalte * KASTEN_SPALTE
    y = KASTEN_B - KASTEN_KOPF - (zeile + 1) * KASTEN_ZEILE
    return x, y


def vorratskasten(ueberschriften=("MAC", "IP", "PORT", "PROTOKOLL")):
    k = fase_oben_unten(rundquader(0, 0, 0, KASTEN_L, KASTEN_B, KASTEN_H, 3), 0.5, 0.6)
    z_fach = KASTEN_H - KASTEN_FACH_T
    for s in range(KASTEN_SPALTEN):
        x_gasse = 2 + s * KASTEN_SPALTE + KASTEN_FACH_L
        k -= quader(x_gasse - 0.01, 2, 2, x_gasse + KASTEN_GASSE, KASTEN_B - KASTEN_KOPF, KASTEN_H + 1)
        for z in range(KASTEN_ZEILEN):
            x, y = kasten_fach_position(s, z)
            k -= quader(x, y, z_fach, x + KASTEN_FACH_L + 0.02, y + KASTEN_FACH_B, KASTEN_H + 1)
    t = Teil("vorratskasten", k, farbe="hellgrau", schriftfarbe="schwarz", anzahl=1)
    for s, text in enumerate(ueberschriften):
        x = 2 + s * KASTEN_SPALTE + KASTEN_FACH_L / 2
        t.beschrifte(text, x, KASTEN_B - KASTEN_KOPF / 2, KASTEN_H, 7.5, KASTEN_FACH_L - 2)
    return t
