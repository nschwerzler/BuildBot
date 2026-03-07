"""
Horizontal Spring-Loaded Rocket Launcher — Bambu Studio / FDM Printable
========================================================================
3 printed parts + 1 real metal spring = working launcher.
The rocket launches HORIZONTALLY (sideways) out the front of the barrel.

PARTS TO PRINT (all on one plate):
  1. barrel.stl     — launch tube (printed upright, used horizontally)
  2. rocket.stl     — the dart/projectile
  3. cradle.stl     — holds barrel horizontal on a table

SPRING TO BUY:
  Outer diameter : 8 mm
  Wire diameter  : 0.8-1.0 mm
  Free length    : 22 mm
  Type           : Compression spring
  Search: "8mm OD compression spring" ~$1-2

HOW TO USE:
  1. Set barrel in cradle (closed end = back, open end = front)
  2. Drop spring into barrel from the back (closed) end — it wraps around guide post
  3. Insert dart nose-first into the FRONT (open) end
  4. Push dart backward with a finger to compress the spring
  5. Point at target, release finger — spring launches dart!

PRINT SETTINGS:
  Layer height : 0.2 mm
  Walls        : 3
  Infill       : 20%
  Material     : PLA
"""
import math, os, zipfile

# ── Parameters ───────────────────────────────────────────────────────────────

# Barrel (printed upright Z, used horizontally X)
BARREL_LEN  = 80.0   # barrel length (mm)
BARREL_OR   =  7.0   # barrel outer radius  → 14mm OD
BARREL_IR   =  5.0   # barrel inner bore radius → 10mm ID
GUIDE_R     =  2.8   # spring guide post radius (spring wraps around it)
GUIDE_H     = 14.0   # guide post height

# Rocket dart (prints upright)
DART_R      =  4.6   # dart body radius → 9.2mm OD (0.4mm gap in bore each side)
DART_H      = 55.0   # dart body cylinder height
NOSE_H      = 14.0   # nose cone height
NOSE_SEGS   = 12     # nose cone ring count

# Cradle (prints flat, holds barrel horizontal)
CRADLE_BASE_H  = 4.0    # base plate thickness
CRADLE_PRONG_H = 12.0   # prong height above base (must be > BARREL_OR so barrel can't roll out)
CRADLE_PRONG_W = 5.0    # prong width
CRADLE_PRONG_D = 12.0   # prong depth (along barrel axis)
CRADLE_GAP     = BARREL_OR * 2 + 0.5   # gap between prongs (barrel fits with clearance)

# Spring model (visual in assembly view)
SPR_COIL_R = 3.3
SPR_WIRE_R = 0.5
SPR_COILS  = 6
SPR_PITCH  = 3.2
SPR_STEPS  = 40
SPR_CS     = 10

