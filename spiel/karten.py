"""Erzeugt alle Karten für Header Ahead.

Aufruf (aus dem Ordner header-ahead):  python3 spiel/karten.py

Ausgabe:
  Karten.pdf            Druckvorlage: Netzpläne, kleine Karten, Auftragskarten (Vorder- und Rückseiten)
  spiel/_karten/*.png   die kleinen Karten einzeln als Bild, für die Renderings
"""

import subprocess
import sys
from html import escape
from pathlib import Path

HIER = Path(__file__).resolve().parent
WURZEL = HIER.parent
sys.path.insert(0, str(HIER))

from daten import CLIENT_PORTS, DIENSTE, EREIGNISSE, HOSTS, NETZE, ROUTER, SWITCH_PORTS, mac_teile  # noqa: E402
from loesung import ALLE, CLIENT_PORT, merksatz  # noqa: E402
from stil import GRUND, KARTEN  # noqa: E402

HTML = HIER / "_html"
PNG = HIER / "_karten"


def mac_html(mac):
    """Ganze MAC-Adresse: Herstellerteil klein und grau, Geräteteil wie die Umgebung (meist fett)."""
    hersteller, geraet = mac_teile(mac)
    return f'<span class="mac"><span class="mac-h">{hersteller}:</span>{geraet}</span>'


# --- kleine Karten ------------------------------------------------------------------

def dienstliste(namen):
    if not namen:
        return "Bietet keine Dienste an (Client)."
    return "Dienste: " + " · ".join(
        f"<b>{n}</b> {DIENSTE[n]['port']}/{DIENSTE[n]['transport']}" for n in namen)


def karte_geraet(name):
    h = HOSTS[name]
    return f"""<div class="karte klein geraet">
  <div class="kopf"><span class="name">{name}</span><span class="art">{h['art']}</span></div>
  <table>
    <tr><th>IP-Adresse</th><td>{h['ip']}</td></tr>
    <tr><th>Netz</th><td>{NETZE[h['netz']]}</td></tr>
    <tr><th>Standard-Gateway</th><td>{h['gateway']}</td></tr>
    <tr><th>MAC-Adresse</th><td>{mac_html(h['mac'])}</td></tr>
  </table>
  <div class="fuss">{dienstliste(h['dienste'])}</div>
</div>"""


def mac_von(geraet):
    return ROUTER["A"]["mac"] if geraet == "ROUTER" else HOSTS[geraet]["mac"]


def karte_mac_tabelle():
    zeilen = "".join(f"<tr><td>{mac_html(mac_von(g))}</td><td>P{p}</td></tr>" for p, g in sorted(SWITCH_PORTS.items()))
    return f"""<div class="karte klein">
  <div class="kopf"><span class="name">SWITCH</span><span class="art">MAC-Tabelle</span></div>
  <table class="tabelle"><tr><th>MAC-Adresse</th><th>Port</th></tr>{zeilen}</table>
  <div class="fuss">Steht die Ziel-MAC nicht in der Tabelle: Störung.</div>
</div>"""


def karte_router_schnittstellen():
    zeilen = "".join(
        f"<tr><td>{s}</td><td>{ROUTER[s]['ip']}</td><td>{mac_html(ROUTER[s]['mac'])}</td></tr>" for s in ("A", "B"))
    return f"""<div class="karte klein">
  <div class="kopf"><span class="name">ROUTER</span><span class="art">Schnittstellen</span></div>
  <table class="tabelle"><tr><th>Anschluss</th><th>IP-Adresse</th><th>MAC-Adresse</th></tr>{zeilen}</table>
  <div class="fuss">Nimm nur Frames an, deren Ziel-MAC zu dem Anschluss gehört, an dem sie ankommen.</div>
</div>"""


def karte_routing_tabelle():
    zeilen = "".join(
        f"<tr><td>{ROUTER[s]['netz']}</td><td>{s}</td><td>direkt</td></tr>" for s in ("A", "B"))
    return f"""<div class="karte klein">
  <div class="kopf"><span class="name">ROUTER</span><span class="art">Routing-Tabelle</span></div>
  <table class="tabelle"><tr><th>Zielnetz</th><th>Anschluss</th><th>Nächster Halt</th></tr>{zeilen}</table>
  <div class="fuss">„direkt“ heißt: Der Empfänger hängt selbst an diesem Anschluss. Seine MAC steht im Netzplan.</div>
</div>"""


