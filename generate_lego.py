"""
LEGO 2x6 Brick Generator
==========================
Generates a realistic, functional 2x6 LEGO-compatible brick
with proper interlocking geometry for 3D printing.

Features:
  - 12 cylindrical studs on top (2x6 grid)
  - Hollow interior with proper wall thickness
  - 5 bottom anti-stud tubes for snap-fit connection
  - Reinforcing ribs along bottom edges
  - Accurate LEGO-compatible dimensions
  - Slight printing tolerances built in

Standard LEGO dimensions used:
  - Pitch: 8.0 mm (stud center-to-center)
  - Brick height (body): 9.6 mm
  - Stud diameter: 4.8 mm, height: 1.8 mm
  - Wall thickness: 1.2 mm (sides), 1.0 mm (top)
  - Anti-stud tube OD: 6.51 mm
  - Anti-stud tube ID: 4.8 mm (grips stud)
"""
import math
import os
import zipfile

# ── LEGO dimensions (mm) ──
PITCH       = 8.0       # stud center spacing
COLS        = 6          # studs along X
ROWS        = 2          # studs along Z
BRICK_H     = 9.6        # body height (without stud)
STUD_D      = 4.8        # stud diameter
STUD_H      = 1.7        # stud height
STUD_SEGS   = 24         # segments per cylinder
WALL        = 1.2        # side wall thickness
TOP_WALL    = 1.0        # top plate thickness
TUBE_OD     = 6.51       # anti-stud outer diameter
TUBE_ID     = 4.8        # anti-stud inner diameter (grips stud)
RIB_W       = 0.8        # reinforcing rib thickness
TOLERANCE   = 0.1        # printing clearance per side

# Derived
BODY_X = COLS * PITCH - TOLERANCE * 2   # 47.8
BODY_Z = ROWS * PITCH - TOLERANCE * 2   # 15.8


