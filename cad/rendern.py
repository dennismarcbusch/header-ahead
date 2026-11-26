"""Rendert die Bilder für Header Ahead mit Blender (Cycles, ohne Fenster).

Aufruf (aus dem Ordner header-ahead):
    blender -b -P cad/rendern.py -- [--entwurf] [szene ...]

Ohne Szenennamen werden alle Bilder gerendert. Die Netze kommen aus
cad/_render (von bauen.py), die Kartenbilder aus spiel/_karten (von karten.py).
"""

import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

HIER = Path(__file__).resolve().parent
WURZEL = HIER.parent
sys.path.insert(0, str(HIER))
sys.path.insert(0, str(WURZEL / "spiel"))
from masse import *  # noqa: E402,F401,F403
import daten as spieldaten  # noqa: E402

NETZE = HIER / "_render"
KARTEN = WURZEL / "spiel" / "_karten"
BILDER = WURZEL / "bilder"
MM = 0.001

# Abgeleitete Maße (wie in teile.py)
ZONE_IP_X = SCHALE_X0 + ETH_L
PAKET_IN_SCHALE = (ETH_L + 0.4, RAND_B + 0.3, BODEN)
FACH_X = (KOPF_L - FACH_L) / 2 + 0.25
BUCHT_Z = PLATTE_H - BUCHT_T
KABEL_B = BUCHT_B + 2 * KABEL_RAND
KASTEN_FACH_L, KASTEN_FACH_B = PL_L + 1.2, PL_B + 1.2
KASTEN_SPALTE = 2 + KASTEN_FACH_L + KASTEN_GASSE
KASTEN_ZEILE = KASTEN_FACH_B + 2
KASTEN_B = KASTEN_ZEILEN * KASTEN_ZEILE + 2 + 13.0
KASTEN_H = 2 + KASTEN_FACH_T + 2

FARBEN = {
    "hellgrau": "#CFD5DB", "weiss": "#F7F6F1", "silber": "#AEB6C0", "blau": "#2660C7",
    "hellblau": "#6CC0EC", "gruen": "#2B9A5C", "orange": "#FFB020", "anthrazit": "#2C3139",
    "schwarz": "#12161B", "rot": "#D6382E", "papier": "#FFFFFF", "tisch": "#8793A0",
}
TEILFARBE = {  # Körper, Schrift
    "frame_schale": ("orange", "schwarz"), "ip_header": ("gruen", "weiss"),
    "tcp_header": ("blau", "weiss"), "udp_header": ("hellblau", "schwarz"),
    "daten_block": ("silber", "schwarz"), "kabel": ("anthrazit", "weiss"),
    "platte_host": ("hellgrau", "schwarz"), "platte_switch": ("hellgrau", "schwarz"),
    "platte_router": ("hellgrau", "schwarz"), "switch_tunnel": ("orange", "schwarz"),
    "router_dach": ("gruen", "weiss"), "vorratskasten": ("hellgrau", "schwarz"),
    "stoerungs_chip": ("rot", "weiss"), "fcs_plaettchen": ("gruen", "weiss"),
}


# --- Grundgerüst ---------------------------------------------------------------

def linear(hexfarbe):
    def kanal(c):
        c = c / 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    h = hexfarbe.lstrip("#")
    return tuple(kanal(int(h[i:i + 2], 16)) for i in (0, 2, 4)) + (1.0,)


_material = {}


def material(name):
    if name not in _material:
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        bsdf = m.node_tree.nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = linear(FARBEN[name])
        bsdf.inputs["Roughness"].default_value = 0.9 if name in ("papier", "tisch") else 0.42
        _material[name] = m
    return _material[name]


