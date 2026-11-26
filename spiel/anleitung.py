"""Setzt die Spielanleitung als PDF.

Aufruf (aus dem Ordner header-ahead):  python3 spiel/anleitung.py

Braucht die Bilder aus bilder/ (cad/rendern.py) und druck/teileliste.json (cad/bauen.py).
"""

import json
import subprocess
import sys
from pathlib import Path

from PIL import Image

HIER = Path(__file__).resolve().parent
WURZEL = HIER.parent
sys.path.insert(0, str(HIER))

from daten import AUFTRAEGE, EREIGNISSE, LIZENZ, QUELLE, URHEBER, plaettchen  # noqa: E402
from loesung import ALLE  # noqa: E402
from stil import GRUND  # noqa: E402

HTML = HIER / "_html"
BILDER = HTML / "bilder"

TEILNAMEN = {
    "frame_schale": "Frame-Schale", "ip_header": "IP-Header", "tcp_header": "TCP-Header",
    "udp_header": "UDP-Header", "daten_block": "Daten-Block", "fcs_plaettchen": "FCS-Plättchen",
    "stoerungs_chip": "Störungs-Chip", "kabel": "Kabel", "platte_host": "Host-Platte",
    "platte_switch": "Switch-Platte", "platte_router": "Router-Platte", "switch_tunnel": "Switch-Tunnel",
    "router_dach": "Router-Dach", "vorratskasten": "Vorratskasten",
    "plaettchen_mac": "Plättchen MAC", "plaettchen_ip": "Plättchen IP",
    "plaettchen_port": "Plättchen Ports", "plaettchen_protokoll": "Plättchen Protokolle",
}
FARBNAMEN = {"hellgrau": "Hellgrau", "weiss": "Weiß", "silber": "Silber", "blau": "Blau", "hellblau": "Hellblau",
             "gruen": "Grün", "orange": "Orange", "anthrazit": "Anthrazit", "schwarz": "Schwarz", "rot": "Rot"}


def bild(name, breite=1500):
    """Verkleinerte JPEG-Kopie eines Renderings für das PDF; gibt den relativen Pfad zurück."""
    BILDER.mkdir(parents=True, exist_ok=True)
    quelle = WURZEL / "bilder" / f"{name}.png"
    ziel = BILDER / f"{name}.jpg"
    im = Image.open(quelle).convert("RGB")
    if im.width > breite:
        im = im.resize((breite, round(im.height * breite / im.width)), Image.LANCZOS)
    im.save(ziel, quality=88)
    return f"bilder/{name}.jpg"


def abbildung(name, text, klasse="", breite=1500):
    return f'<figure class="{klasse}"><img src="{bild(name, breite)}" alt=""><figcaption>{text}</figcaption></figure>'


def druckliste():
    daten = json.loads((WURZEL / "druck" / "teileliste.json").read_text())
    zeilen, volumen = [], 0.0
    for t in daten["teile"]:
        volumen += t["volumen_cm3"] * t["anzahl"]
        l, b, h = t["masse_mm"]
        zeilen.append(
            f"<tr><td>{TEILNAMEN[t['name']]}</td><td class='z'>{t['anzahl']}</td>"
            f"<td class='eng'>{FARBNAMEN[t['farbe']]}<span class='grau'> / {FARBNAMEN[t['schriftfarbe']]}</span></td>"
            f"<td class='z'>{l:.0f} × {b:.0f} × {h:.0f}</td><td class='mono klein'>{t['name']}</td>"
            f"<td class='klein'>{t['hinweis']}</td></tr>")
    return "".join(zeilen), volumen


