"""Prüft Größen und Passungen der Druckteile rechnerisch.

Aufruf (aus dem Ordner header-ahead):  .venv/bin/python cad/pruefen.py

Geprüft wird: Kein Teil ist größer als 240 × 200 mm, zusammengesteckte Teile
durchdringen sich nicht, und die Luft an den Passungen liegt im geplanten Bereich.
"""

import sys
from pathlib import Path

from build123d import Pos

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER))
sys.path.insert(0, str(HIER.parent / "spiel"))

import daten  # noqa: E402
import teile as T  # noqa: E402
from masse import *  # noqa: E402,F401,F403

FEHLER = []


def melde(ok, text):
    print(("  ok      " if ok else "  FEHLER  ") + text)
    if not ok:
        FEHLER.append(text)


def schnitt(a, b):
    """Gemeinsames Volumen zweier Körper in mm³."""
    try:
        gemeinsam = a & b
        return gemeinsam.volume if gemeinsam is not None else 0.0
    except Exception:
        return 0.0


def frei(a, b, was, grenze=0.5):
    v = schnitt(a, b)
    melde(v < grenze, f"{was}: Durchdringung {v:.2f} mm³")


def main():
    schale, ip, tcp, udp, dat = T.frame_schale(), T.ip_header(), T.tcp_header(), T.udp_header(), T.daten_block()
    host, switch, router = T.platte_host(), T.platte_switch(), T.platte_router()
    tunnel, dach, kabel, kasten = T.switch_tunnel(), T.router_dach(), T.kabel(), T.vorratskasten()
    pl = T.plaettchen("10.0.1.11")
    fcs = T.fcs_plaettchen()
    sorten = daten.plaettchen()
    boegen = [T.plaettchen_bogen(f"plaettchen_{s}", e) for s, e in sorten.items()]

    print("Größe (Grenze 240 × 200 mm, jede Lage auf dem Bett):")
    for t in [schale, ip, tcp, udp, dat, host, switch, router, tunnel, dach, kabel, kasten, *boegen]:
        g = t.koerper.bounding_box().size
        lang, kurz = max(g.X, g.Y), min(g.X, g.Y)
        melde(lang <= 240.01 and kurz <= 200.01, f"{t.name}: {g.X:.1f} × {g.Y:.1f} × {g.Z:.1f}")

    print("Höhe der Bausteine (Zapfen dürfen nicht nach unten ragen):")
    for t in [ip, tcp, udp, dat]:
        k = t.koerper.bounding_box()
        melde(abs(k.min.Z) < 0.01 and abs(k.max.Z - BLOCK_H) < 0.01, f"{t.name}: z von {k.min.Z:.1f} bis {k.max.Z:.1f}")

    # Paket zusammenstecken: IP | TCP | Daten, hintereinander entlang X
    print("Paket (IP-Header, TCP-Header, Daten):")
    ip_k = ip.koerper
    tcp_k = Pos(KOPF_L, 0, 0) * tcp.koerper
    udp_k = Pos(KOPF_L, 0, 0) * udp.koerper
    dat_k = Pos(2 * KOPF_L, 0, 0) * dat.koerper
    frei(ip_k, tcp_k, "IP-Header und TCP-Header")
    frei(ip_k, udp_k, "IP-Header und UDP-Header")
    frei(tcp_k, dat_k, "TCP-Header und Daten")
    # Falsche Reihenfolge muss klemmen: IP-Header direkt vor die Daten
    v = schnitt(ip_k, Pos(KOPF_L, 0, 0) * dat.koerper)
    melde(v > 20, f"IP-Header direkt an Daten passt nicht (Überdeckung {v:.0f} mm³)")
    v = schnitt(tcp_k, Pos(2 * KOPF_L, 0, 0) * tcp.koerper)
    melde(v > 20, f"Zwei Transport-Header hintereinander passen nicht (Überdeckung {v:.0f} mm³)")
    laenge = 2 * KOPF_L + DATEN_L
    melde(0.3 <= MULDE_L - laenge <= 1.2, f"Luft des Pakets in der Mulde längs: {MULDE_L - laenge:.1f} mm")
    melde(BLOCK_FASE > RAND_H, f"Fase der Bausteine ({BLOCK_FASE} mm) ist höher als der Schalenrand ({RAND_H} mm)")

    print("Paket in der Schale:")
    y0 = RAND_B + 0.3
    for name, k in [("IP-Header", ip_k), ("TCP-Header", tcp_k), ("Daten", dat_k)]:
        frei(Pos(ETH_L + 0.4, y0, BODEN) * k, schale.koerper, f"{name} in der Schale")
    frei(Pos((ETH_L - FACH_L) / 2 + 0.25, LIPPE_B + 0.25, SCHALE_H - FACH_T) * pl.koerper, schale.koerper,
         "Plättchen im vorderen Fach des Ethernet-Headers")
    frei(Pos((ETH_L - FACH_L) / 2 + 0.25, SCHALE_B - LIPPE_B - FACH_B + 0.25, SCHALE_H - FACH_T) * pl.koerper,
         schale.koerper, "Plättchen im hinteren Fach des Ethernet-Headers")
    frei(Pos((KOPF_L - FACH_L) / 2 + 0.25, LIPPE_B + 0.25, BLOCK_H - FACH_T) * pl.koerper, ip_k,
         "Plättchen im vorderen Fach des IP-Headers")
    frei(Pos(SCHALE_L - LIPPE_B - FCS_PL - 0.25, 4.25, SCHALE_H - FACH_T) * fcs.koerper, schale.koerper,
         "FCS-Plättchen in der Schale")

    print("Schale in den Platten:")
    schale_host = Pos(SCHALE_X0, BUCHT_Y0 + 0.3, PLATTE_H - BUCHT_T) * schale.koerper
    frei(schale_host, host.koerper, "Schale in der Bucht der Host-Platte")
    frei(schale_host, router.koerper, "Schale in der Bucht der Router-Platte")
    schale_sw = Pos(SCHALE_X0, SW_BUCHT_Y0 + 0.3, PLATTE_H - BUCHT_T) * schale.koerper
    frei(schale_sw, switch.koerper, "Schale in der Bucht der Switch-Platte")
    melde(abs((PLATTE_H - BUCHT_T + BODEN) - PLATTE_H) < 0.01, "Schalenboden liegt bündig mit der Plattenoberseite")

    print("Paket auf dem Montageplatz:")
    for name, platte in [("Host", host), ("Router", router)]:
        for teil, k in [("IP-Header", ip_k), ("TCP-Header", tcp_k), ("Daten", dat_k)]:
            frei(Pos(T.ZONE_IP[0], MONTAGE_Y0 + 0.5, PLATTE_H) * k, platte.koerper, f"{teil} auf der {name}-Platte")

    print("Blenden:")
    frei(tunnel.koerper, switch.koerper, "Tunnel in der Switch-Platte")
    frei(dach.koerper, router.koerper, "Dach in der Router-Platte")
    voll = schale_sw
    for k in (ip_k, tcp_k, dat_k):
        voll = voll + Pos(SCHALE_X0 + ETH_L + 0.4, SW_BUCHT_Y0 + 0.3 + y0, PLATTE_H - BUCHT_T + BODEN) * k
    frei(voll, tunnel.koerper, "Volle Schale unter dem Tunnel")
    hoehe_schale = PLATTE_H - BUCHT_T + SCHALE_H + (PL_H - FACH_T)
    melde(PLATTE_H + BLENDE_LICHT - hoehe_schale >= 1.0,
          f"Luft zwischen Plättchen und Tunneldecke: {PLATTE_H + BLENDE_LICHT - hoehe_schale:.1f} mm")
    paket_router = None
    for k in (tcp_k, dat_k):
        teil = Pos(T.ZONE_IP[0], MONTAGE_Y0 + 0.5, PLATTE_H) * k
        paket_router = teil if paket_router is None else paket_router + teil
    frei(paket_router, dach.koerper, "TCP-Header und Daten unter dem Router-Dach")
    frei(Pos(T.ZONE_IP[0], MONTAGE_Y0 + 0.5, PLATTE_H) * ip_k, dach.koerper, "IP-Header liegt frei neben dem Dach")

    print("Kabel:")
    breite = BUCHT_B + 2 * KABEL_RAND
    y_bucht = BUCHT_Y0 + BUCHT_B / 2
    kabel_links = Pos(-KABEL_L, y_bucht - breite / 2, 0) * kabel.koerper
    frei(kabel_links, host.koerper, "Kabel am Anschluss der Host-Platte")
    kabel_rechts = Pos(PLATTE_L, y_bucht - breite / 2, 0) * kabel.koerper
    frei(kabel_rechts, router.koerper, "Kabel am rechten Anschluss der Router-Platte")
    v_ohne = schnitt(Pos(-KABEL_L + 3, y_bucht - breite / 2, 0) * kabel.koerper, host.koerper)
    melde(v_ohne > 5, "Gegenprobe: 3 mm verschobenes Kabel stößt an (Anschluss sitzt, wo erwartet)")

    print("Vorratskasten:")
    x, y = T.kasten_fach_position(0, 0)
    stapel = Pos(x + 0.6, y + 0.6, T.KASTEN_H - KASTEN_FACH_T) * pl.koerper
    frei(stapel, kasten.koerper, "Plättchen im Fach des Vorratskastens")
    anzahl = sum(len(e) for e in sorten.values())
    melde(max(len(e) for e in sorten.values()) <= KASTEN_ZEILEN, f"{anzahl} Sorten Plättchen finden Platz (höchstens {KASTEN_ZEILEN} je Spalte)")

    print()
    print("ALLE PRÜFUNGEN BESTANDEN" if not FEHLER else f"{len(FEHLER)} FEHLER")
    sys.exit(1 if FEHLER else 0)


if __name__ == "__main__":
    main()
