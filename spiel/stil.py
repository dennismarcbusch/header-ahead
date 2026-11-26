"""Gemeinsames Aussehen für Karten und Anleitung (Bitflip: Weiß, Tinte, Amber als Akzent)."""

SCHICHTFARBEN = {
    "l7": "#AEB6C0",   # Daten (Schicht 5–7)
    "l4": "#2660C7",   # TCP
    "l4u": "#6CC0EC",  # UDP
    "l3": "#2B9A5C",   # IP
    "l2": "#FFB020",   # Ethernet / Frame
    "l1": "#2C3139",   # Kabel
}

GRUND = """
:root {
  --tinte: #0B0F14; --flaeche: #F4F6F8; --linie: #D5DBE1; --grau: #5B6672;
  --amber: #FFB020; --amber-text: #A85F00;
  --l7: #AEB6C0; --l4: #2660C7; --l4u: #6CC0EC; --l3: #2B9A5C; --l2: #FFB020; --l1: #2C3139;
}
* { box-sizing: border-box; }
html { font-family: "Inter", sans-serif; color: var(--tinte); font-size: 9.5pt; line-height: 1.4; }
body { margin: 0; }
.mono, th.mono, td.mono { font-family: "JetBrains Mono", monospace; }
h1, h2, h3, .label { font-family: "JetBrains Mono", monospace; }
table { border-collapse: collapse; }
.f-l7 { background: var(--l7); color: var(--tinte); }
.f-l4 { background: var(--l4); color: #fff; }
.f-l4u { background: var(--l4u); color: var(--tinte); }
.f-l3 { background: var(--l3); color: #fff; }
.f-l2 { background: var(--l2); color: var(--tinte); }
.f-l1 { background: var(--l1); color: #fff; }
/* MAC-Adresse: Herstellerteil klein und grau, Geräteteil in der Schrift der Umgebung */
.mac { white-space: nowrap; }
.mac-h { font-size: 0.8em; font-weight: 500; color: var(--grau); }
"""

