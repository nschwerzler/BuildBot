"""
Mario ? Block — LEGO Compatible
=================================
8×8×8 stud cube (64mm × 64mm × 64mm) with:
  - 8×8 top studs
  - Anti-stud tubes underneath
  - Side studs on all 4 walls forming the "?" pattern
  - Hollow interior with walls
  - LEGO-compatible stud/anti-stud dimensions
"""
import math
import os
import zipfile

# ── LEGO Dimensions (mm) ──
PRINT_TOL = 0.1
PITCH     = 8.0          # Stud center-to-center
GRID      = 8            # 8×8×8 studs
CUBE_SIZE = GRID * PITCH # 64mm
STUD_D    = 4.8 - PRINT_TOL * 3  # Stud diameter (shrunk for FDM)
STUD_H    = 1.8          # Stud height
SEGS      = 32           # Cylinder smoothness
WALL      = 1.5          # Wall thickness
TOP_WALL  = 1.0          # Top plate thickness
TUBE_OD   = 6.51         # Anti-stud tube outer diameter
TUBE_ID   = 4.8 + PRINT_TOL  # Anti-stud tube inner diameter
TOL       = 0.1          # Body undersize per side

# Derived
BODY = CUBE_SIZE - TOL * 2  # Actual body size (63.8mm)
SR = STUD_D / 2              # Stud radius

