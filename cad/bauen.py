"""Baut alle Druckteile und schreibt STEP, STL und eine Teileliste.

Aufruf (aus dem Ordner header-ahead):  .venv/bin/python cad/bauen.py

Ausgabe:
  druck/step/<teil>.step            Körper und Schrift als zwei Volumenkörper (für CAD)
  druck/stl/<teil>.stl              Körper mit vertiefter Schrift, in Drucklage
  druck/stl/<teil>_schrift.stl      Schrift als Einleger für die zweite Farbe
  druck/teileliste.json             Anzahl, Farben, Maße, Hinweise
  cad/_render/…                     Netze in Gebrauchslage für die Bilder
"""

import json
import re
import sys
import time
from pathlib import Path

from build123d import Compound, Pos, Rot, export_step, export_stl

HIER = Path(__file__).resolve().parent
WURZEL = HIER.parent
sys.path.insert(0, str(HIER))
sys.path.insert(0, str(WURZEL / "spiel"))

import daten  # noqa: E402
import teile as T  # noqa: E402
from masse import PL_H  # noqa: E402

STEP = WURZEL / "druck" / "step"
STL = WURZEL / "druck" / "stl"
RENDER = HIER / "_render"
NETZ = dict(tolerance=0.01, angular_tolerance=0.25)


def kurz(text):
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def in_drucklage(form, kopfueber, zmax):
    if not kopfueber:
        return form
    return Pos(0, 0, zmax) * Rot(180, 0, 0) * form


def schreibe(teil, liste):
    kasten = teil.koerper.bounding_box()
    zmax = kasten.max.Z
    export_stl(teil.koerper, str(RENDER / f"{teil.name}.stl"), **NETZ)
    export_stl(in_drucklage(teil.koerper, teil.kopfueber, zmax), str(STL / f"{teil.name}.stl"), **NETZ)
    teil.koerper.label = teil.name
    koerper = [teil.koerper]
    if teil.schrift is not None:
        export_stl(teil.schrift, str(RENDER / f"{teil.name}_schrift.stl"), **NETZ)
        export_stl(in_drucklage(teil.schrift, teil.kopfueber, zmax), str(STL / f"{teil.name}_schrift.stl"), **NETZ)
        teil.schrift.label = f"{teil.name}_schrift"
        koerper.append(teil.schrift)
    export_step(Compound(children=koerper, label=teil.name), str(STEP / f"{teil.name}.step"))
    g = kasten.size
    liste.append({
        "name": teil.name, "anzahl": teil.anzahl, "farbe": teil.farbe,
        "schriftfarbe": teil.schriftfarbe, "hinweis": teil.hinweis,
        "kopfueber": teil.kopfueber,
        "masse_mm": [round(g.X, 1), round(g.Y, 1), round(g.Z, 1)],
        "volumen_cm3": round(teil.koerper.volume / 1000 + (teil.schrift.volume / 1000 if teil.schrift else 0), 1),
        **teil.extra,
    })
    print(f"  {teil.name:22s} {g.X:6.1f} × {g.Y:6.1f} × {g.Z:5.1f} mm   {teil.anzahl}×")


def main():
    for ordner in (STEP, STL, RENDER):
        ordner.mkdir(parents=True, exist_ok=True)
    start = time.time()
    liste = []
    sorten = daten.plaettchen()
    alle = [
        T.frame_schale(), T.ip_header(), T.tcp_header(), T.udp_header(), T.daten_block(),
        T.fcs_plaettchen(), T.stoerungs_chip(), T.kabel(),
        T.platte_host(), T.platte_switch(), T.platte_router(),
        T.switch_tunnel(), T.router_dach(), T.vorratskasten(),
        T.plaettchen_bogen("plaettchen_mac", sorten["mac"]),
        T.plaettchen_bogen("plaettchen_ip", sorten["ip"]),
        T.plaettchen_bogen("plaettchen_port", sorten["port"]),
        T.plaettchen_bogen("plaettchen_protokoll", sorten["protokoll"]),
    ]
    for teil in alle:
        schreibe(teil, liste)

    # Einzelne Plättchen nur für die Bilder
    einzeln = {}
    for sorte, eintraege in sorten.items():
        for text, _ in eintraege:
            p = T.plaettchen(text)
            name = f"pl_{kurz(text)}"
            export_stl(p.koerper, str(RENDER / f"{name}.stl"), **NETZ)
            export_stl(p.schrift, str(RENDER / f"{name}_schrift.stl"), **NETZ)
            einzeln[text] = {"datei": name, "sorte": sorte}
    # FCS-Plättchen für die Bilder in zwei Hälften (grün oben, rot unten)
    fcs = T.fcs_plaettchen()
    haelfte = T.quader(-1, -1, PL_H / 2, 20, 20, PL_H + 1)
    export_stl(fcs.koerper & haelfte, str(RENDER / "fcs_oben.stl"), **NETZ)
    export_stl(fcs.koerper - haelfte, str(RENDER / "fcs_unten.stl"), **NETZ)

    (WURZEL / "druck" / "teileliste.json").write_text(
        json.dumps({"teile": liste, "plaettchen": einzeln}, ensure_ascii=False, indent=1))
    print(f"fertig in {time.time() - start:.0f} s")


if __name__ == "__main__":
    main()