def karte_schichten():
    zeilen = [
        ("f-l7", "5–7", "Anwendung, Darstellung, Sitzung", "Anwendung", "Daten-Block", "Daten"),
        ("f-l4", "4", "Transport", "Transport", "TCP- oder UDP-Header", "Segment"),
        ("f-l3", "3", "Vermittlung", "Internet", "IP-Header", "Paket"),
        ("f-l2", "2", "Sicherung", "Netzzugang", "Frame-Schale", "Frame"),
        ("f-l1", "1", "Bitübertragung", "Netzzugang", "Kabel", "Bits"),
    ]
    html = "".join(
        f'<tr class="{f}"><td class="nr">{nr}</td><td>{osi}</td><td>{tcp}</td><td>{teil}</td><td class="pdu">{pdu}</td></tr>'
        for f, nr, osi, tcp, teil, pdu in zeilen)
    return f"""<div class="karte klein schichten">
  <table><col class="c1"><col class="c2"><col class="c3"><col class="c4"><col><tr><th></th><th>OSI</th><th>TCP/IP</th><th>Baustein</th><th>heißt</th></tr>{html}</table>
</div>"""


def karte_ereignis(e):
    folge = f'<p class="folge">{escape(e["folge"])}</p>' if e.get("folge") else ""
    return f"""<div class="karte klein ereignis">
  <div class="kopf"><span class="name">{escape(e['titel'])}</span><span class="art">Ereignis · <span class="stufe">STUFE 3</span></span></div>
  <p>{escape(e['text'])}</p>{folge}
</div>"""


def kleine_karten():
    """(Dateiname, HTML, Anzahl im Druck)"""
    karten = [(f"geraet_{name.lower().replace(' ', '')}", karte_geraet(name), 1) for name in HOSTS]
    karten += [
        ("mac_tabelle", karte_mac_tabelle(), 1),
        ("router_schnittstellen", karte_router_schnittstellen(), 1),
        ("routing_tabelle", karte_routing_tabelle(), 1),
        ("schichten", karte_schichten(), 5),
    ]
    for i, e in enumerate(EREIGNISSE):
        karten.append((f"ereignis_{i + 1}", karte_ereignis(e), e["anzahl"]))
    return karten


# --- Auftragskarten -----------------------------------------------------------------

def auftrag_vorn(l):
    zurueck = '<span class="zurueck">↩ mit Antwort</span>' if l["antwort"] else "<span></span>"
    return f"""<div class="karte auftrag">
  <div class="oben"><span class="nr">AUFTRAG {l['nr']:02d}</span><span class="stufe">STUFE {l['stufe']}</span></div>
  <div class="balken"></div>
  <div class="text">{escape(l['text'])}</div>
  <div class="wer">
    <div><span>Absender</span><span>{l['von']}</span></div>
    <div><span>Empfänger</span><span>{l['nach']}</span></div>
  </div>
  <div class="unten">{zurueck}<span><span class="punkte">{l['punkte']}</span> {'Punkt' if l['punkte'] == 1 else 'Punkte'}</span></div>
</div>"""


def kopfzeilen(s):
    tp = "f-l4" if s["transport"] == "TCP" else "f-l4u"
    a = s["ankunft"]

    def port(p):
        return "ein Client-Port" if p == CLIENT_PORT else p

    return f"""<table class="kopfzeilen">
  <tr><td class="teil f-l2" rowspan="2">ETH</td><td class="feld">Ziel-MAC</td><td class="wert">{mac_html(a['ziel_mac'])}</td></tr>
  <tr><td class="feld">Quell-MAC</td><td class="wert">{mac_html(a['quell_mac'])}</td></tr>
  <tr><td class="teil f-l3" rowspan="2">IP</td><td class="feld">Quell-IP</td><td class="wert">{s['quell_ip']}</td></tr>
  <tr><td class="feld">Ziel-IP</td><td class="wert">{s['ziel_ip']}</td></tr>
  <tr><td class="teil {tp}" rowspan="2">{s['transport']}</td><td class="feld">Quell-Port</td><td class="wert">{port(s['quell_port'])}</td></tr>
  <tr><td class="feld">Ziel-Port</td><td class="wert">{port(s['ziel_port'])}</td></tr>
  <tr><td class="teil f-l7">DATEN</td><td class="feld">Protokoll</td><td class="wert">{s['anwendung']}</td></tr>
</table>"""


def erste_strecke(s):
    if len(s["teilstrecken"]) < 2:
        return ""
    t = s["teilstrecken"][0]
    return (f'<div class="strecke1">Auf der ersten Teilstrecke ({t["von"]} bis {t["bis"]}) stand im '
            f'Ethernet-Header: Ziel <b>{mac_html(t["ziel_mac"])}</b>, Quelle <b>{mac_html(t["quell_mac"])}</b>.</div>')