def bildmaterial(datei):
    schluessel = f"bild:{datei}"
    if schluessel not in _material:
        m = bpy.data.materials.new(schluessel)
        m.use_nodes = True
        knoten = m.node_tree.nodes
        bild = knoten.new("ShaderNodeTexImage")
        bild.image = bpy.data.images.load(str(datei))
        m.node_tree.links.new(bild.outputs["Color"], knoten["Principled BSDF"].inputs["Base Color"])
        knoten["Principled BSDF"].inputs["Roughness"].default_value = 0.9
        _material[schluessel] = m
    return _material[schluessel]


_netz = {}


def netz(name):
    """Lädt ein STL einmal und gibt die Mesh-Daten zurück (None, wenn es fehlt)."""
    if name not in _netz:
        datei = NETZE / f"{name}.stl"
        if not datei.exists():
            _netz[name] = None
        else:
            bpy.ops.wm.stl_import(filepath=str(datei), global_scale=1.0)
            objekt = bpy.context.selected_objects[0]
            daten = objekt.data
            daten.transform(Matrix.Scale(MM, 4))      # Millimeter in Meter, fest im Netz
            daten.set_sharp_from_angle(angle=math.radians(35))
            for flaeche in daten.polygons:
                flaeche.use_smooth = True
            bpy.data.objects.remove(objekt)
            _netz[name] = daten
    return _netz[name]


def anker(x=0, y=0, z=0, drehung=0, eltern=None):
    leer = bpy.data.objects.new("anker", None)
    leer.location = (x * MM, y * MM, z * MM)
    leer.rotation_euler = (0, 0, math.radians(drehung))
    bpy.context.collection.objects.link(leer)
    if eltern is not None:
        leer.parent = eltern
    return leer


def objekt(netzname, farbe, eltern, x=0, y=0, z=0):
    daten = netz(netzname)
    if daten is None:
        return None
    o = bpy.data.objects.new(netzname, daten.copy())
    o.data.materials.append(material(farbe))
    o.location = (x * MM, y * MM, z * MM)
    o.parent = eltern
    bpy.context.collection.objects.link(o)
    return o


def teil(name, eltern, x=0, y=0, z=0, farben=None):
    koerper, schrift = farben or TEILFARBE[name]
    objekt(name, koerper, eltern, x, y, z)
    objekt(f"{name}_schrift", schrift, eltern, x, y, z)


def plaettchen(text, eltern, x, y, z):
    name = "pl_" + "".join(c if c.isalnum() else "_" for c in text.lower()).strip("_")
    while "__" in name:
        name = name.replace("__", "_")
    objekt(name, "weiss", eltern, x, y, z)
    objekt(f"{name}_schrift", "schwarz", eltern, x, y, z)


def fcs(eltern, x, y, z, ok=True):
    if ok:
        objekt("fcs_oben", "gruen", eltern, x, y, z)
        objekt("fcs_unten", "rot", eltern, x, y, z)
        objekt("fcs_plaettchen_schrift", "weiss", eltern, x, y, z)
    else:  # umgedreht: rote Seite oben
        dreh = anker(x + FCS_PL, y, z + PL_H, eltern=eltern)
        dreh.rotation_euler = (0, math.radians(180), 0)
        objekt("fcs_oben", "gruen", dreh)
        objekt("fcs_unten", "rot", dreh)
        objekt("fcs_plaettchen_schrift", "weiss", dreh)


def karte(datei, eltern, x, y, z, laenge=KARTE_L, breite=KARTE_B, drehung=0):
    """Papierkarte als dünne Fläche; mit Bild, wenn die PNG-Datei vorhanden ist."""
    bpy.ops.mesh.primitive_plane_add(size=1)
    o = bpy.context.object
    o.scale = (laenge * MM, breite * MM, 1)
    o.location = ((x + laenge / 2) * MM, (y + breite / 2) * MM, (z + 0.25) * MM)
    o.rotation_euler = (0, 0, math.radians(drehung))
    pfad = KARTEN / f"{datei}.png" if datei else None
    o.data.materials.append(bildmaterial(pfad) if pfad and pfad.exists() else material("papier"))
    o.parent = eltern
    return o