SEGS = 36

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

    # ── Z-axis primitives ────────────────────────────────────────────────────

    def _pts_z(self, cx, cy, z, r, segs):
        return [(cx + r*math.cos(2*math.pi*i/segs),
                 cy + r*math.sin(2*math.pi*i/segs), z)
                for i in range(segs)]

    def disk_z(self, cx, cy, z, r, segs, flip=False):
        ctr = (cx, cy, z)
        pts = self._pts_z(cx, cy, z, r, segs)
        for i in range(segs):
            j = (i+1) % segs
            self.tri(ctr, pts[j], pts[i]) if not flip else self.tri(ctr, pts[i], pts[j])

    def cyl_z(self, cx, cy, z0, z1, r, segs):
        b = self._pts_z(cx, cy, z0, r, segs)
        t = self._pts_z(cx, cy, z1, r, segs)
        for i in range(segs):
            j = (i+1) % segs
            self.quad(b[i], b[j], t[j], t[i])

    def solid_cyl_z(self, cx, cy, z0, z1, r, segs):
        self.cyl_z(cx, cy, z0, z1, r, segs)
        self.disk_z(cx, cy, z0, r, segs, flip=True)
        self.disk_z(cx, cy, z1, r, segs)

    def tube_z(self, cx, cy, z0, z1, ro, ri, segs):
        ob = self._pts_z(cx, cy, z0, ro, segs)
        ot = self._pts_z(cx, cy, z1, ro, segs)
        ib = self._pts_z(cx, cy, z0, ri, segs)
        it_ = self._pts_z(cx, cy, z1, ri, segs)
        for i in range(segs):
            j = (i+1) % segs
            self.quad(ob[i], ob[j], ot[j], ot[i])
            self.quad(ib[j], ib[i], it_[i], it_[j])
            self.quad(ob[j], ob[i], ib[i], ib[j])
            self.quad(ot[i], ot[j], it_[j], it_[i])

    # ── X-axis primitives (barrel lies along X) ──────────────────────────────

    def _pts_x(self, x, cy, cz, r, segs):
        return [(x, cy + r*math.cos(2*math.pi*i/segs),
                    cz + r*math.sin(2*math.pi*i/segs))
                for i in range(segs)]

    def disk_x(self, x, cy, cz, r, segs, flip=False):
        ctr = (x, cy, cz)
        pts = self._pts_x(x, cy, cz, r, segs)
        for i in range(segs):
            j = (i+1) % segs
            self.tri(ctr, pts[i], pts[j]) if not flip else self.tri(ctr, pts[j], pts[i])

    def cyl_x(self, x0, x1, cy, cz, r, segs):
        b = self._pts_x(x0, cy, cz, r, segs)
        t = self._pts_x(x1, cy, cz, r, segs)
        for i in range(segs):
            j = (i+1) % segs
            self.quad(b[i], b[j], t[j], t[i])

    def solid_cyl_x(self, x0, x1, cy, cz, r, segs):
        self.cyl_x(x0, x1, cy, cz, r, segs)
        self.disk_x(x0, cy, cz, r, segs, flip=True)
        self.disk_x(x1, cy, cz, r, segs)

    def tube_x(self, x0, x1, cy, cz, ro, ri, segs):
        ob = self._pts_x(x0, cy, cz, ro, segs)
        ot = self._pts_x(x1, cy, cz, ro, segs)
        ib = self._pts_x(x0, cy, cz, ri, segs)
        it_ = self._pts_x(x1, cy, cz, ri, segs)
        for i in range(segs):
            j = (i+1) % segs
            self.quad(ob[i], ob[j], ot[j], ot[i])
            self.quad(ib[j], ib[i], it_[i], it_[j])
            self.quad(ob[j], ob[i], ib[i], ib[j])
            self.quad(ot[i], ot[j], it_[j], it_[i])

    # ── Box ──────────────────────────────────────────────────────────────────

    def box(self, x0, y0, z0, x1, y1, z1):
        a=(x0,y0,z0); b=(x1,y0,z0); c=(x1,y1,z0); d=(x0,y1,z0)
        e=(x0,y0,z1); f=(x1,y0,z1); g=(x1,y1,z1); h=(x0,y1,z1)
        self.quad(d,c,b,a); self.quad(e,f,g,h)
        self.quad(a,b,f,e); self.quad(b,c,g,f)
        self.quad(c,d,h,g); self.quad(d,a,e,h)

    # ── Spring coil along X axis ─────────────────────────────────────────────

    def spring_x(self, x_start, coil_r, wire_r, coils, pitch, steps, cs, cy=0, cz=0):
        """Coil spring with axis along X."""
        ppr = pitch / (2 * math.pi)
        total = coils * steps
        rings = []
        centers = []
        for i in range(total + 1):
            t = 2 * math.pi * i / steps
            cos_t, sin_t = math.cos(t), math.sin(t)
            # Helix along X: x=ppr*t, yz=coil
            pos = (x_start + ppr * t, cy + coil_r * cos_t, cz + coil_r * sin_t)
            # Tangent
            tx, ty, tz = ppr, -coil_r * sin_t, coil_r * cos_t
            tl = math.sqrt(tx*tx + ty*ty + tz*tz)
            T = (tx/tl, ty/tl, tz/tl)
            # Normal (toward X axis)
            N = (0.0, -cos_t, -sin_t)
            # Binormal
            B = (T[1]*N[2]-T[2]*N[1], T[2]*N[0]-T[0]*N[2], T[0]*N[1]-T[1]*N[0])
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
            self.tri(centers[0],  rings[0][k],  rings[0][j])
            self.tri(centers[-1], rings[-1][j],  rings[-1][k])

    # ── Cone along Z ─────────────────────────────────────────────────────────

    def cone_z(self, cx, cy, z_base, z_tip, r_base, segs, rings=10):
        prev = self._pts_z(cx, cy, z_base, r_base, segs)
        for k in range(1, rings + 1):
            t = k / rings
            zk = z_base + (z_tip - z_base) * t
            rk = r_base * (1 - t)
            if rk < 0.001:
                tip = (cx, cy, z_tip)
                for i in range(segs):
                    j = (i+1) % segs
                    self.tri(tip, prev[i], prev[j])
                break
            cur = self._pts_z(cx, cy, zk, rk, segs)
            for i in range(segs):
                j = (i+1) % segs
                self.quad(prev[i], prev[j], cur[j], cur[i])
            prev = cur

    # ── Utilities ────────────────────────────────────────────────────────────

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
        offset = len(self.verts)
        self.verts.extend(other.verts)
        for ia, ib, ic in other.tris:
            self.tris.append((ia+offset, ib+offset, ic+offset))
        self._vmap = {k: i for i, k in enumerate(self.verts)}

    def _normal(self, ia, ib, ic):
        a, b, c = self.verts[ia], self.verts[ib], self.verts[ic]
        ux,uy,uz = b[0]-a[0],b[1]-a[1],b[2]-a[2]
        vx,vy,vz = c[0]-a[0],c[1]-a[1],c[2]-a[2]
        nx=uy*vz-uz*vy; ny=uz*vx-ux*vz; nz=ux*vy-uy*vx
        ln=math.sqrt(nx*nx+ny*ny+nz*nz)
        return (nx/ln,ny/ln,nz/ln) if ln>1e-12 else (0,0,1)

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
        vl = [f'          <vertex x="{x}" y="{y}" z="{z}"/>' for x,y,z in self.verts]
        tl = [f'          <triangle v1="{a}" v2="{b}" v3="{c}"/>' for a,b,c in self.tris]
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