def auftrag_hinten(l):
    hin = l["hin"]
    teile = [f'<h4>So kommt sie bei {hin["nach"]} an</h4>', kopfzeilen(hin)]
    if not l["antwort"]:
        teile.append(erste_strecke(hin))
    else:
        z = l["zurueck"]
        a = z["ankunft"]
        teile.append(f"""<h4>Antwort, wie sie bei {z['nach']} ankommt</h4>
<table class="kopfzeilen">
  <tr><td class="teil f-l2">ETH</td><td class="wert">Ziel {mac_html(a['ziel_mac'])}<br>Quelle {mac_html(a['quell_mac'])}</td></tr>
  <tr><td class="teil f-l3">IP</td><td class="wert">Quelle {z['quell_ip']} · Ziel {z['ziel_ip']}</td></tr>
  <tr><td class="teil {'f-l4' if z['transport'] == 'TCP' else 'f-l4u'}">{z['transport']}</td><td class="wert">Quelle {z['quell_port']} · Ziel: der Client-Port der Anfrage</td></tr>
</table>""")
    return f"""<div class="karte auftrag loesung">
  <div class="oben"><span class="nr">LÖSUNG {l['nr']:02d}</span><span class="stufe">STUFE {l['stufe']}</span></div>
  <div class="weg">{' → '.join(escape(w) for w in hin['weg'])}</div>
  {''.join(teile)}
  <div class="merke">{escape(merksatz(l))}</div>
</div>"""


# --- Netzplan ------------------------------------------------------------------------

def netzplan(stufe):
    """Schematischer Plan: Lage wie auf dem Tisch, mit allen Adressen."""

    def geraet(name, x, y):
        h = HOSTS[name]
        return (f'<div class="np-geraet" style="left:{x}mm;top:{y}mm"><div class="np-name">{name}</div>'
                f'<div class="np-art">{h["art"]}</div><div class="np-zeile"><span>IP</span><b>{h["ip"]}</b></div>'
                f'<div class="np-zeile"><span>MAC</span><b>{mac_html(h["mac"])}</b></div></div>')

    def linie(x, y, b, h):
        return f'<div class="np-linie" style="left:{x}mm;top:{y}mm;width:{b}mm;height:{h}mm"></div>'

    def port(text, x, y):
        return f'<div class="np-port" style="left:{x}mm;top:{y}mm">{text}</div>'

    voll = stufe >= 2
    teile = [f'<div class="np-netz np-a" style="left:2mm;top:6mm;width:{168 if voll else 150}mm;height:130mm">'
             f'<span>Netz A · {NETZE["A"]}</span></div>']
    if voll:
        teile.append(f'<div class="np-netz np-b" style="left:174mm;top:36mm;width:101mm;height:70mm">'
                     f'<span>Netz B · {NETZE["B"]}</span></div>')
    # Leitungen
    teile += [linie(52, 71, 28, 1.2), linie(100, 38, 1.2, 20), linie(100, 84, 1.2, 20)]
    teile += [geraet("INTRA", 8, 54), geraet("PC 1", 78, 12), geraet("PC 2", 78, 104)]
    teile.append('<div class="np-kasten np-switch" style="left:80mm;top:58mm"><div class="np-name">SWITCH</div>'
                 '<div class="np-art">liest Schicht 2</div></div>')
    teile += [port("P1", 71, 65), port("P2", 103, 50), port("P4", 103, 87)]
    if voll:
        teile += [linie(122, 71, 28, 1.2), linie(196, 71, 26, 1.2)]
        teile.append(port("P3", 124, 65))
        teile.append(
            '<div class="np-kasten np-router" style="left:150mm;top:48mm"><div class="np-name">ROUTER</div>'
            '<div class="np-art">liest bis Schicht 3</div>'
            f'<div class="np-seiten"><div><i>Anschluss A</i><div class="np-zeile"><span>IP</span><b>{ROUTER["A"]["ip"]}</b></div>'
            f'<div class="np-zeile"><span>MAC</span><b>{mac_html(ROUTER["A"]["mac"])}</b></div></div>'
            f'<div><i>Anschluss B</i><div class="np-zeile"><span>IP</span><b>{ROUTER["B"]["ip"]}</b></div>'
            f'<div class="np-zeile"><span>MAC</span><b>{mac_html(ROUTER["B"]["mac"])}</b></div></div></div></div>')
        teile.append(geraet("WEB", 222, 54))
    dienste = "".join(
        f"<tr><td><b>{n}</b></td><td>{d['port']}</td><td>{d['transport']}</td><td>{d['wozu']}</td><td>{', '.join(g for g, h in HOSTS.items() if n in h['dienste'] and (voll or h['netz'] == 'A')) or '–'}</td></tr>"
        for n, d in DIENSTE.items() if voll or any(n in h["dienste"] for h in HOSTS.values() if h["netz"] == "A"))
    untertitel = ("Ein Netz mit Switch. Alle Ziele liegen im eigenen Netz." if not voll else
                  "Zwei Netze, verbunden durch den Router. Ziele im fremden Netz erreicht man nur über das Gateway.")
    return f"""<section class="seite netzplan">
  <header><div><h1>Netzplan · Stufe {stufe}{' und 3' if voll else ''}</h1><p>{untertitel}</p></div>
    <div class="marke">header-ahead_</div></header>
  <div class="np-flaeche">{''.join(teile)}</div>
  <div class="np-unten">
    <table class="np-dienste"><tr><th>Dienst</th><th>Port</th><th>Transport</th><th>Wozu</th><th>Läuft auf</th></tr>{dienste}</table>
    <div class="np-hinweise">
      <p><b>Client-Ports:</b> Der Absender wählt als Quell-Port irgendeinen freien Port aus dem Vorrat
      ({', '.join(str(p) for p in CLIENT_PORTS)}). Der Ziel-Port ist der Port des Dienstes.</p>
      <p><b>MAC-Adressen</b> haben sechs Bytes: drei für den Hersteller, drei für das Gerät. Der Herstellerteil
      steht klein davor, auf den Plättchen klein darüber. Zum Suchen reicht der große Geräteteil.</p>
      <p><b>Woher kennt ein Gerät die MAC eines anderen?</b> In echt fragt es per ARP nach. Hier schlagt ihr im Netzplan nach.</p>
    </div>
  </div>
</section>"""