# --- Zusammengesetzte Dinge ------------------------------------------------------

def baustein(name, eltern, x, y, z, hinten=None, vorn=None, laenge=KOPF_L):
    """Header oder Daten-Block mit Plättchen. hinten/vorn: Text des Plättchens oder None."""
    a = anker(x, y, z, eltern=eltern)
    teil(name, a)
    fx = (laenge - FACH_L) / 2 + 0.25
    if vorn:
        plaettchen(vorn, a, fx, LIPPE_B + 0.25, BLOCK_H - FACH_T)
    if hinten:
        plaettchen(hinten, a, fx, BLOCK_B - LIPPE_B - FACH_B + 0.25, BLOCK_H - FACH_T)
    return a


def paket(eltern, x, y, z, inhalt, stufen=3):
    """Paket aus Daten (stufen>=1), Transport-Header (>=2) und IP-Header (>=3).

    inhalt: dict mit anwendung, transport ('tcp'/'udp'), qport, zport, qip, zip.
    Der Ursprung ist die linke vordere Ecke des IP-Headers.
    """
    a = anker(x, y, z, eltern=eltern)
    baustein("daten_block", a, 2 * KOPF_L, 0, 0, vorn=inhalt.get("anwendung"), laenge=DATEN_L)
    if stufen >= 2:
        baustein(f"{inhalt.get('transport', 'tcp')}_header", a, KOPF_L, 0, 0,
                 hinten=inhalt.get("qport"), vorn=inhalt.get("zport"))
    if stufen >= 3:
        baustein("ip_header", a, 0, 0, 0, hinten=inhalt.get("qip"), vorn=inhalt.get("zip"))
    return a


def schale(eltern, x, y, z, drehung=0, zmac=None, qmac=None, fcs_ok=True, inhalt=None):
    a = anker(x, y, z, drehung, eltern)
    teil("frame_schale", a)
    fx = (ETH_L - FACH_L) / 2 + 0.25
    if qmac:
        plaettchen(qmac, a, fx, LIPPE_B + 0.25, SCHALE_H - FACH_T)
    if zmac:
        plaettchen(zmac, a, fx, SCHALE_B - LIPPE_B - FACH_B + 0.25, SCHALE_H - FACH_T)
    if fcs_ok is not None:
        fcs(a, SCHALE_L - LIPPE_B - FCS_PL - 0.25, 4.25, SCHALE_H - FACH_T, fcs_ok)
    if inhalt:
        paket(a, *PAKET_IN_SCHALE, inhalt)
    return a


def platte(art, x=0, y=0, drehung=0, karten=()):
    """art: host, switch oder router. karten: Dateinamen für die Kartenfächer."""
    a = anker(x, y, 0, drehung)
    teil(f"platte_{art}", a)
    faecher = [(5.8, 6.8)] if art == "switch" else [(6.8, 5.8), (94.8, 5.8)]
    for (kx, ky), datei in zip(faecher, karten):
        karte(datei, a, kx, ky, PLATTE_H - KARTENFACH_T)
    if art == "switch":
        teil("switch_tunnel", a)
    if art == "router":
        teil("router_dach", a)
    return a


def kabel(x, y, drehung=0):
    a = anker(x, y, 0, drehung)
    teil("kabel", a)
    return a


def in_bucht(platte_anker, art="host"):
    """Position einer Schale in der Bucht einer Platte (lokale Koordinaten der Platte)."""
    y = (SW_BUCHT_Y0 if art == "switch" else BUCHT_Y0) + 0.3
    return dict(eltern=platte_anker, x=SCHALE_X0, y=y, z=BUCHT_Z)


def auf_montageplatz(platte_anker):
    return dict(eltern=platte_anker, x=ZONE_IP_X, y=MONTAGE_Y0 + 0.5, z=PLATTE_H)


# --- Beispielinhalte ---------------------------------------------------------------