def build_barrel():
    """
    Hollow tube — closed back end (spring seat), open front (rocket exits).
    Printed upright (Z axis), used horizontally (X axis) in the cradle.
    Closed end goes DOWN when printing = goes BACK when in cradle.
    """
    m = Mesh()
    # Main barrel tube (closed bottom = back, open top = front)
    m.tube_z(0, 0, 0, BARREL_LEN, BARREL_OR, BARREL_IR, SEGS)
    # Back cap (closed bottom)
    m.disk_z(0, 0, 0, BARREL_OR, SEGS, flip=True)
    # Spring guide post at closed end (inside bore, sticking inward)
    m.solid_cyl_z(0, 0, 0, GUIDE_H, GUIDE_R, 20)
    # Front is open — no cap needed
    m.floor_to_z0()
    return m


def build_rocket():
    """Slim dart: cylindrical body + nose cone. Fits inside the barrel bore."""
    m = Mesh()
    # Body cylinder
    m.solid_cyl_z(0, 0, 0, DART_H, DART_R, SEGS)
    # Nose cone (on top when printing = front when launching)
    m.cone_z(0, 0, DART_H, DART_H + NOSE_H, DART_R, SEGS, NOSE_SEGS)
    m.floor_to_z0()
    return m


def build_cradle():
    """
    Two pairs of prongs on a flat base that hold the barrel horizontal.
    Printed flat on the bed.

    Side view of one prong pair:
      ||   ||   <- prongs (barrel rests between them)
      ||   ||
      [base]
    """
    m = Mesh()
    OUTER_W = CRADLE_GAP + 2 * CRADLE_PRONG_W  # total width of one prong pair

    # How far from each end of the barrel the prong stations sit
    STATION_INSET = 8.0
    sx0 = STATION_INSET                         # front station x
    sx1 = BARREL_LEN - STATION_INSET - CRADLE_PRONG_D   # back station x

    # Base plate spanning both stations
    base_x0 = sx0 - 5
    base_x1 = sx1 + CRADLE_PRONG_D + 5
    half_w = OUTER_W / 2
    m.box(base_x0, -half_w, 0, base_x1, half_w, CRADLE_BASE_H)

    # Two prong stations
    for sx in (sx0, sx1):
        ex = sx + CRADLE_PRONG_D
        z0 = CRADLE_BASE_H
        z1 = CRADLE_BASE_H + CRADLE_PRONG_H
        # Left prong
        m.box(sx, -half_w,              z0, ex, -CRADLE_GAP/2, z1)
        # Right prong
        m.box(sx,  CRADLE_GAP/2,        z0, ex,  half_w,       z1)

    m.floor_to_z0()
    return m


