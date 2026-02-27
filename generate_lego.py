"""
LEGO 2x6 Hinge Brick Generator
================================
Functional 2x6 brick with:
  - 12 top studs
  - Side studs on ALL columns, front & back faces
  - Foldable peg arm on RIGHT wall  (single living hinge, folds up)
  - Foldable socket arm on LEFT wall (two living hinges, folds up + turns out)
  - Anti-stud tubes underneath
  - Hollow interior

Folded flat  = normal brick for walls (just studs visible).
Folded out   = connector!  Chain bricks side-by-side:

  <==SOCKET|--arm--| BRICK A |--arm--|PEG==>  <==SOCKET|--arm--| BRICK B ...
"""
import math
import os
import zipfile

# ── Brick dims (mm) ──
PITCH     = 8.0
COLS      = 6
ROWS      = 2
BRICK_H   = 9.6
STUD_D    = 4.8
STUD_H    = 1.7
SEGS      = 24
WALL      = 1.5
TOP_WALL  = 1.0
TUBE_OD   = 6.51
TUBE_ID   = 4.8
RIB_W     = 0.8
TOL       = 0.1

# ── Hinge dims ──
# Foldable living-hinge arms on side walls:
#   RIGHT wall: short arm + peg, SINGLE living hinge (folds up flat)
#   LEFT wall:  longer arm + socket, TWO living hinges (folds up + turns outward)
#   Folded flat = clean wall brick.  Fold out = connector!
PEG_R      = 1.5     # peg radius (3mm diam)
PEG_L      = 4.0     # peg length sticking out
SOCK_OR    = 2.8     # socket outer radius (5.6mm OD)
SOCK_IR    = 1.65    # socket inner radius (3.3mm ID, peg + clearance)
SOCK_L     = 4.0     # socket depth
LH_THICK   = 0.35    # living hinge thickness (thin enough to flex in PLA)
LH_SPAN    = 0.5     # living hinge span (gap between wall and arm)

# ── Derived ──
BODY_X = COLS * PITCH - TOL * 2
BODY_Z = ROWS * PITCH - TOL * 2