def baue():
    sorten = plaettchen()
    anzahl = {s: sum(n for _, n in e) for s, e in sorten.items()}
    plaettchen_gesamt = sum(anzahl.values())
    ereignisse = sum(e["anzahl"] for e in EREIGNISSE)
    stufe1 = [l for l in ALLE if l["stufe"] == 1]
    stufe2 = [l for l in ALLE if l["stufe"] == 2]
    punkte1, punkte2 = sum(l["punkte"] for l in stufe1), sum(l["punkte"] for l in stufe2)
    zeilen, volumen = druckliste()

    return f"""<!doctype html>
<html lang="de"><head><meta charset="utf-8"><title>Header Ahead · Spielanleitung</title>
<style>{GRUND}{CSS}{CSS_LIZENZ}</style></head><body>

<section class="titel">
  <div class="kopfband"><span class="marke">bitflip_</span><span>Lern-Tabletops · ITS 10. Klasse</span></div>
  <h1>Header Ahead</h1>
  <p class="unter">Ein Lern-Tabletop zu den Schichtenmodellen ISO/OSI und TCP/IP</p>
  <div class="eckdaten">
    <div><b>2–6</b><span>Spielende</span></div>
    <div><b>30 Min</b><span>mit Aufbau</span></div>
    <div><b>gemeinsam</b><span>alle gegen die Uhr</span></div>
    <div><b>3 Stufen</b><span>vom Switch bis zum Störfall</span></div>
  </div>
  <img class="held" src="{bild('titel', 1700)}" alt="">
  <div class="spalten2 einstieg">
    <div>
      <h3>Worum es geht</h3>
      <p>Ihr seid gemeinsam das Netz. Ein Auftrag kommt herein, zum Beispiel: PC 1 ruft eine Webseite auf.
      Der Absender verpackt die Daten Schicht für Schicht. Switch und Router reichen sie weiter. Der Empfänger
      packt sie wieder aus.</p>
      <p>Jede Station liest nur, was ihre Schicht angeht. Kommt alles richtig an, gibt es Punkte.
      Passt etwas nicht, bleibt die Dateneinheit hängen, genau wie im echten Netz.</p>
    </div>
    <div>
      <h3>Das könnt ihr danach</h3>
      <ul>
        <li>die Schichten beider Modelle nennen und einander zuordnen,</li>
        <li>erklären, wie aus Daten ein Segment, ein Paket und ein Frame wird,</li>
        <li>sagen, welche Adresse zu welcher Schicht gehört: Port, IP, MAC,</li>
        <li>begründen, warum sich am Router die MAC-Adressen ändern und die IP-Adressen nicht.</li>
      </ul>
    </div>
  </div>
</section>

<section>
  <h2><span>1</span>Spielmaterial</h2>
  {abbildung('material', 'Gedruckte Teile eines Satzes; von den sechs Kabeln sind drei im Bild. Platten und Blenden zeigen die Abschnitte 3 und 4.', 'mittel')}
  <div class="spalten2">
    <div>
      <h3>Aus dem 3D-Drucker</h3>
      <table class="liste">
        <tr><td class="z">4</td><td>Host-Platten</td></tr>
        <tr><td class="z">1</td><td>Switch-Platte mit Tunnel</td></tr>
        <tr><td class="z">1</td><td>Router-Platte mit Dach</td></tr>
        <tr><td class="z">6</td><td>Kabel (5 im Spiel, 1 Reserve)</td></tr>
        <tr><td class="z">3</td><td>Frame-Schalen</td></tr>
        <tr><td class="z">3</td><td>IP-Header</td></tr>
        <tr><td class="z">2 + 2</td><td>TCP-Header und UDP-Header</td></tr>
        <tr><td class="z">3</td><td>Daten-Blöcke</td></tr>
        <tr><td class="z">{plaettchen_gesamt}</td><td>Plättchen: {anzahl['mac']} MAC, {anzahl['ip']} IP, {anzahl['port']} Ports, {anzahl['protokoll']} Protokolle</td></tr>
        <tr><td class="z">4</td><td>FCS-Plättchen (grün: in Ordnung, rot: Bitfehler)</td></tr>
        <tr><td class="z">6</td><td>Störungs-Chips</td></tr>
        <tr><td class="z">1</td><td>Vorratskasten für die Plättchen</td></tr>
      </table>
    </div>
    <div>
      <h3>Auf Papier (Karten.pdf)</h3>
      <table class="liste">
        <tr><td class="z">2</td><td>Netzpläne (Stufe 1, Stufe 2 und 3)</td></tr>
        <tr><td class="z">4</td><td>Gerätekarten: PC 1, PC 2, INTRA, WEB</td></tr>
        <tr><td class="z">3</td><td>Tabellenkarten: MAC-Tabelle, Schnittstellen, Routing-Tabelle</td></tr>
        <tr><td class="z">5</td><td>Schichtenkarten</td></tr>
        <tr><td class="z">{len(AUFTRAEGE)}</td><td>Auftragskarten, Lösung auf der Rückseite</td></tr>
        <tr><td class="z">{ereignisse}</td><td>Ereigniskarten (nur Stufe 3)</td></tr>
      </table>
      <h3>Außerdem</h3>
      <p>Eine Uhr oder ein Handy für die 25 Minuten Spielzeit.</p>
    </div>
  </div>
  {abbildung('dateneinheit', 'So sieht eine fertig gesteckte Dateneinheit aus: PC 1 ruft eine Intranet-Seite auf dem Server INTRA ab.', 'schmal')}
</section>

<section>
  <h2><span>2</span>Die Dateneinheit</h2>
  <p>Was durchs Netz wandert, besteht aus Bausteinen. Jeder Baustein gehört zu einer Schicht und hat Fächer für die
  Adressen dieser Schicht. Die Farbe verrät die Schicht, auch auf der Schichtenkarte.</p>
  {abbildung('dateneinheit_teile', 'Oben die Frame-Schale mit Ethernet-Header und FCS. Unten von links: IP-Header, TCP-Header, Daten-Block, jeweils mit ihren Plättchen.', 'mittel')}
  <table class="tafel">
    <tr><th>Baustein</th><th>OSI-Schicht</th><th>TCP/IP-Schicht</th><th>Fächer</th><th>Das Ganze heißt jetzt</th></tr>
    <tr><td><i class="f-l7"></i>Daten-Block</td><td>5–7 Sitzung, Darstellung, Anwendung</td><td>Anwendung</td><td>Protokoll</td><td><b>Daten</b></td></tr>
    <tr><td><i class="f-l4"></i><i class="f-l4u"></i>TCP- oder UDP-Header</td><td>4 Transport</td><td>Transport</td><td>Quell-Port, Ziel-Port</td><td><b>Segment</b> (bei UDP: Datagramm)</td></tr>
    <tr><td><i class="f-l3"></i>IP-Header</td><td>3 Vermittlung</td><td>Internet</td><td>Quell-IP, Ziel-IP</td><td><b>Paket</b></td></tr>
    <tr><td><i class="f-l2"></i>Frame-Schale</td><td>2 Sicherung</td><td>Netzzugang</td><td>Ziel-MAC, Quell-MAC, FCS</td><td><b>Frame</b></td></tr>
    <tr><td><i class="f-l1"></i>Kabel</td><td>1 Bitübertragung</td><td>Netzzugang</td><td>keine</td><td><b>Bits</b></td></tr>
  </table>
  <div class="spalten2">
    <div>
      <h3>So wird gesteckt</h3>
      <ul>
        <li>Ein Header kommt immer <b>vorn</b> an das, was schon da ist: von oben auf den Zapfen setzen.</li>
        <li>Die Zapfen passen nur in der richtigen Reihenfolge: erst Daten, dann Transport, dann IP.</li>
        <li>Die Frame-Schale ist ein Rahmen. Vorn sitzt der Ethernet-Header, hinten die Prüfsumme (FCS).
        Das Paket liegt dazwischen.</li>
        <li>Plättchen greift ihr an der offenen Seite ihres Fachs.</li>
      </ul>
    </div>
    <div>
      <h3>Gut zu wissen</h3>
      <ul>
        <li>Im Ethernet-Header steht das <b>Ziel zuerst</b>, im IP- und im TCP-Header die Quelle zuerst.
        So ist es auch in echt, und so zeigt es Wireshark.</li>
        <li>Die Dateneinheit liegt immer so, dass ihr die Schrift lesen könnt: Header links.</li>
        <li>Auf einem MAC-Plättchen steht die ganze Adresse: oben klein der Teil des Herstellers, unten groß
        der Teil des Geräts. Zum Suchen und Vergleichen reicht die große Zeile.</li>
        <li>Der Daten-Block nennt die Schichten 5 bis 7 einzeln. Im TCP/IP-Modell sind sie eine einzige: Anwendung.</li>
      </ul>
    </div>
  </div>
</section>

<section>
  <h2><span>3</span>Aufbau</h2>
  <div class="spalten2 bilder">
    {abbildung('spielbrett_stufe1', '<b>Stufe 1:</b> Switch in der Mitte. INTRA an P1, PC 1 an P2, PC 2 an P4.', breite=1100)}
    {abbildung('spielbrett_oben', '<b>Stufe 2 und 3:</b> zusätzlich der Router an P3 und dahinter WEB.', breite=1100)}
  </div>
  <ol class="schritte">
    <li><b>Platten auslegen.</b> Legt den Netzplan der Stufe bereit und baut die Platten wie im Bild auf. Ein Kabel
    verbindet je zwei Platten: Nasen von oben in die Aussparungen drücken. Der Anschluss einer Host-Platte ist links
    an der Bucht, beim Router sind es A (links) und B (rechts). Anschluss A zeigt zum Switch.</li>
    <li><b>Karten einlegen.</b> In jede Host-Platte kommen eine Gerätekarte und eine Schichtenkarte. Die Gerätekarte
    bestimmt, welches Gerät die Platte ist. In den Switch kommt die MAC-Tabelle, in den Router kommen Schnittstellen
    und Routing-Tabelle.</li>
    <li><b>Vorrat bereitstellen.</b> Vorratskasten mit den Plättchen, dazu Bausteine, Schalen, FCS-Plättchen und
    Störungs-Chips so hinlegen, dass alle herankommen.</li>
    <li><b>Aufträge mischen.</b> Die Auftragskarten der Stufe mischen und mit der Auftragsseite nach oben stapeln.
    Die Lösungen liegen unten und bleiben dort.</li>
    <li><b>Stationen verteilen</b> (siehe Tabelle) und die Uhr auf 25 Minuten stellen.</li>
  </ol>
  <h3>Wer bedient was?</h3>
  <table class="tafel rollen">
    <tr><th>Spielende</th><th>Stufe 1</th><th>Stufe 2 und 3</th></tr>
    <tr><td>2</td><td>PC 1 + PC 2 · Switch + INTRA</td><td>PC 1 + PC 2 + INTRA · Switch + Router + WEB</td></tr>
    <tr><td>3</td><td>PC 1 + PC 2 · Switch · INTRA</td><td>PC 1 + PC 2 · Switch + Router · INTRA + WEB</td></tr>
    <tr><td>4</td><td>PC 1 · PC 2 · Switch · INTRA</td><td>PC 1 · PC 2 · Switch + Router · INTRA + WEB</td></tr>
    <tr><td>5</td><td>wie 4, dazu die Leitstelle</td><td>PC 1 · PC 2 · Switch · Router · INTRA + WEB</td></tr>
    <tr><td>6</td><td>wie 5, PC 1 und PC 2 doppelt besetzt</td><td>jede Platte eine Person</td></tr>
  </table>
  <p class="hinweis"><b>Leitstelle:</b> liest die Aufträge vor, verwaltet die Störungs-Chips und vergleicht am Ende mit
  der Lösung. Gibt es keine Leitstelle, übernimmt das, wer gerade nichts zu tun hat. Nach jedem Auftrag rücken alle
  eine Rolle weiter.</p>
</section>

<section>
  <h2><span>4</span>Ein Auftrag, Schritt für Schritt</h2>
  <p><b>Auftrag aufdecken.</b> Lest die oberste Karte vor. Sie nennt Absender und Empfänger, aber keine Adressen
  und keinen Dienst: Das steht im Netzplan und auf den Gerätekarten. Die Karte wird nicht umgedreht.</p>

  <h3>Der Absender kapselt: von Schicht 7 nach unten</h3>
  <div class="raster3">
    {abbildung('schritt_1', '<b>Schicht 5–7.</b> Daten-Block auf den Montageplatz hinter „5–7 Anwendung“. Protokoll-Plättchen einstecken. Welcher Dienst passt, zeigt die Gerätekarte des Empfängers.', breite=900)}
    {abbildung('schritt_2', '<b>Schicht 4.</b> TCP- oder UDP-Header anstecken (Netzplan, Spalte Transport). Quell-Port: ein freier Client-Port. Ziel-Port: der Port des Dienstes. Das ist jetzt ein Segment.', breite=900)}
    {abbildung('schritt_3', '<b>Schicht 3.</b> IP-Header anstecken. Quell-IP: die eigene. Ziel-IP: die des Empfängers. Das ist jetzt ein Paket.', breite=900)}
    {abbildung('schritt_4', '<b>Schicht 2.</b> Paket nach hinten in die Schale schieben. Quell-MAC: die eigene. Ziel-MAC: siehe Kasten. FCS-Plättchen mit Grün nach oben. Das ist jetzt ein Frame.', breite=900)}
    {abbildung('schritt_5', '<b>Schicht 1.</b> Schale über das Kabel zur nächsten Station schieben.', breite=900)}
    <div class="kasten">
      <h4>Die wichtigste Frage: Welche Ziel-MAC?</h4>
      <p>Liegt der Empfänger im <b>eigenen Netz</b>? Dann ist die Ziel-MAC die des Empfängers.</p>
      <p>Liegt er in einem <b>fremden Netz</b>? Dann ist die Ziel-MAC die des Standard-Gateways, also des Routers.
      Die Ziel-IP bleibt trotzdem die des Empfängers.</p>
    </div>
  </div>

  <div class="spalten2 stationen">
    <div>
      {abbildung('switch', 'Der Switch sieht nur den Ethernet-Header und die FCS.', breite=1000)}
      <h3>Der Switch leitet weiter</h3>
      <ol>
        <li>Schale in den Tunnel schieben, bis links der Ethernet-Header und rechts die FCS herausschauen.</li>
        <li>Ist das FCS-Plättchen grün?</li>
        <li>Ziel-MAC in der MAC-Tabelle suchen.</li>
        <li>Schale am genannten Port aufs Kabel setzen und weiterschieben.</li>
      </ol>
      <p>Der Switch fasst kein Plättchen an und holt nichts aus der Schale.</p>
    </div>
    <div>
      {abbildung('router', 'Der Router hat das Paket aus dem alten Frame geholt und baut einen neuen.', breite=1000)}
      <h3>Der Router packt um (ab Stufe 2)</h3>
      <ol>
        <li>Schale in die Bucht. FCS grün? Gehört die Ziel-MAC zu dem Anschluss, an dem die Schale ankam?</li>
        <li>Paket nach vorn aus der Schale schieben, unter das Dach. Sichtbar bleibt nur der IP-Header.</li>
        <li>Alte Schale leeren und zurück in den Vorrat. Dieser Frame hat ausgedient.</li>
        <li>Ziel-IP lesen. In der Routing-Tabelle das Zielnetz suchen: Dort steht der Anschluss.</li>
        <li>Frische Schale in die Bucht, Paket hineinschieben. Quell-MAC: die des Ausgangs-Anschlusses.
        Ziel-MAC: die des nächsten Halts, bei „direkt“ die des Empfängers. FCS grün.</li>
        <li>Schale am Ausgangs-Anschluss weiterschieben.</li>
      </ol>
    </div>
  </div>

  <h3>Der Empfänger prüft und entkapselt: von Schicht 1 nach oben</h3>
  <ol class="schritte">
    <li><b>Kontrolle.</b> Die Schale liegt in der Bucht des Empfängers. Die Leitstelle dreht die Auftragskarte um und
    vergleicht jedes Feld mit dem Kasten „So kommt sie an“. Stimmt ein Feld nicht, ist das eine Störung.</li>
    <li><b>Schicht 2.</b> FCS grün, Ziel-MAC ist meine: Paket nach vorn herausschieben, Schale leeren.</li>
    <li><b>Schicht 3.</b> Ziel-IP ist meine: IP-Header nach oben abheben.</li>
    <li><b>Schicht 4.</b> Läuft auf dem Ziel-Port ein Dienst bei mir? Dann Transport-Header abheben.</li>
    <li><b>Schicht 5–7.</b> Übrig bleiben die Daten für die Anwendung. Die Auftragskarte kommt auf den Stapel
    „Zugestellt“, alle Teile gehen zurück in den Vorrat.</li>
  </ol>
  <p class="hinweis"><b>Aufträge mit Antwort (↩):</b> Nach der Kontrolle schickt der Empfänger sofort die Antwort zurück.
  Der Daten-Block bleibt. Bei Ports, IP-Adressen und MAC-Adressen tauschen Quelle und Ziel die Plätze.
  Beim ursprünglichen Absender wird mit dem zweiten Kasten der Lösung verglichen.</p>
</section>

<section>
  <h2><span>5</span>Störungen, Ende und Wertung</h2>
  <div class="spalten2">
    <div>
      <h3>Wann es eine Störung gibt</h3>
      <ul>
        <li>Das FCS-Plättchen fehlt oder zeigt Rot, ohne dass eine Ereigniskarte das verlangt.</li>
        <li>Die Ziel-MAC steht nicht in der MAC-Tabelle des Switches.</li>
        <li>Die Ziel-MAC gehört nicht zum Anschluss des Routers oder nicht zum Empfänger.</li>
        <li>Das Zielnetz steht nicht in der Routing-Tabelle.</li>
        <li>Die Ziel-IP gehört nicht zum Empfänger, oder der Dienst läuft dort nicht.</li>
        <li>Bei der Kontrolle stimmt ein Feld nicht mit der Lösung überein.</li>
      </ul>
    </div>
    <div>
      <h3>Was dann passiert</h3>
      <ol>
        <li>Die Station sagt, <b>was</b> nicht passt. Sie sagt nicht, was richtig wäre.</li>
        <li>Die Gruppe nimmt einen Störungs-Chip.</li>
        <li>Die Dateneinheit geht zurück an die Station, die das betroffene Feld gefüllt hat. Sie bessert nach.</li>
        <li>Besprecht kurz, warum es nicht gepasst hat. Das ist der wichtigste Moment im Spiel.</li>
      </ol>
    </div>
  </div>
  <p class="hinweis"><b>Helfen:</b> An jeder Station entscheidet, wer dort sitzt, und nur diese Person fasst die Teile an.
  Fragen und Tipps sind erlaubt.</p>

  <h3>Spielende und Wertung</h3>
  <p>Das Spiel endet, wenn die 25 Minuten um sind oder alle Aufträge zugestellt wurden. Ein Auftrag, der beim
  Klingeln unterwegs ist, wird noch zu Ende gebracht. Zählt die Punkte der zugestellten Karten zusammen und zieht
  für jeden Störungs-Chip einen Punkt ab.</p>
  <table class="tafel wertung">
    <tr><th>Punkte</th><th>Rang</th></tr>
    <tr><td>ab 4</td><td>Bote</td></tr>
    <tr><td>ab 7</td><td>Kurier</td></tr>
    <tr><td>ab 10</td><td>Expresskurier</td></tr>
  </table>
  <p class="grau">Die Schwellen sind Richtwerte und noch nicht im Unterricht erprobt.
  In Stufe 1 sind höchstens {punkte1} Punkte möglich, in Stufe 2 höchstens {punkte2}.</p>

  <h2><span>6</span>Die drei Stufen</h2>
  <table class="tafel stufen">
    <tr><th>Stufe</th><th>Aufbau</th><th>Karten</th><th>Darum geht es</th></tr>
    <tr><td><b>1 · Ein Netz</b></td><td>PC 1, PC 2, INTRA, Switch</td><td>Aufträge 1–{len(stufe1)}</td>
      <td>Kapseln und Entkapseln, Segment, Paket, Frame, TCP oder UDP, der Switch und seine MAC-Tabelle.</td></tr>
    <tr><td><b>2 · Über den Router</b></td><td>zusätzlich Router und WEB</td><td>Aufträge {len(stufe1) + 1}–{len(ALLE)}</td>
      <td>Eigenes oder fremdes Netz, Standard-Gateway, neuer Frame am Router, IP-Adressen bleiben gleich.</td></tr>
    <tr><td><b>3 · Störfälle</b></td><td>wie Stufe 2</td><td>Aufträge {len(stufe1) + 1}–{len(ALLE)} und Ereigniskarten</td>
      <td>Vor jedem Auftrag eine Ereigniskarte aufdecken: Bitfehler und FCS, TCP wiederholt, UDP nicht,
      zwei Dateneinheiten gleichzeitig.</td></tr>
  </table>
  <p class="hinweis"><b>Bitfehler:</b> Sobald die Schale die erste Station verlassen hat, dreht die Leitstelle das
  FCS-Plättchen auf Rot. Die nächste Station verwirft den Frame, das kostet keinen Störungs-Chip. Bei TCP baut der
  Absender alles noch einmal und schickt es erneut. Bei UDP ist die Nachricht verloren, die Auftragskarte zählt nicht.</p>
</section>

<section>
  <h2><span>7</span>Für Lehrkräfte</h2>
  <div class="spalten2">
    <div>
      <h3>Einsatz</h3>
      <ul>
        <li><b>Zeit:</b> etwa 5 Minuten Aufbau und Erklärung, 25 Minuten Spiel, danach 5 bis 10 Minuten Auswertung.</li>
        <li><b>Vorwissen:</b> Die Begriffe MAC-Adresse, IP-Adresse und Port sollten bekannt sein. Stufe 1 trägt auch
        als Einstieg, wenn die Schichtenkarte ausliegt.</li>
        <li><b>Leichter:</b> Netzplan und Schichtenkarte offen lassen, nur Aufträge ohne Antwort spielen.</li>
        <li><b>Schwerer:</b> Schichtenkarten herausnehmen, Stufe 3 mit Ereignissen.</li>
      </ul>
      <h3>Fehler, die das Spiel sichtbar macht</h3>
      <ul>
        <li>Ziel-MAC des Servers statt des Gateways: Der Switch findet sie nicht in seiner Tabelle.</li>
        <li>Am Router die IP-Adressen ändern wollen: Unter dem Dach kommt man an nichts anderes heran, und die
        IP-Plättchen bleiben stecken.</li>
        <li>Quell- und Ziel-Port vertauschen oder bei der Antwort nicht tauschen.</li>
        <li>TCP und UDP verwechseln.</li>
      </ul>
    </div>
    <div>
      <h3>Was das Spiel vereinfacht</h3>
      <ul>
        <li>Alle Hosts haben denselben Herstellerteil in der MAC-Adresse. In echt mischen sich die Hersteller.</li>
        <li>ARP fehlt: Die MAC-Adressen stehen im Netzplan.</li>
        <li>Der Switch hat eine fertige MAC-Tabelle. In echt lernt er sie aus den Quell-Adressen.</li>
        <li>TCP kommt ohne Verbindungsaufbau, Sequenznummern und Bestätigungen aus.</li>
        <li>Die Header zeigen nur die Adressen. Felder wie TTL, Protokoll oder EtherType fehlen.</li>
        <li>Die Schichten 5 bis 7 sind ein Block, die Verschlüsselung bei HTTPS wird nicht gezeigt.</li>
        <li>Es gibt kein NAT. Netz B steht für ein anderes Netz, nicht für das Internet.</li>
        <li>Alle Bausteine sind gleich groß. In echt sind Header klein und Daten groß.</li>
      </ul>
      <h3>Fragen für die Auswertung</h3>
      <ol>
        <li>Welche Adressen haben sich unterwegs geändert, welche nicht? Warum?</li>
        <li>Warum kann der Switch mit der MAC-Adresse von WEB nichts anfangen?</li>
        <li>Was hat der Router gelesen und was nicht? Woran sieht man das am Material?</li>
        <li>Woran erkennt der Empfänger, für welche Anwendung die Daten bestimmt sind?</li>
        <li>Wo steckt in der Dateneinheit das OSI-Modell, wo das TCP/IP-Modell?</li>
      </ol>
    </div>
  </div>
  <p class="hinweis"><b>Stand:</b> Header Ahead ist ein Prototyp. Die Passungen sind am Rechner geprüft, aber noch
  nicht gedruckt. Spielzeit, Punktwerte und Rangschwellen sind Schätzungen, bis das Spiel im Unterricht erprobt ist.</p>
</section>

<section>
  <h2><span>8</span>Drucken</h2>
  <table class="tafel druck">
    <tr><th>Teil</th><th>Anzahl</th><th>Farbe / Schrift</th><th>Größe in mm</th><th>Datei</th><th>Hinweis</th></tr>
    {zeilen}
  </table>
  <div class="spalten2">
    <div>
      <h3>Dateien</h3>
      <ul>
        <li><b>druck/stl/&lt;teil&gt;.stl</b> ist das Teil mit 0,6 mm vertiefter Schrift, in Drucklage.</li>
        <li><b>druck/stl/&lt;teil&gt;_schrift.stl</b> ist die Schrift als Einleger für eine zweite Farbe.</li>
        <li><b>druck/step/&lt;teil&gt;.step</b> enthält beide Körper für die Weiterarbeit im CAD.</li>
      </ul>
      <h3>Zwei Farben oder eine</h3>
      <ul>
        <li><b>Zweifarbig:</b> beide STL-Dateien zusammen laden, als ein Objekt mit mehreren Teilen, und der Schrift
        die zweite Farbe geben.</li>
        <li><b>Einfarbig:</b> nur die erste Datei drucken. Die Schrift ist dann vertieft und lässt sich mit einem
        Lackstift auslegen.</li>
        <li><b>FCS-Plättchen:</b> bei 2,5 mm Höhe die Farbe wechseln, damit eine Seite rot und eine grün wird.
        In der Datei liegt die Seite mit dem X unten.</li>
      </ul>
    </div>
    <div>
      <h3>Einstellungen (Vorschlag)</h3>
      <ul>
        <li>Düse 0,4 mm, Schichthöhe 0,2 mm, PLA oder PETG, 3 Wände, 15 % Füllung.</li>
        <li>Kein Teil braucht Stützen. Tunnel und Dach liegen in den STL-Dateien schon kopfüber. Sie werden in die
        Schlitze der Platte gesteckt, bei Bedarf mit einem Tropfen Kleber.</li>
        <li>Das größte Teil misst 240 × 200 mm.</li>
      </ul>
      <h3>Zuerst die Passung prüfen</h3>
      <p>Druckt zuerst einen IP-Header, einen TCP-Header, einen Daten-Block und ein Plättchen. Die Zapfen sollen
      sich leicht aufsetzen lassen, ohne zu wackeln. Sitzt es zu stramm oder zu locker, ändert ihr den Wert
      <span class="mono">SPIEL</span> in <span class="mono">cad/masse.py</span> (jetzt 0,2 mm je Seite) und baut die
      Teile neu.</p>
      <h3>Material</h3>
      <p>Alle Teile zusammen haben massiv etwa {volumen:.0f} cm³. Bei 15 % Füllung ist grob die Hälfte davon
      Filament. Das ist eine Schätzung, den genauen Wert zeigt der Slicer.</p>
      <h3>Karten</h3>
      <p>Netzpläne und kleine Karten einseitig auf 160-g-Papier. Auftragskarten beidseitig, über die kurze Kante
      gewendet. Probe: Auftrag und Lösung mit derselben Nummer liegen Rücken an Rücken.</p>
    </div>
  </div>
</section>
</body></html>"""