KARTEN = """
/* --- kleine Karten 80 × 52 mm (liegen in den Fächern der Platten) --- */
.karte { background: #fff; overflow: hidden; position: relative; }
.klein { width: 80mm; height: 52mm; padding: 3mm 3.5mm 2.5mm; font-size: 7.6pt; line-height: 1.3; }
.klein .kopf { display: flex; justify-content: space-between; align-items: baseline;
  border-bottom: 0.8mm solid var(--amber); padding-bottom: 1mm; margin-bottom: 1.6mm; }
.klein .name { font-family: "JetBrains Mono", monospace; font-weight: 800; font-size: 12pt; letter-spacing: 0.01em; }
.klein .art { font-size: 7pt; color: var(--grau); text-align: right; }
.klein table { width: 100%; }
.klein th { text-align: left; font-weight: 500; color: var(--grau); padding: 0.45mm 0; width: 26mm; }
.klein td { font-family: "JetBrains Mono", monospace; font-weight: 700; font-size: 8.6pt; padding: 0.45mm 0; }
.klein .fuss { position: absolute; left: 3.5mm; right: 3.5mm; bottom: 2.4mm; font-size: 7pt; color: var(--tinte);
  border-top: 0.2mm solid var(--linie); padding-top: 1mm; }
.klein .fuss b { font-family: "JetBrains Mono", monospace; }
.tabelle th { font-family: "JetBrains Mono", monospace; font-weight: 700; color: var(--tinte); font-size: 7pt;
  text-transform: uppercase; letter-spacing: 0.04em; border-bottom: 0.2mm solid var(--tinte); width: auto; }
.tabelle td { border-bottom: 0.2mm solid var(--linie); padding: 0.75mm 0; }
.schichten { padding: 2.4mm 2.6mm; }
.schichten table { width: 100%; font-size: 6.6pt; table-layout: fixed; }
.schichten col.c1 { width: 9mm; } .schichten col.c2 { width: 21.5mm; } .schichten col.c3 { width: 15mm; } .schichten col.c4 { width: 16mm; }
.schichten th { font-family: "JetBrains Mono", monospace; font-size: 5.8pt; text-transform: uppercase; letter-spacing: 0.03em;
  color: var(--grau); font-weight: 700; padding: 0 0.8mm 0.8mm; width: auto; }
.schichten td { font-family: "Inter", sans-serif; font-weight: 500; font-size: 6.7pt; padding: 1mm 0.7mm; line-height: 1.15;
  border-top: 0.5mm solid #fff; vertical-align: middle; }
.schichten td.nr { font-family: "JetBrains Mono", monospace; font-weight: 800; font-size: 9pt; width: 9mm; text-align: center; }
.schichten td.pdu { font-weight: 700; }
.ereignis .name { font-size: 11pt; }
.ereignis p { margin: 0 0 1.4mm; font-size: 7.6pt; }
.ereignis .folge { font-size: 6.8pt; color: var(--grau); }
.stufe { font-family: "JetBrains Mono", monospace; font-weight: 700; font-size: 6.5pt; background: var(--tinte); color: #fff;
  padding: 0.3mm 1.4mm; border-radius: 1mm; }

/* --- Auftragskarten 70 × 100 mm --- */
.auftrag { width: 70mm; height: 100mm; padding: 4mm 4.5mm; font-size: 8.6pt; }
.auftrag .oben { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2.5mm; }
.auftrag .nr { font-family: "JetBrains Mono", monospace; font-weight: 800; font-size: 9pt; letter-spacing: 0.06em; }
.auftrag .balken { height: 1.6mm; background: var(--amber); margin: 0 -4.5mm 4mm; }
.auftrag .text { font-size: 11pt; line-height: 1.32; font-weight: 500; min-height: 31mm; }
.auftrag .wer { margin-top: 3mm; border-top: 0.2mm solid var(--linie); }
.auftrag .wer div { display: flex; justify-content: space-between; border-bottom: 0.2mm solid var(--linie); padding: 1.3mm 0; }
.auftrag .wer span:first-child { color: var(--grau); }
.auftrag .wer span:last-child { font-family: "JetBrains Mono", monospace; font-weight: 800; font-size: 10pt; }
.auftrag .unten { position: absolute; left: 4.5mm; right: 4.5mm; bottom: 4mm; display: flex; justify-content: space-between;
  align-items: flex-end; font-size: 7.4pt; color: var(--grau); }
.auftrag .punkte { font-family: "JetBrains Mono", monospace; font-weight: 800; font-size: 15pt; color: var(--tinte); line-height: 1; }
.auftrag .zurueck { font-family: "JetBrains Mono", monospace; font-weight: 700; color: var(--amber-text); font-size: 8pt; }
.loesung { font-size: 7.3pt; background: var(--flaeche); }
.loesung .oben { margin-bottom: 1.6mm; }
.loesung .weg { font-family: "JetBrains Mono", monospace; font-size: 6.6pt; font-weight: 500; line-height: 1.35; margin-bottom: 1.8mm; }
.loesung h4 { font-family: "JetBrains Mono", monospace; font-size: 6.4pt; text-transform: uppercase; letter-spacing: 0.05em;
  margin: 1.6mm 0 0.8mm; color: var(--tinte); }
.kopfzeilen { width: 100%; font-size: 7pt; }
.kopfzeilen td { padding: 0.55mm 1.2mm; border-top: 0.35mm solid var(--flaeche); }
.kopfzeilen td.teil { font-family: "JetBrains Mono", monospace; font-weight: 800; font-size: 6.2pt; width: 12.5mm; }
.kopfzeilen td.feld { background: #fff; color: var(--grau); width: 17mm; }
.kopfzeilen td.wert { background: #fff; font-family: "JetBrains Mono", monospace; font-weight: 700; }
.loesung .strecke1 { font-size: 6.7pt; margin-top: 1.4mm; line-height: 1.3; }
.loesung .strecke1 b { font-family: "JetBrains Mono", monospace; }
.loesung .merke { position: absolute; left: 4.5mm; right: 4.5mm; bottom: 3.2mm; font-size: 6.7pt; line-height: 1.28;
  border-top: 0.6mm solid var(--amber); padding-top: 1.1mm; }
"""