class Mesh:
    """Indexed triangle mesh with vertex dedup."""
    def __init__(self):
        self.verts = []
        self.tris = []
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
        self.tri(a, b, c); self.tri(a, c, d)

    def box(self, x0, y0, z0, x1, y1, z1):
        a,b,c,d = (x0,y0,z0),(x1,y0,z0),(x1,y0,z1),(x0,y0,z1)
        e,f,g,h = (x0,y1,z0),(x1,y1,z0),(x1,y1,z1),(x0,y1,z1)
        self.quad(d,c,b,a); self.quad(e,f,g,h)
        self.quad(a,b,f,e); self.quad(c,d,h,g)
        self.quad(a,e,h,d); self.quad(b,c,g,f)

    def cyl_y(self, cx, y0, cz, r, h, segs=SEGS):
        """Cylinder along Y (for top studs)."""
        bot, top = [], []
        for i in range(segs):
            a = 2*math.pi*i/segs
            px, pz = cx+r*math.cos(a), cz+r*math.sin(a)
            bot.append((px, y0, pz)); top.append((px, y0+h, pz))
        for i in range(segs):
            j = (i+1) % segs
            self.quad(bot[i], bot[j], top[j], top[i])
        ct = (cx, y0+h, cz)
        cb = (cx, y0, cz)
        for i in range(segs):
            j = (i+1) % segs
            self.tri(ct, top[i], top[j])
            self.tri(cb, bot[j], bot[i])

    def cyl_x(self, x0, cy, cz, r, l, segs=SEGS):
        """Cylinder along X (for hinge pegs)."""
        s, e = [], []
        for i in range(segs):
            a = 2*math.pi*i/segs
            py, pz = cy+r*math.cos(a), cz+r*math.sin(a)
            s.append((x0, py, pz)); e.append((x0+l, py, pz))
        for i in range(segs):
            j = (i+1) % segs
            self.quad(s[i], s[j], e[j], e[i])
        cs = (x0, cy, cz); ce = (x0+l, cy, cz)
        for i in range(segs):
            j = (i+1) % segs
            self.tri(ce, e[i], e[j])
            self.tri(cs, s[j], s[i])

    def cyl_z(self, cx, cy, z0, r, l, segs=SEGS):
        """Cylinder along Z (for side studs)."""
        s, e = [], []
        for i in range(segs):
            a = 2*math.pi*i/segs
            px, py = cx+r*math.cos(a), cy+r*math.sin(a)
            s.append((px, py, z0)); e.append((px, py, z0+l))
        for i in range(segs):
            j = (i+1) % segs
            self.quad(s[i], s[j], e[j], e[i])
        cs = (cx, cy, z0); ce = (cx, cy, z0+l)
        for i in range(segs):
            j = (i+1) % segs
            self.tri(ce, e[i], e[j])
            self.tri(cs, s[j], s[i])

    def tube_x(self, x0, cy, cz, ro, ri, l, segs=SEGS):
        """Hollow tube along X (for hinge sockets)."""
        os_, oe, is_, ie = [], [], [], []
        for i in range(segs):
            a = 2*math.pi*i/segs
            ca, sa = math.cos(a), math.sin(a)
            os_.append((x0, cy+ro*ca, cz+ro*sa))
            oe.append((x0+l, cy+ro*ca, cz+ro*sa))
            is_.append((x0, cy+ri*ca, cz+ri*sa))
            ie.append((x0+l, cy+ri*ca, cz+ri*sa))
        for i in range(segs):
            j = (i+1) % segs
            self.quad(os_[i], os_[j], oe[j], oe[i])
            self.quad(is_[j], is_[i], ie[i], ie[j])
            self.quad(oe[i], oe[j], ie[j], ie[i])
            self.quad(os_[j], os_[i], is_[i], is_[j])

    def tube_y(self, cx, y0, cz, ro, ri, h, segs=SEGS):
        """Hollow tube along Y (for anti-studs)."""
        ob, ot, ib, it = [], [], [], []
        for i in range(segs):
            a = 2*math.pi*i/segs
            ca, sa = math.cos(a), math.sin(a)
            ob.append((cx+ro*ca, y0, cz+ro*sa))
            ot.append((cx+ro*ca, y0+h, cz+ro*sa))
            ib.append((cx+ri*ca, y0, cz+ri*sa))
            it.append((cx+ri*ca, y0+h, cz+ri*sa))
        for i in range(segs):
            j = (i+1) % segs
            self.quad(ob[i], ob[j], ot[j], ot[i])
            self.quad(ib[j], ib[i], it[i], it[j])
            self.quad(ot[i], ot[j], it[j], it[i])
            self.quad(ob[j], ob[i], ib[i], ib[j])

    def _normal(self, ia, ib, ic):
        a, b, c = self.verts[ia], self.verts[ib], self.verts[ic]
        ux,uy,uz = b[0]-a[0], b[1]-a[1], b[2]-a[2]
        vx,vy,vz = c[0]-a[0], c[1]-a[1], c[2]-a[2]
        nx,ny,nz = uy*vz-uz*vy, uz*vx-ux*vz, ux*vy-uy*vx
        ln = math.sqrt(nx*nx+ny*ny+nz*nz)
        return (nx/ln, ny/ln, nz/ln) if ln > 1e-12 else (0,0,1)

    def save_stl(self, path):
        with open(path, 'w') as f:
            f.write("solid lego\n")
            for ia,ib,ic in self.tris:
                n = self._normal(ia,ib,ic)
                a,b,c = self.verts[ia], self.verts[ib], self.verts[ic]
                f.write(f"  facet normal {n[0]:.6e} {n[1]:.6e} {n[2]:.6e}\n")
                f.write("    outer loop\n")
                for p in (a,b,c):
                    f.write(f"      vertex {p[0]:.6e} {p[1]:.6e} {p[2]:.6e}\n")
                f.write("    endloop\n  endfacet\n")
            f.write("endsolid lego\n")
        print(f"  STL: {len(self.tris)} tris, {os.path.getsize(path)//1024} KB -> {path}")

    def save_3mf(self, path):
        vl = [f'          <vertex x="{x}" y="{y}" z="{z}"/>' for x,y,z in self.verts]
        tl = [f'          <triangle v1="{a}" v2="{b}" v3="{c}"/>' for a,b,c in self.tris]
        model = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<model unit="millimeter" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">\n'
            '  <metadata name="Application">LegoGen</metadata>\n'
            '  <resources>\n    <object id="1" type="model">\n      <mesh>\n'
            '        <vertices>\n'+'\n'.join(vl)+'\n        </vertices>\n'
            '        <triangles>\n'+'\n'.join(tl)+'\n        </triangles>\n'
            '      </mesh>\n    </object>\n  </resources>\n'
            '  <build>\n    <item objectid="1"/>\n  </build>\n</model>')
        ct = ('<?xml version="1.0" encoding="UTF-8"?>\n'
              '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
              '  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n'
              '  <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>\n'
              '</Types>')
        rels = ('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
                '  <Relationship Target="/3D/3dmodel.model" Id="rel0" '
                'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n'
                '</Relationships>')
        with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr('[Content_Types].xml', ct)
            zf.writestr('_rels/.rels', rels)
            zf.writestr('3D/3dmodel.model', model)
        print(f"  3MF: {len(self.tris)} tris, {os.path.getsize(path)//1024} KB -> {path}")