# Lizenzhinweis: in der Fußzeile jeder Seite, auf der Titelseite mit Urheber und Quelle
CSS_LIZENZ = f"""
@page {{ @bottom-left {{ content: "Header Ahead · Spielanleitung · {LIZENZ}"; }} }}
@page :first {{ @bottom-left {{ content: "Header Ahead von {URHEBER} · Lizenz {LIZENZ} · {QUELLE}";
  font-family: "JetBrains Mono", monospace; font-size: 7pt; color: #5B6672; }} }}
"""

CSS = """
@page { size: A4; margin: 15mm 16mm 16mm;
  @bottom-left { content: "Header Ahead · Spielanleitung"; font-family: "JetBrains Mono", monospace; font-size: 7pt; color: #5B6672; }
  @bottom-right { content: counter(page); font-family: "JetBrains Mono", monospace; font-size: 8pt; font-weight: 700; } }
@page :first { margin-top: 12mm; @bottom-left { content: none; } @bottom-right { content: none; } }
html { font-size: 9.4pt; }
section { page-break-before: always; }
section.titel { page-break-before: avoid; }
h1 { font-size: 40pt; font-weight: 800; margin: 7mm 0 0; letter-spacing: -0.02em; line-height: 1; }
h1::after { content: "_"; color: var(--amber); }
h2 { font-size: 15pt; font-weight: 800; margin: 0 0 3.5mm; padding-bottom: 1.8mm; border-bottom: 1.2mm solid var(--amber);
  display: flex; align-items: baseline; gap: 3mm; }
h2 span { background: var(--tinte); color: #fff; font-size: 11pt; padding: 0.4mm 2.4mm; border-radius: 1mm; }
section > h2:not(:first-child) { margin-top: 7mm; }
h3 { font-size: 9.6pt; font-weight: 800; margin: 3.6mm 0 1.2mm; text-transform: uppercase; letter-spacing: 0.04em; }
h4 { font-family: "JetBrains Mono", monospace; font-size: 8.8pt; margin: 0 0 1.4mm; }
p { margin: 0 0 2mm; }
ul, ol { margin: 0 0 2mm; padding-left: 4.4mm; }
li { margin-bottom: 0.9mm; }
.grau { color: var(--grau); } .klein { font-size: 7.4pt; }
.kopfband { display: flex; justify-content: space-between; font-family: "JetBrains Mono", monospace; font-size: 8pt;
  border-bottom: 0.3mm solid var(--tinte); padding-bottom: 1.6mm; }
.marke { font-weight: 800; }
.unter { font-size: 13pt; margin: 2.5mm 0 5mm; color: var(--grau); }
.eckdaten { display: grid; grid-template-columns: repeat(4, 1fr); column-gap: 3mm; margin-bottom: 5mm; }
.eckdaten div { background: var(--flaeche); border-top: 1mm solid var(--amber); padding: 2.2mm 2.8mm; }
.eckdaten b { display: block; font-family: "JetBrains Mono", monospace; font-size: 13pt; font-weight: 800; }
.eckdaten span { font-size: 8pt; color: var(--grau); }
img { max-width: 100%; display: block; }
.held { width: 100%; border-radius: 1.5mm; margin-bottom: 5mm; }
.spalten2 { display: grid; grid-template-columns: 1fr 1fr; column-gap: 7mm; }
.einstieg p { font-size: 10pt; }
figure { margin: 0 0 3mm; }
figure img { width: 100%; border-radius: 1.2mm; }
figure.schmal { width: 56%; margin: 3mm auto 0; }
figure.mittel { width: 72%; margin: 2mm auto 3mm; }
figcaption { font-size: 7.8pt; color: var(--grau); margin-top: 1.2mm; line-height: 1.3; }
figcaption b { color: var(--tinte); }
.liste { width: 100%; }
.liste td { padding: 0.75mm 0; border-bottom: 0.2mm solid var(--linie); vertical-align: top; }
td.z { font-family: "JetBrains Mono", monospace; font-weight: 700; white-space: nowrap; }
.liste td.z { width: 13mm; }
.tafel { width: 100%; margin: 2mm 0 3mm; font-size: 8.6pt; }
.tafel th { text-align: left; font-family: "JetBrains Mono", monospace; font-size: 7.3pt; text-transform: uppercase;
  letter-spacing: 0.04em; border-bottom: 0.4mm solid var(--tinte); padding: 1mm 2mm 1mm 0; }
.tafel td { border-bottom: 0.2mm solid var(--linie); padding: 1.3mm 2mm 1.3mm 0; vertical-align: top; }
.tafel i { display: inline-block; width: 3.2mm; height: 3.2mm; border-radius: 0.6mm; margin-right: 1.4mm; vertical-align: -0.4mm; }
.rollen td:first-child, .wertung td:first-child { font-family: "JetBrains Mono", monospace; font-weight: 800; width: 22mm; }
.wertung { width: 70mm; }
.stufen td:first-child { white-space: nowrap; }
.druck { font-size: 7.5pt; margin-bottom: 1mm; } .druck td { padding: 0.45mm 2mm 0.45mm 0; } .druck td.eng, .druck td:first-child { white-space: nowrap; }
.schritte { padding-left: 5mm; } .schritte li { margin-bottom: 1.5mm; }
.hinweis { background: var(--flaeche); border-left: 1mm solid var(--amber); padding: 2.2mm 3mm; margin: 2.5mm 0; }
.bilder figure { margin-bottom: 3mm; }
.raster3 { display: grid; grid-template-columns: repeat(3, 1fr); column-gap: 4mm; row-gap: 2mm; margin-bottom: 2mm; }
.raster3 figure { margin: 0; }
.kasten { background: var(--tinte); color: #fff; border-radius: 1.5mm; padding: 3.2mm 3.4mm; font-size: 8.4pt; align-self: start; }
.kasten h4 { color: var(--amber); } .kasten p { margin-bottom: 1.6mm; }
.stationen { page-break-before: always; }
.stationen figure { margin-bottom: 1mm; }
.stationen ol, .stationen p { font-size: 8.7pt; }
"""


def main():
    HTML.mkdir(exist_ok=True)
    (HTML / "anleitung.html").write_text(baue(), encoding="utf-8")
    subprocess.run(["weasyprint", "-q", str(HTML / "anleitung.html"), str(WURZEL / "Spielanleitung.pdf")], check=True)
    print("Spielanleitung.pdf geschrieben")


if __name__ == "__main__":
    main()
