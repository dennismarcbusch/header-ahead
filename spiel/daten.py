"""Spieldaten für Header Ahead: Netz, Adressen, Dienste, Aufträge.

Alles, was auf Plättchen, Karten und in den Lösungen steht, kommt aus dieser
Datei. Die Lösungen werden daraus berechnet (loesung.py), nicht abgetippt.
"""

# --- Herkunft und Lizenz (stehen in der Anleitung und auf den Kartenbögen) -----
URHEBER = "Dennis Busch"
LIZENZ = "CC BY-SA 4.0"
QUELLE = "github.com/dennismarcbusch/header-ahead"

# --- Geräte -----------------------------------------------------------------
# MAC-Adressen stehen vollständig da (sechs Bytes). Die ersten drei Bytes sind der
# Herstellerteil, die letzten drei der Geräteteil. Alle Hosts haben denselben
# Herstellerteil, der Router einen anderen: Zum Suchen und Vergleichen reicht so
# der Geräteteil, der auf Plättchen und Karten groß gedruckt ist.

HERSTELLER_HOST = "00:1B:44"
HERSTELLER_ROUTER = "A8:5E:45"

HOSTS = {
    "PC 1": {
        "art": "Client", "netz": "A", "ip": "10.0.1.11", "mac": f"{HERSTELLER_HOST}:4C:A1:07",
        "gateway": "10.0.1.1", "dienste": [],
    },
    "PC 2": {
        "art": "Client", "netz": "A", "ip": "10.0.1.12", "mac": f"{HERSTELLER_HOST}:9E:32:F4",
        "gateway": "10.0.1.1", "dienste": [],
    },
    "INTRA": {
        "art": "Server im eigenen Netz", "netz": "A", "ip": "10.0.1.20",
        "mac": f"{HERSTELLER_HOST}:2A:F3:6C", "gateway": "10.0.1.1",
        "dienste": ["HTTP", "DNS", "NTP"],
    },
    "WEB": {
        "art": "Server im fremden Netz", "netz": "B", "ip": "10.0.2.10",
        "mac": f"{HERSTELLER_HOST}:7C:3F:94", "gateway": "10.0.2.1",
        "dienste": ["HTTPS", "SMTP"],
    },
}

ROUTER = {
    "name": "ROUTER",
    "A": {"ip": "10.0.1.1", "mac": f"{HERSTELLER_ROUTER}:E0:15:0A", "netz": "10.0.1.0/24"},
    "B": {"ip": "10.0.2.1", "mac": f"{HERSTELLER_ROUTER}:E0:15:0B", "netz": "10.0.2.0/24"},
}


def mac_teile(mac):
    """Teilt eine MAC-Adresse in Herstellerteil und Geräteteil (je drei Bytes)."""
    teile = mac.split(":")
    return ":".join(teile[:3]), ":".join(teile[3:])


def mac_plaettchen(mac):
    """Text eines MAC-Plättchens: zwei Zeilen, oben der Herstellerteil, unten der Geräteteil."""
    hersteller, geraet = mac_teile(mac)
    return f"{hersteller}:\n{geraet}"

NETZE = {"A": "10.0.1.0/24", "B": "10.0.2.0/24"}

# Switch im Netz A: Port -> Gerät. Port 3 führt zum Router (Schnittstelle A).
SWITCH_PORTS = {1: "INTRA", 2: "PC 1", 3: "ROUTER", 4: "PC 2"}

# --- Dienste ----------------------------------------------------------------
DIENSTE = {
    "HTTP":  {"port": 80,  "transport": "TCP", "wozu": "Webseite ohne Verschlüsselung"},
    "HTTPS": {"port": 443, "transport": "TCP", "wozu": "Webseite mit Verschlüsselung"},
    "DNS":   {"port": 53,  "transport": "UDP", "wozu": "Namen in IP-Adressen auflösen"},
    "NTP":   {"port": 123, "transport": "UDP", "wozu": "Uhrzeit abgleichen"},
    "SMTP":  {"port": 25,  "transport": "TCP", "wozu": "E-Mail versenden"},
}

CLIENT_PORTS = [49152, 50001, 51515, 60000]

# --- Plättchen (Text, Anzahl) -----------------------------------------------
def plaettchen():
    mac = [h["mac"] for h in HOSTS.values()] + [ROUTER["A"]["mac"], ROUTER["B"]["mac"]]
    ip = [h["ip"] for h in HOSTS.values()] + [ROUTER["A"]["ip"], ROUTER["B"]["ip"]]
    return {
        "mac": [(mac_plaettchen(m), 2) for m in mac],
        "ip": [(i, 2) for i in ip],
        "port": [(str(d["port"]), 2) for d in DIENSTE.values()]
                + [(str(p), 1) for p in CLIENT_PORTS],
        "protokoll": [(name, 2) for name in DIENSTE],
    }

# --- Aufträge ---------------------------------------------------------------
# stufe: ab welcher Stufe die Karte mitspielt. antwort: der Empfänger schickt
# danach eine Antwort zurück. Die Texte nennen Geräte und Dienst in Alltags-
# sprache, aber keine Adressen: die schlägt man im Netzplan nach.