class Mesh:
    """Indexed triangle mesh with vertex deduplication."""
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
        """Two triangles forming a quad (a-b-c-d in order)."""
        self.tri(a, b, c)
        self.tri(a, c, d)

    def box(self, x0, y0, z0, x1, y1, z1):
        """Axis-aligned solid box."""
        a = (x0, y0, z0); b = (x1, y0, z0)
        c = (x1, y0, z1); d = (x0, y0, z1)
        e = (x0, y1, z0); f = (x1, y1, z0)
        g = (x1, y1, z1); h = (x0, y1, z1)
        self.quad(d, c, b, a)  # bottom
        self.quad(e, f, g, h)  # top
        self.quad(a, b, f, e)  # front
        self.quad(c, d, h, g)  # back
        self.quad(a, e, h, d)  # left
        self.quad(b, c, g, f)  # right

    def cylinder(self, cx, cy_bot, cz, radius, height, segs=STUD_SEGS, cap_top=True, cap_bot=True):
        """Solid cylinder along Y axis."""
        pts_bot = []
        pts_top = []
        for i in range(segs):
            a = 2 * math.pi * i / segs
            px = cx + radius * math.cos(a)
            pz = cz + radius * math.sin(a)
            pts_bot.append((px, cy_bot, pz))
            pts_top.append((px, cy_bot + height, pz))
        # Side quads
        for i in range(segs):
            j = (i + 1) % segs
            self.quad(pts_bot[i], pts_bot[j], pts_top[j], pts_top[i])
        # Top cap (fan)
        if cap_top:
            center_top = (cx, cy_bot + height, cz)
            for i in range(segs):
                j = (i + 1) % segs
                self.tri(center_top, pts_top[i], pts_top[j])
        # Bottom cap (fan)
        if cap_bot:
            center_bot = (cx, cy_bot, cz)
            for i in range(segs):
                j = (i + 1) % segs
                self.tri(center_bot, pts_bot[j], pts_bot[i])

    def tube(self, cx, cy_bot, cz, r_outer, r_inner, height, segs=STUD_SEGS):
        """Hollow tube (pipe) along Y axis - open top and bottom."""
        out_bot, out_top, in_bot, in_top = [], [], [], []
        for i in range(segs):
            a = 2 * math.pi * i / segs
            cos_a = math.cos(a)
            sin_a = math.sin(a)
            out_bot.append((cx + r_outer * cos_a, cy_bot, cz + r_outer * sin_a))
            out_top.append((cx + r_outer * cos_a, cy_bot + height, cz + r_outer * sin_a))
            in_bot.append((cx + r_inner * cos_a, cy_bot, cz + r_inner * sin_a))
            in_top.append((cx + r_inner * cos_a, cy_bot + height, cz + r_inner * sin_a))
        for i in range(segs):
            j = (i + 1) % segs
            # Outer wall
            self.quad(out_bot[i], out_bot[j], out_top[j], out_top[i])
            # Inner wall (reversed winding)
            self.quad(in_bot[j], in_bot[i], in_top[i], in_top[j])
            # Top ring
            self.quad(out_top[i], out_top[j], in_top[j], in_top[i])
            # Bottom ring
            self.quad(out_bot[j], out_bot[i], in_bot[i], in_bot[j])

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
        with open(path, 'w') as f:
            f.write("solid lego\n")
            for ia, ib, ic in self.tris:
                n = self._normal(ia, ib, ic)
                a, b, c = self.verts[ia], self.verts[ib], self.verts[ic]
                f.write(f"  facet normal {n[0]:.6e} {n[1]:.6e} {n[2]:.6e}\n")
                f.write("    outer loop\n")
                f.write(f"      vertex {a[0]:.6e} {a[1]:.6e} {a[2]:.6e}\n")
                f.write(f"      vertex {b[0]:.6e} {b[1]:.6e} {b[2]:.6e}\n")
                f.write(f"      vertex {c[0]:.6e} {c[1]:.6e} {c[2]:.6e}\n")
                f.write("    endloop\n  endfacet\n")
            f.write("endsolid lego\n")
        kb = os.path.getsize(path) // 1024
        print(f"  STL: {len(self.tris)} tris, {kb} KB -> {path}")

    def save_3mf(self, path):
        vlines = [f'          <vertex x="{x}" y="{y}" z="{z}"/>'
                  for x, y, z in self.verts]
        tlines = [f'          <triangle v1="{a}" v2="{b}" v3="{c}"/>'
                  for a, b, c in self.tris]
        model_xml = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<model unit="millimeter" '
            'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">\n'
            '  <metadata name="Application">LegoGen</metadata>\n'
            '  <resources>\n'
            '    <object id="1" type="model">\n'
            '      <mesh>\n'
            '        <vertices>\n' + '\n'.join(vlines) + '\n'
            '        </vertices>\n'
            '        <triangles>\n' + '\n'.join(tlines) + '\n'
            '        </triangles>\n'
            '      </mesh>\n'
            '    </object>\n'
            '  </resources>\n'
            '  <build>\n'
            '    <item objectid="1"/>\n'
            '  </build>\n'
            '</model>'
        )
        content_types = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
            '  <Default Extension="rels" ContentType='
            '"application/vnd.openxmlformats-package.relationships+xml"/>\n'
            '  <Default Extension="model" ContentType='
            '"application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>\n'
            '</Types>'
        )
        rels = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<Relationships xmlns='
            '"http://schemas.openxmlformats.org/package/2006/relationships">\n'
            '  <Relationship Target="/3D/3dmodel.model" Id="rel0" '
            'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n'
            '</Relationships>'
        )
        with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr('[Content_Types].xml', content_types)
            zf.writestr('_rels/.rels', rels)
            zf.writestr('3D/3dmodel.model', model_xml)
        kb = os.path.getsize(path) // 1024
        print(f"  3MF: {len(self.tris)} tris, {kb} KB -> {path}")


# ── Build the brick ──────────────────────────────────────────────

