"""Prüft die STL-Dateien in druck/stl: Sind die Netze geschlossen (jede Kante gehört zu genau zwei Dreiecken)?

Aufruf (aus dem Ordner header-ahead):  python3 cad/netze_pruefen.py
"""

import sys
from pathlib import Path

import numpy as np

STL = Path(__file__).resolve().parent.parent / "druck" / "stl"


def dreiecke(datei):
    roh = datei.read_bytes()
    anzahl = int.from_bytes(roh[80:84], "little")
    typ = np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    return np.frombuffer(roh, dtype=typ, count=anzahl, offset=84)["v"]


def pruefe(datei):
    v = dreiecke(datei)
    punkte, index = np.unique(np.round(v.reshape(-1, 3), 3), axis=0, return_inverse=True)
    f = index.reshape(-1, 3)
    kanten = np.sort(np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]]), axis=1)
    _, haeufigkeit = np.unique(kanten, axis=0, return_counts=True)
    offen = int((haeufigkeit == 1).sum())
    mehrfach = int((haeufigkeit > 2).sum())
    groesse = v.reshape(-1, 3).max(axis=0) - v.reshape(-1, 3).min(axis=0)
    z_min = float(v[:, :, 2].min())
    return len(v), offen, mehrfach, groesse, z_min


def main():
    fehler = 0
    for datei in sorted(STL.glob("*.stl")):
        n, offen, mehrfach, g, z_min = pruefe(datei)
        ok = offen == 0
        fehler += not ok
        print(f"{'ok    ' if ok else 'FEHLER'} {datei.name:34s} {n:7d} Dreiecke  offen {offen:3d}  mehrfach {mehrfach:3d}  "
              f"{g[0]:6.1f} × {g[1]:6.1f} × {g[2]:5.1f}  z ab {z_min:5.2f}")
    print("ALLE NETZE GESCHLOSSEN" if not fehler else f"{fehler} Netze mit offenen Kanten")
    sys.exit(1 if fehler else 0)


if __name__ == "__main__":
    main()
