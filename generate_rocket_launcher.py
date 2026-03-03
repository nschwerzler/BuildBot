"""
Spring-Loaded Rocket Launcher — Bambu Studio / FDM Printable
=============================================================
3 printed parts + 1 real metal spring = working spring-loaded rocket launcher.

PARTS TO PRINT:
  rocket_body.stl      — the projectile (rocket)
  launcher_body.stl    — outer tube + base
  plunger.stl          — inner piston that compresses the spring

SPRING TO BUY (very common compression spring):
  Outer diameter : 8 mm
  Wire diameter  : 0.8 mm
  Free length    : 22 mm
  Type           : Compression spring
  Search: "8mm OD compression spring" on Amazon / hardware store
  Cost: ~$1-2 for a pack

HOW TO USE:
  1. Drop the spring into the launcher tube (it sits around the guide post)
  2. Push the plunger into the tube on top of the spring
  3. Place the rocket on the plunger peg
  4. Push rocket + plunger down to compress the spring (hold with fingers)
  5. Let go — spring launches the rocket!

PRINT SETTINGS (each part separately):
  Layer height : 0.2 mm
  Walls        : 3
  Infill       : 20%
  Material     : PLA
"""
import math, os, zipfile

# ── Parameters ───────────────────────────────────────────────────────────────

# Launcher body
BASE_R      = 20.0    # Base plate radius (mm)
BASE_H      = 4.0     # Base plate thickness
TUBE_OD     = 8.0     # Tube outer radius
TUBE_ID     = 5.3     # Tube inner bore radius  (fits 10.0mm OD plunger + 0.3mm gap)
TUBE_H      = 34.0    # Tube height above base
GUIDE_R     = 2.2     # Center guide post radius (spring wraps around it)
GUIDE_H     = 14.0    # Guide post height

# Plunger
PLUNGER_R   = 5.0     # Plunger radius (snug in tube bore)
PLUNGER_H   = 30.0    # Plunger body height
PEG_R       = 2.0     # Launch peg radius
PEG_H       = 10.0    # Launch peg height above plunger top

# Rocket
ROCKET_R    = 4.2     # Rocket body radius
ROCKET_H    = 45.0    # Rocket body cylinder height
NOSE_H      = 14.0    # Nose cone height
NOSE_SEGS   = 10      # Nose cone taper rings
FIN_SPAN    = 9.0     # Fin radius from body center
FIN_H       = 18.0    # Fin height
FIN_T       = 1.4     # Fin thickness (half-thickness each side)
SOCKET_R    = 2.2     # Rocket socket inner radius (fits 2mm peg + 0.2mm)
SOCKET_D    = 12.0    # Rocket socket depth

# Spring model (visual guide inside the assembly view)
SPR_COIL_R  = 3.3     # Spring coil center-line radius
SPR_WIRE_R  = 0.55    # Wire visual radius
SPR_COILS   = 6
SPR_PITCH   = 3.3     # mm per coil
SPR_STEPS   = 48
SPR_CS      = 10

SEGS = 36             # General cylinder resolution

OUT_DIR = os.path.dirname(os.path.abspath(__file__))