HTTP_LOKAL = dict(anwendung="HTTP", transport="tcp", qport="49152", zport="80",
                  qip="10.0.1.11", zip="10.0.1.20")
HTTPS_FERN = dict(anwendung="HTTPS", transport="tcp", qport="50001", zport="443",
                  qip="10.0.1.11", zip="10.0.2.10")
DNS_LOKAL = dict(anwendung="DNS", transport="udp", qport="51515", zport="53",
                 qip="10.0.1.12", zip="10.0.1.20")
# Texte der MAC-Plättchen (zweizeilig), wie sie bauen.py als Netze ablegt
MAC = {name: spieldaten.mac_plaettchen(h["mac"]) for name, h in spieldaten.HOSTS.items()}
MAC["R-A"] = spieldaten.mac_plaettchen(spieldaten.ROUTER["A"]["mac"])
MAC["R-B"] = spieldaten.mac_plaettchen(spieldaten.ROUTER["B"]["mac"])


# --- Kamera, Licht, Ausgabe -----------------------------------------------------------

def leere_szene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _material.clear()
    _netz.clear()
    szene = bpy.context.scene
    szene.render.engine = "CYCLES"
    szene.cycles.device = "CPU"
    szene.cycles.use_denoising = True
    szene.view_settings.view_transform = "Standard"
    szene.render.film_transparent = False
    welt = bpy.data.worlds.new("welt")
    welt.use_nodes = True
    hintergrund = welt.node_tree.nodes["Background"]
    hintergrund.inputs["Color"].default_value = (1, 1, 1, 1)
    hintergrund.inputs["Strength"].default_value = 0.32
    szene.world = welt
    return szene


def tisch(mitte=(0, 0), groesse=6000):
    bpy.ops.mesh.primitive_plane_add(size=groesse * MM, location=(mitte[0] * MM, mitte[1] * MM, 0))
    bpy.context.object.data.materials.append(material("tisch"))


def licht(ziel, abstand=900):
    zx, zy, zz = ziel
    for name, (dx, dy, dz), staerke, groesse in [
        ("haupt", (-0.55, -0.45, 1.0), 1.0, 0.9),
        ("auf", (0.9, -0.7, 0.6), 0.28, 1.4),
        ("kante", (0.2, 1.0, 0.7), 0.35, 1.0),
    ]:
        daten = bpy.data.lights.new(name, "AREA")
        daten.energy = staerke * 13 * (abstand / 900) ** 2
        daten.size = groesse * abstand * MM
        lampe = bpy.data.objects.new(name, daten)
        ort = Vector(((zx + dx * abstand) * MM, (zy + dy * abstand) * MM, (zz + dz * abstand) * MM))
        lampe.location = ort
        richtung = Vector((zx * MM, zy * MM, zz * MM)) - ort
        lampe.rotation_euler = richtung.to_track_quat("-Z", "Y").to_euler()
        bpy.context.collection.objects.link(lampe)


def kamera(ort, ziel, brennweite=70, ortho=None):
    daten = bpy.data.cameras.new("kamera")
    if ortho:
        daten.type = "ORTHO"
        daten.ortho_scale = ortho * MM
    else:
        daten.lens = brennweite
    daten.clip_start, daten.clip_end = 0.01, 50
    k = bpy.data.objects.new("kamera", daten)
    k.location = Vector(ort) * MM
    richtung = Vector(ziel) * MM - k.location
    k.rotation_euler = richtung.to_track_quat("-Z", "Y").to_euler()
    bpy.context.collection.objects.link(k)
    bpy.context.scene.camera = k


def ausgabe(name, breite, hoehe, entwurf):
    szene = bpy.context.scene
    faktor = 0.5 if entwurf else 1.0
    szene.render.resolution_x = int(breite * faktor)
    szene.render.resolution_y = int(hoehe * faktor)
    szene.cycles.samples = 24 if entwurf else 96
    szene.render.image_settings.file_format = "PNG"
    BILDER.mkdir(exist_ok=True)
    szene.render.filepath = str(BILDER / f"{name}.png")
    bpy.ops.render.render(write_still=True)
    print(f"BILD {name}.png")