def build_assembly():
    """All parts in use position: barrel horizontal in cradle, dart loaded, spring visible."""
    m = Mesh()

    # Cradle on ground
    OUTER_W  = CRADLE_GAP + 2 * CRADLE_PRONG_W
    STATION_INSET = 8.0
    sx0 = STATION_INSET
    sx1 = BARREL_LEN - STATION_INSET - CRADLE_PRONG_D
    half_w = OUTER_W / 2
    base_x0 = sx0 - 5
    base_x1 = sx1 + CRADLE_PRONG_D + 5
    m.box(base_x0, -half_w, 0, base_x1, half_w, CRADLE_BASE_H)
    for sx in (sx0, sx1):
        ex = sx + CRADLE_PRONG_D
        z0 = CRADLE_BASE_H
        z1 = CRADLE_BASE_H + CRADLE_PRONG_H
        m.box(sx, -half_w,       z0, ex, -CRADLE_GAP/2, z1)
        m.box(sx,  CRADLE_GAP/2, z0, ex,  half_w,       z1)

    # Barrel center height in cradle
    barrel_cz = CRADLE_BASE_H + BARREL_OR   # center of barrel cross-section
    # Barrel horizontal along X (x=0 = back/closed, x=BARREL_LEN = front/open)
    m.tube_x(0, BARREL_LEN, 0, barrel_cz, BARREL_OR, BARREL_IR, SEGS)
    m.disk_x(0, 0, barrel_cz, BARREL_OR, SEGS, flip=True)   # closed back cap
    # Guide post along X inside barrel (from back)
    m.solid_cyl_x(0, GUIDE_H, 0, barrel_cz, GUIDE_R, 20)

    # Spring coil inside barrel near back
    spring_len = SPR_COILS * SPR_PITCH
    m.spring_x(GUIDE_H, SPR_COIL_R, SPR_WIRE_R, SPR_COILS, SPR_PITCH,
               SPR_STEPS, SPR_CS, cy=0, cz=barrel_cz)

    # Dart partially inserted from front (nose sticking out)
    dart_x0 = BARREL_LEN - DART_H + 15   # dart mostly inside, nose sticking out
    m.solid_cyl_x(dart_x0, dart_x0 + DART_H, 0, barrel_cz, DART_R, SEGS)
    # Nose cone (pointing out the front)
    nose_tip_x = dart_x0 + DART_H + NOSE_H
    # cone along X: need to build as z-cone then rotate
    # Build as tube rings along X manually
    nose_base_x = dart_x0 + DART_H
    for k in range(1, NOSE_SEGS + 1):
        t0 = (k-1) / NOSE_SEGS
        t1 = k / NOSE_SEGS
        r0 = DART_R * (1 - t0)
        r1 = DART_R * (1 - t1)
        x0 = nose_base_x + t0 * NOSE_H
        x1 = nose_base_x + t1 * NOSE_H
        if r1 < 0.001:
            tip = (nose_tip_x, 0, barrel_cz)
            ring0 = m._pts_x(x0, 0, barrel_cz, r0, SEGS)
            for i in range(SEGS):
                j = (i+1) % SEGS
                m.tri(tip, ring0[i], ring0[j])
            break
        ring0 = m._pts_x(x0, 0, barrel_cz, r0, SEGS)
        ring1 = m._pts_x(x1, 0, barrel_cz, r1, SEGS)
        for i in range(SEGS):
            j = (i+1) % SEGS
            m.quad(ring0[i], ring0[j], ring1[j], ring1[i])

    m.floor_to_z0()
    return m


def build_print_plate():
    """All 3 parts on one flat plate, each at z=0, spaced apart."""
    GAP = 8.0

    # Cradle: prints flat. Centered at x = barrel_len/2, y=0
    cradle = build_cradle()
    # Cradle x footprint: roughly 0 to BARREL_LEN, y footprint ±(CRADLE_GAP/2 + CRADLE_PRONG_W)
    cradle_half_w = CRADLE_GAP/2 + CRADLE_PRONG_W

    # Barrel: prints upright, footprint = BARREL_OR radius circle
    barrel = build_barrel()
    barrel_x = BARREL_LEN/2   # center barrel over cradle x-center
    barrel_y = cradle_half_w + GAP + BARREL_OR
    barrel.translate(barrel_x, barrel_y)

    # Rocket: prints upright, footprint = DART_R radius
    rocket = build_rocket()
    rocket_x = BARREL_LEN/2
    rocket_y = barrel_y + BARREL_OR + GAP + DART_R
    rocket.translate(rocket_x, rocket_y)

    plate = Mesh()
    plate.merge(cradle)
    plate.merge(barrel)
    plate.merge(rocket)
    return plate


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("=== Horizontal Spring Rocket Launcher ===")
    print()
    print("Spring to buy: 8mm OD compression spring, ~22mm long")
    print('Search "8mm OD compression spring" ~$1')
    print()

    print("Building parts...")
    build_barrel().save_stl(os.path.join(OUT_DIR, "barrel.stl"))
    build_rocket().save_stl(os.path.join(OUT_DIR, "rocket.stl"))
    build_cradle().save_stl(os.path.join(OUT_DIR, "cradle.stl"))

    print()
    print("Building print plate (all 3 parts)...")
    build_print_plate().save_3mf(os.path.join(OUT_DIR, "rocket_launcher_plate.3mf"))

    print()
    print("Building assembly preview...")
    build_assembly().save_3mf(os.path.join(OUT_DIR, "rocket_launcher_assembly.3mf"))

    print()
    print("Done!")
    print()
    print("PRINT  -> rocket_launcher_plate.3mf  (all parts, one plate)")
    print("PREVIEW-> rocket_launcher_assembly.3mf (how it looks assembled)")
    print()
    print("How to launch:")
    print("  1. Put barrel in cradle (closed end = back)")
    print("  2. Drop spring in from the back (wraps around guide post)")
    print("  3. Insert rocket nose-first from the front")
    print("  4. Push rocket back to compress spring, release -> launches sideways!")