SEITEN_CSS = """
@page { margin: 0; }
@page netz { size: 297mm 210mm; }
@page klein { size: 210mm 297mm; }
@page auftrag { size: 297mm 210mm; }
.seite { page-break-after: always; position: relative; }
.netzplan { page: netz; width: 297mm; height: 210mm; padding: 9mm 10mm; }
.netzplan header { display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 1.2mm solid var(--amber);
  padding-bottom: 2mm; margin-bottom: 3mm; }
.netzplan h1 { font-size: 17pt; margin: 0; font-weight: 800; }
.netzplan header p { margin: 0.6mm 0 0; font-size: 9.5pt; color: var(--grau); }
.marke { font-family: "JetBrains Mono", monospace; font-weight: 800; font-size: 10pt; }
.np-flaeche { position: relative; width: 277mm; height: 138mm; }
.np-netz { position: absolute; border-radius: 3mm; }
.np-netz span { position: absolute; left: 3mm; top: 2mm; font-family: "JetBrains Mono", monospace; font-weight: 700; font-size: 9pt; }
.np-a { background: #EEF2F6; } .np-b { background: #FFF3DA; }
.np-linie { position: absolute; background: var(--l1); }
.np-geraet, .np-kasten { position: absolute; background: #fff; border: 0.5mm solid var(--tinte); border-radius: 1.5mm;
  padding: 2mm 2.6mm; width: 44mm; }
.np-kasten { text-align: center; }
.np-switch { border-top: 2.2mm solid var(--l2); width: 42mm; height: 26mm; }
.np-router { border-top: 2.2mm solid var(--l3); width: 46mm; }
.np-name { font-family: "JetBrains Mono", monospace; font-weight: 800; font-size: 12pt; }
.np-art { font-size: 7.4pt; color: var(--grau); margin-bottom: 1mm; }
.np-zeile { display: flex; justify-content: space-between; font-size: 8pt; }
.np-zeile span { color: var(--grau); } .np-zeile b { font-family: "JetBrains Mono", monospace; font-size: 9pt; }
.np-seiten { text-align: left; } .np-seiten > div { border-top: 0.2mm solid var(--linie); padding-top: 0.8mm; margin-top: 0.8mm; }
.np-seiten i { font-style: normal; font-size: 7pt; font-weight: 600; }
.np-port { position: absolute; font-family: "JetBrains Mono", monospace; font-weight: 800; font-size: 8pt; }
.np-unten { display: grid; grid-template-columns: 150mm 1fr; column-gap: 9mm; margin-top: 2mm; }
.np-dienste { font-size: 8.4pt; width: 150mm; }
.np-dienste th { text-align: left; font-family: "JetBrains Mono", monospace; font-size: 7.2pt; text-transform: uppercase;
  letter-spacing: 0.04em; border-bottom: 0.3mm solid var(--tinte); padding: 0.6mm 1.5mm 0.6mm 0; }
.np-dienste td { border-bottom: 0.2mm solid var(--linie); padding: 0.8mm 1.5mm 0.8mm 0; }
.np-dienste td:nth-child(-n+3), .np-dienste td:last-child { font-family: "JetBrains Mono", monospace; }
.np-hinweise { font-size: 8pt; line-height: 1.35; } .np-hinweise p { margin: 0 0 1.4mm; }
.bogen { display: grid; gap: 0; align-content: start; justify-content: center; }
.bogen .karte { outline: 0.15mm dashed #9AA4AE; }
.bogen-klein { page: klein; width: 210mm; height: 297mm; padding-top: 14mm; }
.bogen-klein .bogen { grid-template-columns: 80mm 80mm; }
.bogen-auftrag { page: auftrag; width: 297mm; height: 210mm; padding-top: 4mm; }
.bogen-auftrag .bogen { grid-template-columns: repeat(4, 70mm); }
.bogenseite { overflow: hidden; }
.bogenseite .hinweis { position: absolute; left: 0; right: 0; bottom: 1.6mm; text-align: center; font-size: 6.5pt; color: var(--grau); }
"""