# --- Szenen ------------------------------------------------------------------------------

def szene_dateneinheit():
    """Ein fertiger Frame: Schale mit Paket, alle Felder gefüllt."""
    tisch()
    schale(None, 0, 0, 0, zmac=MAC["INTRA"], qmac=MAC["PC 1"], inhalt=HTTP_LOKAL)
    ziel = (SCHALE_L / 2, SCHALE_B / 2, 8)
    licht(ziel, 600)
    kamera((SCHALE_L / 2 - 60, -430, 520), ziel, 85)
    return 1800, 900


def szene_dateneinheit_teile():
    """Dieselbe Dateneinheit auseinandergezogen, Plättchen über ihren Fächern."""
    tisch()
    luft = 26
    schale(None, 0, 86, 0, fcs_ok=None)
    x = ETH_L + 6
    for name, laenge, hinten, vorn in [("ip_header", KOPF_L, "10.0.1.11", "10.0.1.20"),
                                       ("tcp_header", KOPF_L, "49152", "80"),
                                       ("daten_block", DATEN_L, None, "HTTP")]:
        a = anker(x, -22, 0)
        teil(name, a)
        fx = (laenge - FACH_L) / 2 + 0.25
        if vorn:
            plaettchen(vorn, a, fx, -PL_B - 6, 0)
        if hinten:
            plaettchen(hinten, a, fx, BLOCK_B + 6, 0)
        x += laenge + luft
    plaettchen(MAC["PC 1"], None, (ETH_L - FACH_L) / 2, 86 - PL_B - 6, 0)
    plaettchen(MAC["INTRA"], None, (ETH_L - FACH_L) / 2, 86 + SCHALE_B + 6, 0)
    fcs(None, SCHALE_L + 10, 90, 0)
    ziel = (SCHALE_L / 2 + 22, 52, 5)
    licht(ziel, 700)
    kamera((SCHALE_L / 2 + 5, -470, 690), ziel, 70)
    return 1800, 1150


def _host_mit_karten(x=0, y=0, drehung=0, name="pc1"):
    return platte("host", x, y, drehung, karten=(f"geraet_{name}", "schichten"))


def _schritt(nummer):
    """Kapselung auf der Host-Platte in fünf Schritten."""
    tisch((120, 100))
    p = _host_mit_karten()
    if nummer <= 3:
        paket(stufen=nummer, inhalt=HTTP_LOKAL, **auf_montageplatz(p))
        schale(fcs_ok=None, **in_bucht(p))
    elif nummer == 4:
        schale(zmac=MAC["INTRA"], qmac=MAC["PC 1"], inhalt=HTTP_LOKAL, **in_bucht(p))
    else:
        s = in_bucht(p)
        s["x"] -= 150
        schale(zmac=MAC["INTRA"], qmac=MAC["PC 1"], inhalt=HTTP_LOKAL, **s)
    kabel(-KABEL_L, BUCHT_Y0 + BUCHT_B / 2 - KABEL_B / 2)
    ziel = (95 if nummer == 5 else 118, 112, 6)
    licht(ziel, 700)
    kamera((ziel[0] - 30, -330, 470), ziel, 70)
    return 1500, 1050


def szene_titel():
    tisch((120, 100))
    p = _host_mit_karten()
    schale(zmac=MAC["INTRA"], qmac=MAC["PC 1"], inhalt=HTTP_LOKAL, **in_bucht(p))
    kabel(-KABEL_L, BUCHT_Y0 + BUCHT_B / 2 - KABEL_B / 2)
    paket(inhalt=DNS_LOKAL, stufen=2, **auf_montageplatz(p))
    baustein("ip_header", None, 262, 96, 0)
    plaettchen("10.0.1.12", None, 268, 60, 0)
    plaettchen("10.0.1.20", None, 262, 36, 0)
    ziel = (135, 96, 8)
    licht(ziel, 750)
    kamera((-70, -400, 400), ziel, 50)
    return 1800, 1100


