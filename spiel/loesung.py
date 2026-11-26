"""Berechnet aus daten.py die Lösung jedes Auftrags: Weg, Header je Teilstrecke, Punkte."""

from daten import AUFTRAEGE, DIENSTE, HOSTS, ROUTER, SWITCH_PORTS

CLIENT_PORT = "Client-Port"          # frei wählbar aus den Client-Ports
SWITCH_NETZ = "A"                    # der Switch steht im Netz A, Netz B hängt direkt am Router


def port_von(geraet):
    return next(p for p, name in SWITCH_PORTS.items() if name == geraet)


def stationen(von, nach):
    """Liste der Stationen mit dem, was sie tun."""
    a, b = HOSTS[von], HOSTS[nach]
    weg = [von]
    if a["netz"] == b["netz"]:
        weg.append(f"Switch P{port_von(von)} → P{port_von(nach)}")
    else:
        if a["netz"] == SWITCH_NETZ:
            weg.append(f"Switch P{port_von(von)} → P{port_von('ROUTER')}")
            weg.append(f"Router {a['netz']} → {b['netz']}")
        else:
            weg.append(f"Router {a['netz']} → {b['netz']}")
            weg.append(f"Switch P{port_von('ROUTER')} → P{port_von(nach)}")
    weg.append(nach)
    return weg


def teilstrecken(von, nach):
    """Ethernet-Header je Teilstrecke: ein Eintrag im selben Netz, zwei über den Router."""
    a, b = HOSTS[von], HOSTS[nach]
    if a["netz"] == b["netz"]:
        return [{"von": von, "bis": nach, "ziel_mac": b["mac"], "quell_mac": a["mac"]}]
    return [
        {"von": von, "bis": "Router", "ziel_mac": ROUTER[a["netz"]]["mac"], "quell_mac": a["mac"]},
        {"von": "Router", "bis": nach, "ziel_mac": b["mac"], "quell_mac": ROUTER[b["netz"]]["mac"]},
    ]


def sendung(von, nach, dienst, antwort=False):
    """Eine Sendung von 'von' nach 'nach'. Bei antwort=True sind Quell- und Ziel-Port getauscht."""
    d = DIENSTE[dienst]
    strecken = teilstrecken(von, nach)
    return {
        "von": von, "nach": nach, "weg": stationen(von, nach), "teilstrecken": strecken,
        "ankunft": strecken[-1],
        "quell_ip": HOSTS[von]["ip"], "ziel_ip": HOSTS[nach]["ip"],
        "transport": d["transport"],
        "quell_port": str(d["port"]) if antwort else CLIENT_PORT,
        "ziel_port": CLIENT_PORT if antwort else str(d["port"]),
        "anwendung": dienst,
    }


def loese(auftrag):
    von, nach, dienst = auftrag["von"], auftrag["nach"], auftrag["dienst"]
    assert dienst in HOSTS[nach]["dienste"], f"Auftrag {auftrag['nr']}: {nach} bietet {dienst} nicht an"
    hin = sendung(von, nach, dienst)
    fern = len(hin["teilstrecken"]) > 1
    loesung = {**auftrag, "hin": hin, "fern": fern,
               "punkte": (2 if fern else 1) + (1 if auftrag["antwort"] else 0)}
    if auftrag["antwort"]:
        loesung["zurueck"] = sendung(nach, von, dienst, antwort=True)
    return loesung


def merksatz(l):
    if l["antwort"]:
        return "Bei der Antwort tauschen Quelle und Ziel die Plätze: bei den Ports, den IP-Adressen und den MAC-Adressen."
    if l["fern"]:
        return "Ziel im fremden Netz: Die Ziel-MAC gehört dem Router. Die Ziel-IP bleibt die des Servers."
    if l["hin"]["transport"] == "UDP":
        return "DNS und NTP nutzen UDP: kurz fragen, kurz antworten, ohne Verbindungsaufbau."
    return "Ziel im eigenen Netz: Die Ziel-MAC gehört dem Empfänger selbst."


ALLE = [loese(a) for a in AUFTRAEGE]


if __name__ == "__main__":
    for l in ALLE:
        h = l["hin"]
        strecken = " | ".join(f"{t['ziel_mac']}←{t['quell_mac']}" for t in h["teilstrecken"])
        print(f"{l['nr']:2d} S{l['stufe']} {l['punkte']}P  {' · '.join(h['weg']):48s} "
              f"{h['quell_ip']}→{h['ziel_ip']:10s} {h['transport']} {h['ziel_port']:>3s} {h['anwendung']:5s} {strecken}"
              + ("  ↩" if l["antwort"] else ""))
    for stufe in (1, 2):
        karten = [l for l in ALLE if l["stufe"] == stufe]
        print(f"Stufe {stufe}: {len(karten)} Karten, {sum(l['punkte'] for l in karten)} Punkte")