def bogen(klasse, karten, hinweis):
    # Der Hinweis steht außerhalb des Rasters, sonst zählt er als Rasterzelle und rutscht auf eine eigene Seite.
    return (f'<section class="seite bogenseite {klasse}"><div class="bogen">{"".join(karten)}</div>'
            f'<div class="hinweis">{hinweis}</div></section>')


def druckvorlage():
    seiten = [netzplan(1), netzplan(2)]
    klein = [html for _, html, anzahl in kleine_karten() for _ in range(anzahl)]
    for i in range(0, len(klein), 10):
        seiten.append(bogen("bogen-klein", klein[i:i + 10],
                            "Kleine Karten 80 × 52 mm · einseitig drucken, an den gestrichelten Linien schneiden"))
    for i in range(0, len(ALLE), 8):
        gruppe = ALLE[i:i + 8]
        seiten.append(bogen("bogen-auftrag", [auftrag_vorn(l) for l in gruppe],
                            "Auftragskarten 70 × 100 mm · Vorderseiten · beidseitig drucken, über die kurze Kante wenden · Auftrag und Lösung mit derselben Nummer liegen Rücken an Rücken"))
        # Rückseiten: jede Viererreihe spiegeln, damit Lösung und Auftrag aufeinanderliegen
        hinten = []
        for r in range(0, len(gruppe), 4):
            reihe = [auftrag_hinten(l) for l in gruppe[r:r + 4]]
            reihe += ['<div class="karte auftrag" style="outline:none"></div>'] * (4 - len(reihe))
            hinten += reversed(reihe)
        seiten.append(bogen("bogen-auftrag", hinten, "Auftragskarten · Rückseiten (Lösungen)"))
    return (f'<!doctype html><html lang="de"><head><meta charset="utf-8"><title>Header Ahead · Karten</title>'
            f'<style>{GRUND}{KARTEN}{SEITEN_CSS}</style></head><body>{"".join(seiten)}</body></html>')


def einzelbilder():
    karten = kleine_karten()
    css = "@page { size: 80mm 52mm; margin: 0; } .karte { page-break-after: always; }"
    html = (f'<!doctype html><html lang="de"><head><meta charset="utf-8"><style>{GRUND}{KARTEN}{css}</style></head>'
            f'<body>{"".join(h for _, h, _ in karten)}</body></html>')
    return html, [name for name, _, _ in karten]


def weasyprint(quelle, ziel):
    subprocess.run(["weasyprint", "-q", str(quelle), str(ziel)], check=True)


def main():
    HTML.mkdir(exist_ok=True)
    PNG.mkdir(exist_ok=True)
    (HTML / "karten.html").write_text(druckvorlage(), encoding="utf-8")
    weasyprint(HTML / "karten.html", WURZEL / "Karten.pdf")
    html, namen = einzelbilder()
    (HTML / "kleinkarten.html").write_text(html, encoding="utf-8")
    weasyprint(HTML / "kleinkarten.html", HTML / "kleinkarten.pdf")
    for alt in PNG.glob("*.png"):
        alt.unlink()
    subprocess.run(["pdftoppm", "-r", "300", "-png", str(HTML / "kleinkarten.pdf"), str(PNG / "seite")], check=True)
    for datei, name in zip(sorted(PNG.glob("seite-*.png")), namen):
        datei.rename(PNG / f"{name}.png")
    print(f"Karten.pdf und {len(namen)} Kartenbilder geschrieben")


if __name__ == "__main__":
    main()