def szene_switch():
    tisch((120, 100))
    p = platte("switch", karten=("mac_tabelle",))
    schale(zmac=MAC["INTRA"], qmac=MAC["PC 1"], inhalt=HTTP_LOKAL, **in_bucht(p, "switch"))
    mitte = PLATTE_B / 2 - KABEL_B / 2
    kabel(-KABEL_L, mitte)
    kabel(PLATTE_L, mitte)
    kabel(PLATTE_L / 2 + KABEL_B / 2, PLATTE_B, 90)
    kabel(PLATTE_L / 2 - KABEL_B / 2, 0, -90)
    ziel = (120, 96, 8)
    licht(ziel, 750)
    kamera((70, -380, 470), ziel, 55)
    return 1500, 1150


def szene_router():
    tisch((120, 100))
    p = platte("router", karten=("router_schnittstellen", "routing_tabelle"))
    paket(inhalt=HTTPS_FERN, **auf_montageplatz(p))
    schale(zmac=MAC["WEB"], qmac=MAC["R-B"], fcs_ok=True, **in_bucht(p))
    schale(None, -20, -95, 0, drehung=-12, fcs_ok=None)       # alte, geleerte Schale
    plaettchen(MAC["R-A"], None, 228, -72, 0)
    plaettchen(MAC["PC 1"], None, 238, -96, 0)
    y = BUCHT_Y0 + BUCHT_B / 2 - KABEL_B / 2
    kabel(-KABEL_L, y)
    kabel(PLATTE_L, y)
    ziel = (120, 48, 8)
    licht(ziel, 800)
    kamera((50, -500, 560), ziel, 50)
    return 1500, 1200


# Aufbau der Stufe 2: Ursprung ist die linke vordere Ecke der Switch-Platte
BRETT = {
    "switch": (0, 0, 0),
    "router": (PLATTE_L + KABEL_L, PLATTE_B / 2 - (BUCHT_Y0 + BUCHT_B / 2), 0),
    "web": (2 * (PLATTE_L + KABEL_L), PLATTE_B / 2 - (BUCHT_Y0 + BUCHT_B / 2), 0),
    "intra": (-KABEL_L, PLATTE_B / 2 + BUCHT_Y0 + BUCHT_B / 2, 180),
    "pc1": (PLATTE_L / 2 + BUCHT_Y0 + BUCHT_B / 2, PLATTE_B + KABEL_L, 90),
    "pc2": (PLATTE_L / 2 - (BUCHT_Y0 + BUCHT_B / 2), -KABEL_L, -90),
}


def _brett(stufe=2):
    mitte = PLATTE_B / 2 - KABEL_B / 2
    platten = {"switch": platte("switch", *BRETT["switch"], karten=("mac_tabelle",))}
    for name in ("intra", "pc1", "pc2"):
        platten[name] = _host_mit_karten(*BRETT[name], name=name)
    kabel(-KABEL_L, mitte)
    kabel(PLATTE_L / 2 + KABEL_B / 2, PLATTE_B, 90)
    kabel(PLATTE_L / 2 - KABEL_B / 2, 0, -90)
    if stufe >= 2:
        platten["router"] = platte("router", *BRETT["router"],
                                   karten=("router_schnittstellen", "routing_tabelle"))
        platten["web"] = _host_mit_karten(*BRETT["web"], name="web")
        kabel(PLATTE_L, mitte)
        kabel(2 * PLATTE_L + KABEL_L, mitte)
    return platten