# ==================================================================
def build_lego_2x6():
    m = Mesh()
    cz = BODY_Z / 2       # center Z of brick
    cy = BRICK_H / 2      # center Y of brick
    sr = STUD_D / 2       # stud radius

    # ── 1. SHELL (5 box slabs forming hollow brick) ──
    m.box(0, BRICK_H - TOP_WALL, 0, BODY_X, BRICK_H, BODY_Z)        # top plate
    m.box(0, 0, 0, BODY_X, BRICK_H - TOP_WALL, WALL)                 # front wall
    m.box(0, 0, BODY_Z - WALL, BODY_X, BRICK_H - TOP_WALL, BODY_Z)  # back wall
    m.box(0, 0, WALL, WALL, BRICK_H - TOP_WALL, BODY_Z - WALL)      # left wall
    m.box(BODY_X-WALL, 0, WALL, BODY_X, BRICK_H-TOP_WALL, BODY_Z-WALL)  # right wall

    # ── 2. TOP STUDS (2x6 grid) ──
    for col in range(COLS):
        for row in range(ROWS):
            m.cyl_y(PITCH/2 + col*PITCH - TOL, BRICK_H,
                    PITCH/2 + row*PITCH - TOL, sr, STUD_H)

    # ── 3. SIDE STUDS — all columns on front & back faces ──
    for col in range(COLS):
        cx = PITCH/2 + col*PITCH - TOL
        m.cyl_z(cx, cy, -STUD_H, sr, STUD_H)           # front face
        m.cyl_z(cx, cy, BODY_Z, sr, STUD_H)             # back face

    # ── 4. ANTI-STUD TUBES (underneath) ──
    tro, tri_ = TUBE_OD/2, TUBE_ID/2
    th = BRICK_H - TOP_WALL
    for col in range(COLS - 1):
        m.tube_y(PITCH + col*PITCH - TOL, 0, cz, tro, tri_, th)

    # ── 5. RIBS ──
    for col in range(COLS):
        cx = PITCH/2 + col*PITCH - TOL
        m.box(cx-RIB_W/2, 0, WALL, cx+RIB_W/2, th*0.3, cz - tro)
        m.box(cx-RIB_W/2, 0, cz + tro, cx+RIB_W/2, th*0.3, BODY_Z - WALL)

    # ==============================================================
    #  6. FOLDABLE HINGE — RIGHT WALL (short peg arm)
    # ==============================================================
    #  Single arm with peg, connected by a living hinge.
    #  Living hinge is thin in Y -> arm folds UP flat against wall.
    #
    #     WALL |--hinge--| ARM |===PEG===>
    #
    arm_cy = BRICK_H / 2       # mid-height of brick
    arm_cz = BODY_Z / 2        # centered between the two rows

    # Living hinge bridge (thin in Y so it flexes up/down)
    m.box(BODY_X,            arm_cy - LH_THICK/2, arm_cz - 2.0,
          BODY_X + LH_SPAN,  arm_cy + LH_THICK/2, arm_cz + 2.0)

    # Arm plate (5mm × 5mm face, 2mm thick)
    pax0 = BODY_X + LH_SPAN
    pax1 = pax0 + 2.0
    par  = 2.5
    m.box(pax0, arm_cy - par, arm_cz - par,
          pax1, arm_cy + par, arm_cz + par)

    # Peg extending right from arm
    m.cyl_x(pax1, arm_cy, arm_cz, PEG_R, PEG_L)

    # ==============================================================
    #  7. FOLDABLE HINGE — LEFT WALL (socket arm, two-stage fold)
    # ==============================================================
    #  Longer arm with socket.  TWO living hinges:
    #    Hinge 1 (at wall): thin in Y -> folds arm UP against wall
    #    Hinge 2 (mid-arm): thin in Z -> turns socket OUTWARD
    #
    #  <===SOCKET=| ARM2 |--h2--| ARM1 |--h1--| WALL
    #
    # First living hinge (folds up, thin in Y, fold axis along Z)
    h1x0 = -LH_SPAN
    m.box(h1x0,  arm_cy - LH_THICK/2, arm_cz - 2.0,
          0,     arm_cy + LH_THICK/2, arm_cz + 2.0)

    # Arm segment 1 (bridge between the two hinges, 5mm × 5mm × 3mm)
    s1x0 = h1x0 - 3.0
    s1r  = 2.5
    m.box(s1x0, arm_cy - s1r, arm_cz - s1r,
          h1x0, arm_cy + s1r, arm_cz + s1r)

    # Second living hinge (turns outward, thin in Z, fold axis along Y)
    h2x0 = s1x0 - LH_SPAN
    m.box(h2x0,  arm_cy - 2.0, arm_cz - LH_THICK/2,
          s1x0,  arm_cy + 2.0, arm_cz + LH_THICK/2)

    # Arm segment 2 — socket mount (6mm × 6mm × 2.5mm)
    s2x0 = h2x0 - 2.5
    s2r  = 3.0
    m.box(s2x0, arm_cy - s2r, arm_cz - s2r,
          h2x0, arm_cy + s2r, arm_cz + s2r)

    # Socket tube opening to the left
    m.tube_x(s2x0 - SOCK_L, arm_cy, arm_cz, SOCK_OR, SOCK_IR, SOCK_L)

    # ──────────────────────────────────────────────────────────────
    n_side = COLS * 2
    print(f"LEGO 2x{COLS} Foldable-Hinge Brick:")
    print(f"  Body: {BODY_X:.1f} x {BRICK_H:.1f} x {BODY_Z:.1f} mm")
    print(f"  Top studs: {COLS * ROWS}")
    print(f"  Side studs: {n_side} (front + back, all columns)")
    print(f"  RIGHT = Foldable peg arm (diam {PEG_R*2:.1f}mm, {PEG_L:.0f}mm long)")
    print(f"  LEFT  = Foldable socket arm (OD {SOCK_OR*2:.1f}mm, ID {SOCK_IR*2:.1f}mm)")
    print(f"  Living hinges: {LH_THICK}mm thick (foldable)")
    print(f"  Anti-stud tubes: {COLS - 1}")
    print(f"  Triangles: {len(m.tris)}")
    return m


if __name__ == "__main__":
    m = build_lego_2x6()
    m.save_stl("lego_2x6.stl")
    m.save_3mf("lego_2x6.3mf")
    print("\nDone! Foldable hinge arms on both side walls.")
    print("Fold flat for plain wall brick, fold out to connect!")
    print("RIGHT arm: folds up (peg). LEFT arm: folds up + turns outward (socket).")