# ── Mesh ─────────────────────────────────────────────────────────────────────
class Mesh:
    def __init__(self):
        self.verts = []
        self.tris  = []
        self._vmap = {}

    def v(self, x, y, z):
        key = (round(x, 4), round(y, 4), round(z, 4))
        if key not in self._vmap:
            self._vmap[key] = len(self.verts)
            self.verts.append(key)
        return self._vmap[key]

    def tri(self, a, b, c):
        ia, ib, ic = self.v(*a), self.v(*b), self.v(*c)
        if ia != ib and ib != ic and ia != ic:
            self.tris.append((ia, ib, ic))

    def quad(self, a, b, c, d):
        self.tri(a, b, c)
        self.tri(a, c, d)

    def _pts(self, cx, cy, z, r, segs):
        return [(cx + r*math.cos(2*math.pi*i/segs),
                 cy + r*math.sin(2*math.pi*i/segs), z)
                for i in range(segs)]

    def disk(self, cx, cy, z, r, segs, flip=False):
        ctr = (cx, cy, z)
        pts = self._pts(cx, cy, z, r, segs)
        for i in range(segs):
            j = (i+1) % segs
            self.tri(ctr, pts[j], pts[i]) if not flip else self.tri(ctr, pts[i], pts[j])

    def cyl_wall(self, cx, cy, z0, z1, r, segs):
        b = self._pts(cx, cy, z0, r, segs)
        t = self._pts(cx, cy, z1, r, segs)
        for i in range(segs):
            j = (i+1) % segs
            self.quad(b[i], b[j], t[j], t[i])

    def solid_cyl(self, cx, cy, z0, z1, r, segs):
        self.cyl_wall(cx, cy, z0, z1, r, segs)
        self.disk(cx, cy, z0, r, segs, flip=True)
        self.disk(cx, cy, z1, r, segs)

    def tube(self, cx, cy, z0, z1, ro, ri, segs):
        """Hollow tube with inner + outer walls + top + bottom annular rings."""
        ob = self._pts(cx, cy, z0, ro, segs)
        ot = self._pts(cx, cy, z1, ro, segs)
        ib = self._pts(cx, cy, z0, ri, segs)
        it_ = self._pts(cx, cy, z1, ri, segs)
        for i in range(segs):
            j = (i+1) % segs
            self.quad(ob[i], ob[j], ot[j], ot[i])          # outer wall
            self.quad(ib[j], ib[i], it_[i], it_[j])        # inner wall
            self.quad(ob[j], ob[i], ib[i], ib[j])          # bottom ring
            self.quad(ot[i], ot[j], it_[j], it_[i])        # top ring

    def cone(self, cx, cy, z_base, z_tip, r_base, segs, rings=8):
        """Tapered cone from r_base at z_base to point at z_tip."""
        prev = self._pts(cx, cy, z_base, r_base, segs)
        for k in range(1, rings + 1):
            t  = k / rings
            zk = z_base + (z_tip - z_base) * t
            rk = r_base * (1 - t)
            if rk < 0.001:
                tip = (cx, cy, z_tip)
                for i in range(segs):
                    j = (i+1) % segs
                    self.tri(tip, prev[i], prev[j])
                break
            cur = self._pts(cx, cy, zk, rk, segs)
            for i in range(segs):
                j = (i+1) % segs
                self.quad(prev[i], prev[j], cur[j], cur[i])
            prev = cur

    def fin(self, angle_deg, body_r, span, height, thickness, z_base):
        """Single swept fin at given angle around Z axis."""
        a   = math.radians(angle_deg)
        ca, sa = math.cos(a), math.sin(a)
        # Normal direction (perpendicular to fin face, in-plane)
        na, nb = -sa, ca   # rotated 90 deg from radial
        # 4 corners of the fin (a thin box)
        r0, r1 = body_r, span     # inner and outer edge radii
        z0, z1 = z_base, z_base + height
        # Fin center line runs radially outward
        # Build thin flat panel: 4 corners x 2 sides (thickness)
        def pt(ri, zi, side):
            off = thickness * side
            return (ri*ca + off*na, ri*sa + off*nb, zi)
        corners = [(r0, z0), (r1, z0), (r1, z1), (r0, z1)]
        front = [pt(r, z,  1) for r, z in corners]
        back  = [pt(r, z, -1) for r, z in corners]
        # Faces
        self.quad(front[0], front[1], front[2], front[3])   # front face
        self.quad(back[3],  back[2],  back[1],  back[0])    # back face
        self.quad(front[0], back[0],  back[1],  front[1])   # bottom edge
        self.quad(front[1], back[1],  back[2],  front[2])   # outer edge
        self.quad(front[2], back[2],  back[3],  front[3])   # top edge
        self.quad(front[3], back[3],  back[0],  front[0])   # inner edge

    def spring_coil(self, coil_r, wire_r, coils, pitch, steps, cs, z_off=0):
        """Visual coil spring along Z axis."""
        ppr = pitch / (2 * math.pi)
        total = coils * steps
        rings = []
        centers = []
        for i in range(total + 1):
            t = 2 * math.pi * i / steps
            cos_t, sin_t = math.cos(t), math.sin(t)
            pos = (coil_r * cos_t, coil_r * sin_t, ppr * t + z_off)
            T   = (-coil_r * sin_t, coil_r * cos_t, ppr)
            tl  = math.sqrt(sum(x*x for x in T))
            T   = tuple(x/tl for x in T)
            N   = (-cos_t, -sin_t, 0.0)
            B   = (T[1]*N[2]-T[2]*N[1], T[2]*N[0]-T[0]*N[2], T[0]*N[1]-T[1]*N[0])
            ring = []
            for j in range(cs):
                a = 2*math.pi*j/cs
                ca, sa = math.cos(a), math.sin(a)
                ring.append((pos[0]+wire_r*(ca*N[0]+sa*B[0]),
                             pos[1]+wire_r*(ca*N[1]+sa*B[1]),
                             pos[2]+wire_r*(ca*N[2]+sa*B[2])))
            rings.append(ring)
            centers.append(pos)
        for i in range(total):
            r0, r1 = rings[i], rings[i+1]
            for j in range(cs):
                k = (j+1) % cs
                self.quad(r0[j], r0[k], r1[k], r1[j])
        for j in range(cs):
            k = (j+1) % cs
            self.tri(centers[0],  rings[0][k],   rings[0][j])
            self.tri(centers[-1], rings[-1][j],   rings[-1][k])

    def floor_to_z0(self):
        if not self.verts:
            return
        z_min = min(v[2] for v in self.verts)
        if abs(z_min) > 1e-6:
            self.verts = [(x, y, z - z_min) for x, y, z in self.verts]
            self._vmap = {k: i for i, k in enumerate(self.verts)}

    def translate(self, dx, dy, dz=0):
        self.verts = [(x+dx, y+dy, z+dz) for x, y, z in self.verts]
        self._vmap = {k: i for i, k in enumerate(self.verts)}

    def merge(self, other):
        """Append another mesh's geometry into this one."""
        offset = len(self.verts)
        self.verts.extend(other.verts)
        for ia, ib, ic in other.tris:
            self.tris.append((ia + offset, ib + offset, ic + offset))
        self._vmap = {k: i for i, k in enumerate(self.verts)}

    def _normal(self, ia, ib, ic):
        a, b, c = self.verts[ia], self.verts[ib], self.verts[ic]
        ux, uy, uz = b[0]-a[0], b[1]-a[1], b[2]-a[2]
        vx, vy, vz = c[0]-a[0], c[1]-a[1], c[2]-a[2]
        nx = uy*vz - uz*vy
        ny = uz*vx - ux*vz
        nz = ux*vy - uy*vx
        ln = math.sqrt(nx*nx + ny*ny + nz*nz)
        return (nx/ln, ny/ln, nz/ln) if ln > 1e-12 else (0, 0, 1)

    def save_stl(self, path):
        name = os.path.splitext(os.path.basename(path))[0]
        with open(path, 'w') as f:
            f.write(f"solid {name}\n")
            for ia, ib, ic in self.tris:
                n = self._normal(ia, ib, ic)
                a, b, c = self.verts[ia], self.verts[ib], self.verts[ic]
                f.write(f"  facet normal {n[0]:.6e} {n[1]:.6e} {n[2]:.6e}\n")
                f.write("    outer loop\n")
                for p in (a, b, c):
                    f.write(f"      vertex {p[0]:.6e} {p[1]:.6e} {p[2]:.6e}\n")
                f.write("    endloop\n  endfacet\n")
            f.write(f"endsolid {name}\n")
        kb = os.path.getsize(path) // 1024
        print(f"  STL  {len(self.tris):>6} tris  {kb} KB  ->  {os.path.basename(path)}")

    def save_3mf(self, path):
        vl = [f'          <vertex x="{x}" y="{y}" z="{z}"/>' for x, y, z in self.verts]
        tl = [f'          <triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in self.tris]
        model = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<model unit="millimeter"'
            ' xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">\n'
            '  <metadata name="Application">RocketLauncherGen</metadata>\n'
            '  <resources>\n    <object id="1" type="model">\n      <mesh>\n'
            '        <vertices>\n' + '\n'.join(vl) + '\n        </vertices>\n'
            '        <triangles>\n' + '\n'.join(tl) + '\n        </triangles>\n'
            '      </mesh>\n    </object>\n  </resources>\n'
            '  <build>\n    <item objectid="1"/>\n  </build>\n</model>')
        ct = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
            '  <Default Extension="rels"'
            ' ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n'
            '  <Default Extension="model"'
            ' ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>\n'
            '</Types>')
        rels = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<Relationships'
            ' xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
            '  <Relationship Target="/3D/3dmodel.model" Id="rel0"'
            ' Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n'
            '</Relationships>')
        with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr('[Content_Types].xml', ct)
            zf.writestr('_rels/.rels', rels)
            zf.writestr('3D/3dmodel.model', model)
        kb = os.path.getsize(path) // 1024
        print(f"  3MF  {len(self.tris):>6} tris  {kb} KB  ->  {os.path.basename(path)}")