def szene_spielbrett():
    """Ganzer Aufbau der Stufe 2, ein Frame steckt gerade im Switch."""
    tisch((270, 100))
    p = _brett(2)
    schale(zmac=MAC["R-A"], qmac=MAC["PC 1"], inhalt=HTTPS_FERN, **in_bucht(p["switch"], "switch"))
    paket(inhalt=DNS_LOKAL, stufen=2, **auf_montageplatz(p["pc2"]))
    schale(fcs_ok=None, **in_bucht(p["pc2"]))
    ziel = (270, 85, 0)
    licht(ziel, 1500)
    kamera((270, -600, 1180), ziel, 40)
    return 2000, 1450


def szene_spielbrett_oben():
    """Aufbau der Stufe 2 genau von oben, als Plan."""
    tisch((270, 100))
    _brett(2)
    licht((270, 100, 0), 1500)
    kamera((270, 100, 2500), (270, 100.001, 0), ortho=1230)
    return 2000, 1420


def szene_spielbrett_stufe1():
    tisch((0, 100))
    _brett(1)
    licht((0, 100, 0), 1300)
    kamera((0, 100, 2500), (0, 100.001, 0), ortho=900)
    return 1500, 1420


def szene_material():
    """Alle Teile eines Satzes nebeneinander."""
    tisch((300, 150))
    a = anker(0, 0, 0)
    teil("vorratskasten", a)
    sorten = [
        [text for text, _ in spieldaten.plaettchen()["mac"]],
        ["10.0.1.11", "10.0.1.12", "10.0.1.20", "10.0.2.10", "10.0.1.1", "10.0.2.1"],
        ["80", "443", "53", "123", "25", "49152", "50001", "51515", "60000"],
        ["HTTP", "HTTPS", "DNS", "NTP", "SMTP"],
    ]
    for s, texte in enumerate(sorten):
        for z, text in enumerate(texte):
            x = 2 + s * KASTEN_SPALTE + 0.6
            y = KASTEN_B - 13 - (z + 1) * KASTEN_ZEILE + 0.6
            anzahl = 1 if (s == 2 and z >= 5) else 2
            for i in range(anzahl):
                plaettchen(text, a, x, y, KASTEN_H - KASTEN_FACH_T + i * PL_H)
    for i in range(3):
        schale(None, 250, 150 - i * 72, 0, fcs_ok=None)
    x0 = 345
    for i, name in enumerate(["ip_header"] * 3 + ["tcp_header"] * 2 + ["udp_header"] * 2):
        teil(name, anker(x0 + (i % 4) * 68 + (10 if "ip" not in name else 0), -75 - (i // 4) * 66, 0))
    for i in range(3):
        teil("daten_block", anker(500 + 15, 150 - i * 66, 0))
    for i in range(4):
        fcs(None, 250 + i * 22, -40, 0, ok=(i != 3))
    for i in range(6):
        teil("stoerungs_chip", anker(20 + i * 34, -45, 0))
    for i in range(3):
        kabel(20 + i * 110, -140)
    ziel = (305, 20, 0)
    licht(ziel, 1100)
    kamera((305, -600, 960), ziel, 55)
    return 2000, 1300


SZENEN = {
    "titel": szene_titel,
    "dateneinheit": szene_dateneinheit,
    "dateneinheit_teile": szene_dateneinheit_teile,
    "schritt_1": lambda: _schritt(1), "schritt_2": lambda: _schritt(2),
    "schritt_3": lambda: _schritt(3), "schritt_4": lambda: _schritt(4),
    "schritt_5": lambda: _schritt(5),
    "switch": szene_switch,
    "router": szene_router,
    "spielbrett": szene_spielbrett,
    "spielbrett_oben": szene_spielbrett_oben,
    "spielbrett_stufe1": szene_spielbrett_stufe1,
    "material": szene_material,
}


def main():
    argumente = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    entwurf = "--entwurf" in argumente
    namen = [a for a in argumente if not a.startswith("--")] or list(SZENEN)
    for name in namen:
        leere_szene()
        breite, hoehe = SZENEN[name]()
        ausgabe(name, breite, hoehe, entwurf)


if __name__ == "__main__":
    main()
