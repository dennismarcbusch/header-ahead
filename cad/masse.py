"""Maße für Header Ahead (alle Angaben in Millimetern).

Diese Datei ist die einzige Stelle, an der Maße stehen. Teile (teile.py),
Prüfung (pruefen.py) und Bilder (rendern.py) lesen von hier.

Koordinaten in jedem Teil: X läuft vom Header zum Trailer (links nach rechts),
Y von der Spielerin weg (vorn nach hinten), Z nach oben.
"""

# --- Passungen -------------------------------------------------------------
SPIEL = 0.2          # Luft je Seite bei Steckverbindungen (Zapfen in Tasche)
SCHRIFT_T = 0.6      # Tiefe der Schrift (drei Schichten bei 0,2 mm)

# --- Adress-Plättchen ------------------------------------------------------
PL_L, PL_B, PL_H = 44.0, 15.0, 5.0        # Länge, Breite, Höhe
FACH_L, FACH_B, FACH_T = 44.5, 15.5, 2.6  # Fach im Baustein
LIPPE_B, LIPPE_H = 1.0, 0.6               # Haltelippe an der offenen Fachseite

# --- Bausteine der Dateneinheit --------------------------------------------
KOPF_L = 50.0        # Länge eines Headers (IP, TCP, UDP)
DATEN_L = 56.0       # Länge des Daten-Blocks
BLOCK_B = 56.0       # Breite aller Bausteine
BLOCK_H = 16.0       # Höhe aller Bausteine
ZAPFEN_H = 12.0      # Höhe der Steckzapfen (Taschen sind unten offen)

# Streifen quer über einen Baustein (Y-Bereiche), von vorn nach hinten
FACH_VORN_Y = (LIPPE_B, LIPPE_B + FACH_B)                 # 1,0 … 16,5
TEXT_VORN_Y = (16.5, 22.0)
TITEL_Y = (22.0, 34.0)
TEXT_HINTEN_Y = (34.0, 39.5)
FACH_HINTEN_Y = (39.5, 55.0)

# --- Frame-Schale -----------------------------------------------------------
BODEN = 3.2          # Bodenstärke der Schale = Tiefe der Bucht in der Platte
ETH_L = 50.0         # Ethernet-Header (Vorderwand)
FCS_L = 20.0         # FCS (Rückwand)
SCHIENE_B, SCHIENE_H = 4.0, 8.0   # hintere Führung
RAND_B, RAND_H = 1.2, 0.6         # niedriger Rand an der offenen Vorderseite (niedriger als BLOCK_FASE)
BLOCK_FASE = 0.8                  # Fase an der Unterkante der Bausteine: gleitet über den Rand
MULDE_L = 2 * KOPF_L + DATEN_L + 0.8          # 156,8: Platz für das Paket
SCHALE_L = ETH_L + MULDE_L + FCS_L            # 226,8
SCHALE_B = RAND_B + BLOCK_B + 0.6 + SCHIENE_B  # 61,8
SCHALE_H = BODEN + BLOCK_H                    # 19,2

# --- Stationsplatten --------------------------------------------------------
PLATTE_L, PLATTE_B, PLATTE_H = 240.0, 200.0, 6.0
BUCHT_B = SCHALE_B + 0.6                      # 62,4
BUCHT_T = BODEN                               # Schalenboden bündig zur Platte
SCHALE_X0 = 0.7                               # Schale liegt links an
KARTE_L, KARTE_B = 80.0, 52.0                 # Papierkarten in den Platten
KARTENFACH_T = 1.0

# Host- und Router-Platte: Bucht hinten, Montageplatz davor
BUCHT_Y0 = 134.0
MONTAGE_Y0 = 75.0
LEISTE_Y0 = 63.0      # Leiste mit den Schichtnummern, 2 mm erhaben
RAND_PLATTE_H = 2.0

# Switch-Platte: Bucht in der Mitte, Tunnel darüber
SW_BUCHT_Y0 = (PLATTE_B - BUCHT_B) / 2        # 68,8

# Blenden (Switch-Tunnel, Router-Dach)
BLENDE_LICHT = 20.0   # lichte Höhe über der Plattenoberseite
BLENDE_WAND = 3.5
BLENDE_DECKE = 3.0
FEDER_L, FEDER_T = 10.0, 4.0   # Steckfedern der Blenden in der Platte

# --- Kabel ------------------------------------------------------------------
KABEL_L = 60.0
KABEL_RAND = 3.0
NASE_HALS_B, NASE_HALS_L, NASE_R = 10.0, 5.0, 8.0   # Puzzle-Nase
NASE_SPIEL = 0.25

# --- Vorratskasten ----------------------------------------------------------
KASTEN_SPALTEN = 4
KASTEN_ZEILEN = 9
KASTEN_FACH_T = 6.0
KASTEN_GASSE = 8.0    # Griffgasse neben jeder Spalte

# --- Sonstiges --------------------------------------------------------------
FCS_PL = 15.0         # FCS-Plättchen (quadratisch, zweifarbig)
CHIP_D, CHIP_H = 28.0, 3.2