# ── Part Builders ─────────────────────────────────────────────────────────────

def build_launcher_body(z0=0.0):
    """Outer tube + wide base. Spring and plunger slide inside the tube."""
    m = Mesh()
    zb = z0 + BASE_H          # top of base plate = bottom of tube

    # Wide base plate
    m.solid_cyl(0, 0, z0, zb, BASE_R, SEGS)

    # Launch tube (hollow cylinder)
    m.tube(0, 0, zb, zb + TUBE_H, TUBE_OD, TUBE_ID, SEGS)

    # Center guide post inside tube (spring wraps around this)
    m.solid_cyl(0, 0, zb, zb + GUIDE_H, GUIDE_R, 16)

    m.floor_to_z0()
    return m


def build_plunger(z0=0.0):
    """Solid piston that slides into the tube. Top has a peg for the rocket."""
    m = Mesh()

    # Main cylinder body
    m.solid_cyl(0, 0, z0, z0 + PLUNGER_H, PLUNGER_R, SEGS)

    # Launch peg on top
    m.solid_cyl(0, 0, z0 + PLUNGER_H, z0 + PLUNGER_H + PEG_H, PEG_R, 20)

    m.floor_to_z0()
    return m


def build_rocket(z0=0.0):
    """Rocket projectile: hollow socket at bottom (fits peg), body tube, nose cone, 3 fins."""
    m = Mesh()

    # Socket at bottom (hollow tube = the peg hole)
    m.tube(0, 0, z0, z0 + SOCKET_D, ROCKET_R, SOCKET_R, SEGS)

    # Main body above socket
    m.solid_cyl(0, 0, z0 + SOCKET_D, z0 + ROCKET_H, ROCKET_R, SEGS)

    # Nose cone
    m.cone(0, 0, z0 + ROCKET_H, z0 + ROCKET_H + NOSE_H, ROCKET_R, SEGS, rings=NOSE_SEGS)

    # 3 fins at 120-degree intervals, starting from socket top
    for angle in [0, 120, 240]:
        m.fin(angle, ROCKET_R, FIN_SPAN, FIN_H, FIN_T, z0 + SOCKET_D)

    # Bottom disk cap for the socket annular ring
    # (already closed by tube's bottom ring, nothing extra needed)

    m.floor_to_z0()
    return m