# ── "?" Pattern on 8×8 grid (1 = stud, 0 = empty) ──
# Viewed from the front, row 0 = top
QUESTION_MARK = [
    [0, 0, 1, 1, 1, 1, 0, 0],
    [0, 1, 1, 0, 0, 1, 1, 0],
    [0, 1, 1, 0, 0, 1, 1, 0],
    [0, 0, 0, 0, 1, 1, 0, 0],
    [0, 0, 0, 1, 1, 0, 0, 0],
    [0, 0, 0, 1, 1, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 1, 1, 0, 0, 0],
]


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
        a, b, c, d = (x0,y0,z0),(x1,y0,z0),(x1,y0,z1),(x0,y0,z1)
        e, f, g, h = (x0,y1,z0),(x1,y1,z0),(x1,y1,z1),(x0,y1,z1)
        self.quad(d,c,b,a); self.quad(e,f,g,h)
        self.quad(a,b,f,e); self.quad(c,d,h,g)
        self.quad(a,e,h,d); self.quad(b,c,g,f)

    def cyl_y(self, cx, y0, cz, r, h, segs=SEGS):
        """Cylinder along Y (top studs)."""
        bot, top = [], []
        for i in range(segs):
            a = 2*math.pi*i/segs
            px, pz = cx+r*math.cos(a), cz+r*math.sin(a)
            bot.append((px, y0, pz)); top.append((px, y0+h, pz))
        for i in range(segs):
            j = (i+1) % segs
            self.quad(bot[i], bot[j], top[j], top[i])
        ct, cb = (cx, y0+h, cz), (cx, y0, cz)
        for i in range(segs):
            j = (i+1) % segs
            self.tri(ct, top[i], top[j])
            self.tri(cb, bot[j], bot[i])

    def cyl_z(self, cx, cy, z0, r, l, segs=SEGS):
        """Cylinder along Z (front/back wall studs)."""
        s, e = [], []
        for i in range(segs):
            a = 2*math.pi*i/segs
            px, py = cx+r*math.cos(a), cy+r*math.sin(a)
            s.append((px, py, z0)); e.append((px, py, z0+l))
        for i in range(segs):
            j = (i+1) % segs
            self.quad(s[i], s[j], e[j], e[i])
        cs, ce = (cx, cy, z0), (cx, cy, z0+l)
        for i in range(segs):
            j = (i+1) % segs
            self.tri(ce, e[i], e[j])
            self.tri(cs, s[j], s[i])

    def cyl_x(self, x0, cy, cz, r, l, segs=SEGS):
        """Cylinder along X (left/right wall studs)."""
        s, e = [], []
        for i in range(segs):
            a = 2*math.pi*i/segs
            py, pz = cy+r*math.cos(a), cz+r*math.sin(a)
            s.append((x0, py, pz)); e.append((x0+l, py, pz))
        for i in range(segs):
            j = (i+1) % segs
            self.quad(s[i], s[j], e[j], e[i])
        cs, ce = (x0, cy, cz), (x0+l, cy, cz)
        for i in range(segs):
            j = (i+1) % segs
            self.tri(ce, e[i], e[j])
            self.tri(cs, s[j], s[i])

    def tube_y(self, cx, y0, cz, ro, ri, h, segs=SEGS):
        """Hollow tube along Y (anti-studs)."""
        ob, ot, ib, it_ = [], [], [], []
        for i in range(segs):
            a = 2*math.pi*i/segs
            ca, sa = math.cos(a), math.sin(a)
            ob.append((cx+ro*ca, y0, cz+ro*sa))
            ot.append((cx+ro*ca, y0+h, cz+ro*sa))
            ib.append((cx+ri*ca, y0, cz+ri*sa))
            it_.append((cx+ri*ca, y0+h, cz+ri*sa))
        for i in range(segs):
            j = (i+1) % segs
            self.quad(ob[i], ob[j], ot[j], ot[i])
            self.quad(ib[j], ib[i], it_[i], it_[j])
            self.quad(ot[i], ot[j], it_[j], it_[i])
            self.quad(ob[j], ob[i], ib[i], ib[j])

    def _normal(self, ia, ib, ic):
        a, b, c = self.verts[ia], self.verts[ib], self.verts[ic]
        ux, uy, uz = b[0]-a[0], b[1]-a[1], b[2]-a[2]
        vx, vy, vz = c[0]-a[0], c[1]-a[1], c[2]-a[2]
        nx, ny, nz = uy*vz-uz*vy, uz*vx-ux*vz, ux*vy-uy*vx
        ln = math.sqrt(nx*nx+ny*ny+nz*nz)
        return (nx/ln, ny/ln, nz/ln) if ln > 1e-12 else (0, 0, 1)

    def save_stl(self, path):
        with open(path, 'w') as f:
            f.write("solid mario_block\n")
            for ia, ib, ic in self.tris:
                n = self._normal(ia, ib, ic)
                a, b, c = self.verts[ia], self.verts[ib], self.verts[ic]
                f.write(f"  facet normal {n[0]:.6e} {n[1]:.6e} {n[2]:.6e}\n")
                f.write("    outer loop\n")
                for p in (a, b, c):
                    f.write(f"      vertex {p[0]:.6e} {p[1]:.6e} {p[2]:.6e}\n")
                f.write("    endloop\n  endfacet\n")
            f.write("endsolid mario_block\n")
        print(f"  STL: {len(self.tris)} tris, {os.path.getsize(path)//1024} KB -> {path}")

    def save_3mf(self, path):
        vl = [f'          <vertex x="{x}" y="{y}" z="{z}"/>' for x, y, z in self.verts]
        tl = [f'          <triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in self.tris]
        model = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<model unit="millimeter" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">\n'
            '  <metadata name="Application">MarioBlockGen</metadata>\n'
            '  <resources>\n    <object id="1" type="model">\n      <mesh>\n'
            '        <vertices>\n' + '\n'.join(vl) + '\n        </vertices>\n'
            '        <triangles>\n' + '\n'.join(tl) + '\n        </triangles>\n'
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


def build_mario_block():
    m = Mesh()

    # ── 1. SHELL — hollow box (6 slabs: top, bottom, 4 walls) ──
    # Top plate
    m.box(0, BODY - TOP_WALL, 0, BODY, BODY, BODY)
    # Bottom plate
    m.box(0, 0, 0, BODY, TOP_WALL, BODY)
    # Front wall (Z=0 side)
    m.box(0, TOP_WALL, 0, BODY, BODY - TOP_WALL, WALL)
    # Back wall (Z=BODY side)
    m.box(0, TOP_WALL, BODY - WALL, BODY, BODY - TOP_WALL, BODY)
    # Left wall (X=0 side)
    m.box(0, TOP_WALL, WALL, WALL, BODY - TOP_WALL, BODY - WALL)
    # Right wall (X=BODY side)
    m.box(BODY - WALL, TOP_WALL, WALL, BODY, BODY - TOP_WALL, BODY - WALL)

    # ── 2. TOP STUDS — 8×8 grid ──
    for col in range(GRID):
        for row in range(GRID):
            cx = PITCH/2 + col * PITCH - TOL
            cz = PITCH/2 + row * PITCH - TOL
            m.cyl_y(cx, BODY, cz, SR, STUD_H)

    # ── 3. BOTTOM ANTI-STUD TUBES — 7×7 grid ──
    tro, tri_ = TUBE_OD / 2, TUBE_ID / 2
    for col in range(GRID - 1):
        for row in range(GRID - 1):
            cx = PITCH + col * PITCH - TOL
            cz = PITCH + row * PITCH - TOL
            m.tube_y(cx, TOP_WALL, cz, tro, tri_, BODY - TOP_WALL * 2)

    # ── 4. SIDE STUDS with "?" pattern on all 4 faces ──
    # Each side is 8 wide × 8 tall. Studs at grid positions.
    # Row 0 in QUESTION_MARK = top of the face.
    # Y coordinate: top of block is BODY, bottom is 0.
    # Side stud Y centers go from near-top to near-bottom.

    for row in range(GRID):
        for col in range(GRID):
            has_stud = QUESTION_MARK[row][col] == 1
            if not has_stud:
                continue

            # Y center for this row (row 0 = top)
            cy = BODY - PITCH/2 - row * PITCH + TOL
            
            # Front face (Z = 0, studs point -Z)
            sx = PITCH/2 + col * PITCH - TOL
            m.cyl_z(sx, cy, -STUD_H, SR, STUD_H)

            # Back face (Z = BODY, studs point +Z)
            # Mirror horizontally so ? reads correctly from outside
            sx_back = PITCH/2 + (GRID - 1 - col) * PITCH - TOL
            m.cyl_z(sx_back, cy, BODY, SR, STUD_H)

            # Left face (X = 0, studs point -X)
            sz = PITCH/2 + col * PITCH - TOL
            m.cyl_x(-STUD_H, cy, sz, SR, STUD_H)

            # Right face (X = BODY, studs point +X)
            # Mirror so ? reads correctly from outside
            sz_right = PITCH/2 + (GRID - 1 - col) * PITCH - TOL
            m.cyl_x(BODY, cy, sz_right, SR, STUD_H)

    # ── Summary ──
    side_studs = sum(sum(row) for row in QUESTION_MARK)
    print(f"Mario ? Block (8×8×8):")
    print(f"  Body: {BODY:.1f} × {BODY:.1f} × {BODY:.1f} mm")
    print(f"  Top studs: {GRID*GRID} (8×8)")
    print(f"  Anti-stud tubes: {(GRID-1)**2} (7×7)")
    print(f"  Side studs per face: {side_studs} (? pattern)")
    print(f"  Total side studs: {side_studs * 4} (4 faces)")
    print(f"  Triangles: {len(m.tris)}")
    return m


if __name__ == "__main__":
    m = build_mario_block()
    m.save_stl("mario_question_block.stl")
    m.save_3mf("mario_question_block.3mf")
    print("\nDone! Mario ? Block ready to print.")
    print("Paint yellow body + brown/dark ? studs for the classic look!")