AUFTRAEGE = [
    # Stufe 1: alles im Netz A
    {"nr": 1,  "stufe": 1, "von": "PC 1",  "nach": "INTRA", "dienst": "HTTP",  "antwort": False,
     "text": "Du öffnest auf PC 1 die Startseite im Intranet."},
    {"nr": 2,  "stufe": 1, "von": "PC 2",  "nach": "INTRA", "dienst": "HTTP",  "antwort": False,
     "text": "Auf PC 2 lädt jemand den Speiseplan aus dem Intranet."},
    {"nr": 3,  "stufe": 1, "von": "PC 1",  "nach": "INTRA", "dienst": "DNS",   "antwort": False,
     "text": "PC 1 kennt nur einen Namen und fragt nach der IP-Adresse dazu."},
    {"nr": 4,  "stufe": 1, "von": "PC 2",  "nach": "INTRA", "dienst": "DNS",   "antwort": False,
     "text": "PC 2 will wissen, welche IP-Adresse hinter einem Namen steckt."},
    {"nr": 5,  "stufe": 1, "von": "PC 1",  "nach": "INTRA", "dienst": "NTP",   "antwort": False,
     "text": "Die Uhr von PC 1 geht falsch. Er fragt nach der genauen Zeit."},
    {"nr": 6,  "stufe": 1, "von": "PC 2",  "nach": "INTRA", "dienst": "NTP",   "antwort": False,
     "text": "PC 2 gleicht nach dem Hochfahren seine Uhrzeit ab."},
    {"nr": 7,  "stufe": 1, "von": "PC 1",  "nach": "INTRA", "dienst": "HTTP",  "antwort": True,
     "text": "PC 1 ruft die Vertretungsplan-Seite im Intranet auf und wartet auf die Seite."},
    {"nr": 8,  "stufe": 1, "von": "PC 2",  "nach": "INTRA", "dienst": "DNS",   "antwort": True,
     "text": "PC 2 fragt nach einer IP-Adresse und braucht die Auskunft zurück."},
    # Stufe 2: über den Router ins Netz B, gemischt mit Zielen im eigenen Netz
    {"nr": 9,  "stufe": 2, "von": "PC 1",  "nach": "WEB",   "dienst": "HTTPS", "antwort": False,
     "text": "Du öffnest auf PC 1 eine verschlüsselte Webseite draußen im Netz."},
    {"nr": 10, "stufe": 2, "von": "PC 2",  "nach": "WEB",   "dienst": "HTTPS", "antwort": False,
     "text": "Auf PC 2 meldet sich jemand in einem Webshop an."},
    {"nr": 11, "stufe": 2, "von": "PC 1",  "nach": "WEB",   "dienst": "SMTP",  "antwort": False,
     "text": "PC 1 verschickt eine E-Mail über den Mailserver draußen."},
    {"nr": 12, "stufe": 2, "von": "INTRA", "nach": "WEB",   "dienst": "SMTP",  "antwort": False,
     "text": "Der Intranet-Server meldet per E-Mail, dass seine Festplatte voll ist."},
    {"nr": 13, "stufe": 2, "von": "PC 2",  "nach": "INTRA", "dienst": "DNS",   "antwort": False,
     "text": "PC 2 fragt den Server im eigenen Netz nach einer IP-Adresse."},
    {"nr": 14, "stufe": 2, "von": "PC 1",  "nach": "INTRA", "dienst": "HTTP",  "antwort": False,
     "text": "PC 1 öffnet die Intranet-Seite. Achtung: Wo steht der Server?"},
    {"nr": 15, "stufe": 2, "von": "PC 2",  "nach": "WEB",   "dienst": "SMTP",  "antwort": False,
     "text": "PC 2 schickt eine Bewerbung per E-Mail ab."},
    {"nr": 16, "stufe": 2, "von": "PC 1",  "nach": "WEB",   "dienst": "HTTPS", "antwort": True,
     "text": "PC 1 ruft eine verschlüsselte Webseite auf und wartet auf die Seite."},
    {"nr": 17, "stufe": 2, "von": "PC 2",  "nach": "WEB",   "dienst": "HTTPS", "antwort": True,
     "text": "PC 2 lädt ein Video-Vorschaubild von draußen und wartet darauf."},
    {"nr": 18, "stufe": 2, "von": "INTRA", "nach": "WEB",   "dienst": "HTTPS", "antwort": True,
     "text": "Der Intranet-Server holt sich ein Update von draußen und wartet auf die Datei."},
]

# --- Ereignisse (Erweiterung für Stufe 3) -----------------------------------
EREIGNISSE = [
    {"titel": "Freie Leitung", "anzahl": 6,
     "text": "Nichts passiert. Der Auftrag läuft ganz normal."},
    {"titel": "Bitfehler", "anzahl": 4,
     "text": "Auf der ersten Teilstrecke kippt ein Bit. Sobald die Schale die "
             "erste Station verlassen hat, dreht ihr das FCS-Plättchen auf Rot.",
     "folge": "Die nächste Station prüft die FCS und verwirft den Frame. "
              "TCP: Der Absender merkt, dass keine Bestätigung kommt, und "
              "schickt alles noch einmal. UDP: Die Nachricht ist verloren, "
              "der Auftrag zählt nicht."},
    {"titel": "Volllast", "anzahl": 2,
     "text": "Deckt sofort einen zweiten Auftrag auf. Beide Dateneinheiten "
             "sind gleichzeitig unterwegs."},
]