def build_assembly():
    """All 3 parts + spring model shown in assembled/ready-to-fire position."""
    m = Mesh()

    # Z positions in assembly
    z_base     = 0.0
    z_tube_bot = z_base + BASE_H          # 4
    z_tube_top = z_tube_bot + TUBE_H      # 38

    # Spring sits at bottom of tube bore, around guide post
    # Spring free length = SPR_COILS * SPR_PITCH
    spring_len = SPR_COILS * SPR_PITCH    # ~20mm
    z_spring   = z_tube_bot              # spring bottom at tube floor

    # Plunger rests on top of spring (spring extended = plunger raised)
    z_plunger_bot = z_spring + spring_len  # plunger bottom = spring top
    z_plunger_top = z_plunger_bot + PLUNGER_H
    z_peg_top     = z_plunger_top + PEG_H

    # Rocket sits on plunger peg
    z_rocket      = z_plunger_top         # rocket bottom = plunger top

    # -- Launcher body --
    m.solid_cyl(0, 0, z_base, z_tube_bot, BASE_R, SEGS)
    m.tube(0, 0, z_tube_bot, z_tube_top, TUBE_OD, TUBE_ID, SEGS)
    m.solid_cyl(0, 0, z_tube_bot, z_tube_bot + GUIDE_H, GUIDE_R, 16)

    # -- Spring (visual model of where real spring goes) --
    m.spring_coil(SPR_COIL_R, SPR_WIRE_R, SPR_COILS, SPR_PITCH,
                  SPR_STEPS, SPR_CS, z_off=z_spring)

    # -- Plunger --
    m.solid_cyl(0, 0, z_plunger_bot, z_plunger_top, PLUNGER_R, SEGS)
    m.solid_cyl(0, 0, z_plunger_top, z_peg_top,      PEG_R,     20)

    # -- Rocket --
    m.tube(0, 0, z_rocket, z_rocket + SOCKET_D, ROCKET_R, SOCKET_R, SEGS)
    m.solid_cyl(0, 0, z_rocket + SOCKET_D, z_rocket + ROCKET_H, ROCKET_R, SEGS)
    m.cone(0, 0, z_rocket + ROCKET_H, z_rocket + ROCKET_H + NOSE_H, ROCKET_R, SEGS, NOSE_SEGS)
    for angle in [0, 120, 240]:
        m.fin(angle, ROCKET_R, FIN_SPAN, FIN_H, FIN_T, z_rocket + SOCKET_D)

    m.floor_to_z0()
    return m


