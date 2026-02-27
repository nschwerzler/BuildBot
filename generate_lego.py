"""
LEGO 2x6 Hinge Brick Generator
================================
Functional 2x6 brick with:
  - 12 top studs
  - Side studs on front & back faces
  - Hinge PIN (male finger) on RIGHT end
  - Hinge FORK (female socket) on LEFT end
  - Anti-stud tubes underneath
  - Hollow interior

Two identical bricks chain together:
  Brick A's right PIN slides into Brick B's left FORK -> spins freely!

        +--------------+        +--------------+
  FORK =|  BRICK A     |= PIN --> FORK =|  BRICK B     |= PIN
        +--------------+        +--------------+
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
# Simple peg-and-socket hinge:
#   RIGHT end: two pegs sticking up from the top surface
#   LEFT end: two hollow sockets (tubes) that the pegs fit into
#   Brick A's pegs drop into Brick B's sockets -> spins!
PEG_R       = 1.5         # peg radius (3mm diameter)
PEG_H       = 6.0         # peg height above brick top
SOCK_OR     = 2.8         # socket outer radius
SOCK_IR     = 1.65        # socket inner radius (peg + 0.15mm clearance)
SOCK_H      = 6.0         # socket height

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

    def cyl_z(self, cx, cy, z0, r, l, segs=SEGS):
        """Cylinder along Z (for side studs & hinge pin)."""
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

    # ── 3. SIDE STUDS — 3 per face (every other column, cleaner look) ──
    for col in range(0, COLS, 2):
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
    #  6. HINGE PEGS (male) — RIGHT END, top surface
    # ==============================================================
    #  Two solid pegs sticking up from the rightmost stud positions.
    #  These drop into the sockets on another brick.
    #
    #       ┌──┐  ┌──┐
    #       │  │  │  │   <- pegs
    #   ════╧══╧══╧══╧═══  <- brick top
    #
    for row in range(ROWS):
        peg_x = PITCH/2 + (COLS - 1)*PITCH - TOL   # rightmost column
        peg_z = PITCH/2 + row*PITCH - TOL
        m.cyl_y(peg_x, BRICK_H + STUD_H, peg_z, PEG_R, PEG_H)

    # ==============================================================
    #  7. HINGE SOCKETS (female) — LEFT END, top surface
    # ==============================================================
    #  Two hollow tubes at the leftmost stud positions.
    #  Another brick's pegs drop in and spin freely.
    #
    #       ╔══╗  ╔══╗
    #       ║  ║  ║  ║   <- sockets (hollow)
    #   ════╩══╩══╩══╩═══  <- brick top
    #
    for row in range(ROWS):
        sock_x = PITCH/2 + 0*PITCH - TOL   # leftmost column
        sock_z = PITCH/2 + row*PITCH - TOL
        # Hollow tube: outer wall + inner hole
        m.tube_y(sock_x, BRICK_H + STUD_H, sock_z, SOCK_OR, SOCK_IR, SOCK_H)
        # Bottom cap (ring) to support the peg
        # The stud already provides a base, but add a ring floor
        # (stud is already there at this position from step 2)

    # ──────────────────────────────────────────────────────────────
    n_side = ((COLS+1)//2) * 2
    print(f"LEGO 2x{COLS} Hinge Brick:")
    print(f"  Body: {BODY_X:.1f} x {BRICK_H:.1f} x {BODY_Z:.1f} mm")
    print(f"  Top studs: {COLS * ROWS}")
    print(f"  Side studs: {n_side} (front + back)")
    print(f"  RIGHT = 2 Pegs (diam {PEG_R*2:.1f}mm, height {PEG_H:.0f}mm)")
    print(f"  LEFT  = 2 Sockets (OD {SOCK_OR*2:.1f}mm, ID {SOCK_IR*2:.1f}mm)")
    print(f"  Anti-stud tubes: {COLS - 1}")
    print(f"  Triangles: {len(m.tris)}")
    return m


if __name__ == "__main__":
    m = build_lego_2x6()
    m.save_stl("lego_2x6.stl")
    m.save_3mf("lego_2x6.3mf")
    print("\nDone! Pegs on right, sockets on left.")
    print("Print 2 — drop Brick A's pegs into Brick B's sockets to spin!")