def build_lego_2x6():
    m = Mesh()

    # Origin at bottom-left corner of brick, Y-up
    # Body outer box: 0..BODY_X in X, 0..BRICK_H in Y, 0..BODY_Z in Z

    # ── 1. Outer shell (hollow box) ──
    # We build it as: outer box minus inner cavity

    # Outer walls
    ox0, oy0, oz0 = 0, 0, 0
    ox1, oy1, oz1 = BODY_X, BRICK_H, BODY_Z

    # Inner cavity (cut out from bottom, leaving top plate and side walls)
    ix0 = WALL
    iz0 = WALL
    ix1 = BODY_X - WALL
    iz1 = BODY_Z - WALL
    iy0 = 0              # open bottom
    iy1 = BRICK_H - TOP_WALL  # stop below top plate

    # ── Build outer shell as 5 faces (no bottom face - it's open) ──
    # Top face (outer)
    m.quad((ox0, oy1, oz0), (ox1, oy1, oz0), (ox1, oy1, oz1), (ox0, oy1, oz1))
    # Front face (Z=0)
    m.quad((ox0, oy0, oz0), (ox1, oy0, oz0), (ox1, oy1, oz0), (ox0, oy1, oz0))
    # Back face (Z=BODY_Z)
    m.quad((ox1, oy0, oz1), (ox0, oy0, oz1), (ox0, oy1, oz1), (ox1, oy1, oz1))
    # Left face (X=0)
    m.quad((ox0, oy0, oz1), (ox0, oy0, oz0), (ox0, oy1, oz0), (ox0, oy1, oz1))
    # Right face (X=BODY_X)
    m.quad((ox1, oy0, oz0), (ox1, oy0, oz1), (ox1, oy1, oz1), (ox1, oy1, oz0))

    # ── Inner cavity walls ──
    # Inner top face (ceiling of cavity, underside of top plate)
    m.quad((ix1, iy1, iz0), (ix0, iy1, iz0), (ix0, iy1, iz1), (ix1, iy1, iz1))
    # Inner front wall
    m.quad((ix1, iy0, iz0), (ix0, iy0, iz0), (ix0, iy1, iz0), (ix1, iy1, iz0))
    # Inner back wall
    m.quad((ix0, iy0, iz1), (ix1, iy0, iz1), (ix1, iy1, iz1), (ix0, iy1, iz1))
    # Inner left wall
    m.quad((ix0, iy0, iz0), (ix0, iy0, iz1), (ix0, iy1, iz1), (ix0, iy1, iz0))
    # Inner right wall
    m.quad((ix1, iy0, iz1), (ix1, iy0, iz0), (ix1, iy1, iz0), (ix1, iy1, iz1))

    # ── Bottom rim (connects outer wall bottom edge to inner wall bottom edge) ──
    # Front rim
    m.quad((ox0, oy0, oz0), (ox1, oy0, oz0), (ix1, iy0, iz0), (ix0, iy0, iz0))
    # Back rim
    m.quad((ox1, oy0, oz1), (ox0, oy0, oz1), (ix0, iy0, iz1), (ix1, iy0, iz1))
    # Left rim
    m.quad((ox0, oy0, oz1), (ox0, oy0, oz0), (ix0, iy0, iz0), (ix0, iy0, iz1))
    # Right rim
    m.quad((ox1, oy0, oz0), (ox1, oy0, oz1), (ix1, iy0, iz1), (ix1, iy0, iz0))

    # ── Top ledge (connects outer top to inner cavity ceiling) ──
    # The top plate thickness = TOP_WALL. Outer top is at BRICK_H, inner ceiling at BRICK_H - TOP_WALL.
    # These ledges fill the step between outer top surface edge and inner cavity ceiling edge.
    # Front ledge
    m.quad((ix0, iy1, iz0), (ix1, iy1, iz0), (ox1, oy1, oz0), (ox0, oy1, oz0))
    # Back ledge
    m.quad((ix1, iy1, iz1), (ix0, iy1, iz1), (ox0, oy1, oz1), (ox1, oy1, oz1))
    # Left ledge
    m.quad((ix0, iy1, iz1), (ix0, iy1, iz0), (ox0, oy1, oz0), (ox0, oy1, oz1))
    # Right ledge
    m.quad((ix1, iy1, iz0), (ix1, iy1, iz1), (ox1, oy1, oz1), (ox1, oy1, oz0))

    # Wait — this approach makes overlapping geometry. Let me simplify.
    # The top plate outer surface is at oy1 for both outer and inner.
    # The inner cavity ceiling face IS already the underside of the top plate.
    # The above "ledge" quads are actually at the same Y height, so they'd be degenerate.
    # Actually no: outer top = oy1 = BRICK_H, inner ceiling = iy1 = BRICK_H - TOP_WALL
    # So the top surface is correct as outer, and the cavity ceiling is correct as inner.
    # The "ledge" would be where the inner wall extends up higher than the cavity —
    # but actually the inner walls go from iy0 to iy1, and the outer walls go to oy1.
    # The gap between iy1 and oy1 is the top plate itself, which is solid.
    # The outer top face and inner ceiling face handle this correctly since the
    # side walls (both outer and inner) already span to their respective heights.
    # We just need to make sure the inner side walls connect properly.

    # Actually, there's a gap: the outer side walls go from y=0 to y=BRICK_H,
    # but the inner side walls only go to y=BRICK_H-TOP_WALL.
    # That creates an unclosed gap at the top of the inner walls.
    # The "ledge" IS needed — it connects the top edge of each inner wall to the
    # underside perimeter of the outer top face. But they're at different Y values!

    # Let me reconsider. Actually the top surface of the outer box is a full rectangle
    # at y=BRICK_H. The inner cavity ceiling is a smaller rectangle at y=iy1.
    # To close the mesh between the outer top (big rect at BRICK_H) and inner ceiling
    # (small rect at iy1), we need the top plate to be properly represented.

    # Simplest approach: just remove the problematic "ledge" quads above and
    # re-do the outer top face as a frame (outer rect minus inner rect) at BRICK_H,
    # plus the inner ceiling at iy1, plus 4 connecting strips on the sides.

    # Actually, my current approach IS correct:
    # - Outer 5 faces (top + 4 sides) form the exterior  
    # - Inner 5 faces (ceiling + 4 sides) form the cavity
    # - Bottom rim connects outer and inner bottom edges
    # The mesh is closed everywhere. The "ledge" quads above are wrong/redundant
    # since the outer top and inner ceiling are at different Y levels but the 
    # side walls already bridge between them properly.
    
    # Let me just remove the ledge quads. The mesh closes via:
    # outer side wall (y=0 to BRICK_H) + inner side wall (y=0 to iy1)
    # + outer top (y=BRICK_H) + inner ceiling (y=iy1) + bottom rim
    # Wait, there's still a gap at the top! The outer side at top has edge at y=BRICK_H,
    # but the inner side at top has edge at y=iy1 < BRICK_H. 
    # The outer top face's inner edge is at (ix, BRICK_H, iz) but no geometry connects
    # from there down to (ix, iy1, iz).

    # OK I need to just rebuild this properly. Let me use a clean approach.

    # Clear and restart
    m = Mesh()

    # I'll build the shell as individual box walls to ensure proper closure.
    # Think of it as 5 rectangular slabs:
    #   - Top plate: full XZ area, thickness TOP_WALL
    #   - Front wall: full XY area, thickness WALL  
    #   - Back wall: full XY area, thickness WALL
    #   - Left wall: shortened Z (between front/back walls), full Y, thickness WALL
    #   - Right wall: same

    # Top plate
    m.box(0, BRICK_H - TOP_WALL, 0, BODY_X, BRICK_H, BODY_Z)

    # Front wall (Z near side, full width, from bottom to top plate underside)
    m.box(0, 0, 0, BODY_X, BRICK_H - TOP_WALL, WALL)

    # Back wall
    m.box(0, 0, BODY_Z - WALL, BODY_X, BRICK_H - TOP_WALL, BODY_Z)

    # Left wall (between front and back walls in Z)
    m.box(0, 0, WALL, WALL, BRICK_H - TOP_WALL, BODY_Z - WALL)

    # Right wall
    m.box(BODY_X - WALL, 0, WALL, BODY_X, BRICK_H - TOP_WALL, BODY_Z - WALL)

    # ── 2. Studs on top ──
    stud_r = STUD_D / 2
    for col in range(COLS):
        for row in range(ROWS):
            cx = PITCH / 2 + col * PITCH - TOLERANCE
            cz = PITCH / 2 + row * PITCH - TOLERANCE
            m.cylinder(cx, BRICK_H, cz, stud_r, STUD_H, STUD_SEGS)

    # ── 3. Anti-stud tubes (bottom, between stud positions) ──
    # For a 2×N brick, tubes go along the center line (between the 2 rows)
    # at positions between each column pair
    tube_r_out = TUBE_OD / 2
    tube_r_in  = TUBE_ID / 2
    tube_h     = BRICK_H - TOP_WALL  # from bottom to underside of top plate
    center_z   = BODY_Z / 2
    for col in range(COLS - 1):
        cx = PITCH + col * PITCH - TOLERANCE  # halfway between col and col+1
        m.tube(cx, 0, center_z, tube_r_out, tube_r_in, tube_h, STUD_SEGS)

    # ── 4. Reinforcing ribs along the bottom ──
    # Small ribs on the inside of front and back walls for strength
    rib_h = BRICK_H - TOP_WALL  # full interior height
    # Ribs under each stud column along front wall
    for col in range(COLS):
        cx = PITCH / 2 + col * PITCH - TOLERANCE
        # Front rib
        m.box(cx - RIB_W/2, 0, WALL, cx + RIB_W/2, rib_h * 0.3, center_z - tube_r_out)
        # Back rib
        m.box(cx - RIB_W/2, 0, center_z + tube_r_out, cx + RIB_W/2, rib_h * 0.3, BODY_Z - WALL)

    print(f"LEGO 2x{COLS} brick:")
    print(f"  Body: {BODY_X:.1f} x {BRICK_H:.1f} x {BODY_Z:.1f} mm")
    print(f"  Studs: {COLS * ROWS} ({ROWS}x{COLS}), ø{STUD_D} x {STUD_H} mm")
    print(f"  Anti-stud tubes: {COLS - 1}, OD {TUBE_OD} / ID {TUBE_ID} mm")
    print(f"  Total triangles: {len(m.tris)}")

    return m


if __name__ == "__main__":
    m = build_lego_2x6()
    m.save_stl("lego_2x6.stl")
    m.save_3mf("lego_2x6.3mf")
    print("\nDone! Files: lego_2x6.stl, lego_2x6.3mf")