def build_print_plate():
    """All 3 parts laid out side-by-side on one print plate, each at z=0."""
    # Build each part at origin, then translate to non-overlapping positions.
    # Footprints (radius):  body=BASE_R=20, plunger=PLUNGER_R=5, rocket=FIN_SPAN=9
    GAP = 6.0   # mm between parts

    body = build_launcher_body()
    # already at origin, footprint radius = BASE_R (20mm)

    plunger = build_plunger()
    plunger.translate(BASE_R + GAP + PLUNGER_R, 0)   # x = 20 + 6 + 5 = 31

    rocket = build_rocket()
    rocket_x = BASE_R + GAP + PLUNGER_R*2 + GAP + FIN_SPAN
    rocket.translate(rocket_x, 0)                     # x = 20 + 6 + 10 + 6 + 9 = 51

    plate = Mesh()
    plate.merge(body)
    plate.merge(plunger)
    plate.merge(rocket)
    return plate


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("=== Spring-Loaded Rocket Launcher ===")
    print()
    print("Spring to buy:")
    print(f"  OD {SPR_COIL_R*2 + SPR_WIRE_R*2:.0f} mm  wire {SPR_WIRE_R*2:.1f} mm  length ~{SPR_COILS*SPR_PITCH:.0f} mm")
    print('  Search: "8mm OD compression spring" - very common, ~$1')
    print()

    print("Building print plate (all 3 parts, one plate)...")
    plate = build_print_plate()
    plate.save_3mf(os.path.join(OUT_DIR, "rocket_launcher_plate.3mf"))

    print()
    print("Building assembly preview...")
    asm = build_assembly()
    asm.save_3mf(os.path.join(OUT_DIR, "rocket_launcher_assembly.3mf"))

    print()
    print("Done!")
    print()
    print("PRINT: open rocket_launcher_plate.3mf  (all 3 parts on one plate)")
    print("PREVIEW: open rocket_launcher_assembly.3mf")
    print()
    print("How to launch:")
    print("  1. Drop spring in tube")
    print("  2. Push plunger into tube")
    print("  3. Place rocket on plunger peg")
    print("  4. Push down and release!")
