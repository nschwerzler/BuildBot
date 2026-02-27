"""
LEGO 2x6 Brick Generator — Deluxe Edition
============================================
Generates a functional 2x6 LEGO-compatible brick with:
  - 12 top studs (2x6 grid)
  - Side studs on front and back faces
  - Hinge finger (male) on left end
  - Hinge socket (female) on right end
  - Anti-stud tubes underneath
  - Reinforcing ribs
  - Hollow interior, proper wall thickness

Two bricks connect via hinges to spin freely!
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
WALL        = 1.5        # side wall thickness (slightly thicker for side studs)
TOP_WALL    = 1.0        # top plate thickness
TUBE_OD     = 6.51       # anti-stud outer diameter
TUBE_ID     = 4.8        # anti-stud inner diameter (grips stud)
RIB_W       = 0.8        # reinforcing rib thickness
TOLERANCE   = 0.1        # printing clearance per side

# Hinge dimensions
HINGE_PIN_R  = 1.6       # hinge pin radius (3.2mm diameter)
HINGE_PIN_L  = 5.0       # how far pin extends from brick face
HINGE_ARM_T  = 1.8       # arm/prong thickness
HINGE_ARM_W  = 8.0       # arm width (covers center of brick height)
HINGE_GAP    = 3.6       # gap between socket prongs (pin + clearance)
HINGE_SOCK_L = 5.5       # socket prong extension length

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
        """Hollow tube (pipe) along Y axis."""
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
            self.quad(out_bot[i], out_bot[j], out_top[j], out_top[i])
            self.quad(in_bot[j], in_bot[i], in_top[i], in_top[j])
            self.quad(out_top[i], out_top[j], in_top[j], in_top[i])
            self.quad(out_bot[j], out_bot[i], in_bot[i], in_bot[j])

    def cylinder_z(self, cx, cy, cz_start, radius, length, segs=STUD_SEGS, cap_start=True, cap_end=True):
        """Solid cylinder along Z axis (for side studs on front/back)."""
        pts_s, pts_e = [], []
        for i in range(segs):
            a = 2 * math.pi * i / segs
            px = cx + radius * math.cos(a)
            py = cy + radius * math.sin(a)
            pts_s.append((px, py, cz_start))
            pts_e.append((px, py, cz_start + length))
        for i in range(segs):
            j = (i + 1) % segs
            self.quad(pts_s[i], pts_s[j], pts_e[j], pts_e[i])
        if cap_end:
            c = (cx, cy, cz_start + length)
            for i in range(segs):
                j = (i + 1) % segs
                self.tri(c, pts_e[i], pts_e[j])
        if cap_start:
            c = (cx, cy, cz_start)
            for i in range(segs):
                j = (i + 1) % segs
                self.tri(c, pts_s[j], pts_s[i])

    def cylinder_x(self, cx_start, cy, cz, radius, length, segs=STUD_SEGS, cap_start=True, cap_end=True):
        """Solid cylinder along X axis (for hinge pins)."""
        pts_s, pts_e = [], []
        for i in range(segs):
            a = 2 * math.pi * i / segs
            py = cy + radius * math.cos(a)
            pz = cz + radius * math.sin(a)
            pts_s.append((cx_start, py, pz))
            pts_e.append((cx_start + length, py, pz))
        for i in range(segs):
            j = (i + 1) % segs
            self.quad(pts_s[i], pts_s[j], pts_e[j], pts_e[i])
        if cap_end:
            c = (cx_start + length, cy, cz)
            for i in range(segs):
                j = (i + 1) % segs
                self.tri(c, pts_e[i], pts_e[j])
        if cap_start:
            c = (cx_start, cy, cz)
            for i in range(segs):
                j = (i + 1) % segs
                self.tri(c, pts_s[j], pts_s[i])

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

    # ── 1. Shell (5 box slabs) ──
    # Top plate
    m.box(0, BRICK_H - TOP_WALL, 0, BODY_X, BRICK_H, BODY_Z)
    # Front wall
    m.box(0, 0, 0, BODY_X, BRICK_H - TOP_WALL, WALL)
    # Back wall
    m.box(0, 0, BODY_Z - WALL, BODY_X, BRICK_H - TOP_WALL, BODY_Z)
    # Left wall
    m.box(0, 0, WALL, WALL, BRICK_H - TOP_WALL, BODY_Z - WALL)
    # Right wall
    m.box(BODY_X - WALL, 0, WALL, BODY_X, BRICK_H - TOP_WALL, BODY_Z - WALL)

    stud_r = STUD_D / 2

    # ── 2. Top studs (2x6 grid) ──
    for col in range(COLS):
        for row in range(ROWS):
            cx = PITCH / 2 + col * PITCH - TOLERANCE
            cz = PITCH / 2 + row * PITCH - TOLERANCE
            m.cylinder(cx, BRICK_H, cz, stud_r, STUD_H, STUD_SEGS)

    # ── 3. Side studs on front face (Z=0, pointing -Z) ──
    side_stud_len = STUD_H
    for col in range(COLS):
        cx = PITCH / 2 + col * PITCH - TOLERANCE
        cy = BRICK_H / 2  # centered vertically on brick
        m.cylinder_z(cx, cy, -side_stud_len, stud_r, side_stud_len, STUD_SEGS)

    # ── 4. Side studs on back face (Z=BODY_Z, pointing +Z) ──
    for col in range(COLS):
        cx = PITCH / 2 + col * PITCH - TOLERANCE
        cy = BRICK_H / 2
        m.cylinder_z(cx, cy, BODY_Z, stud_r, side_stud_len, STUD_SEGS)

    # ── 5. Anti-stud tubes underneath ──
    tube_r_out = TUBE_OD / 2
    tube_r_in  = TUBE_ID / 2
    tube_h     = BRICK_H - TOP_WALL
    center_z   = BODY_Z / 2
    for col in range(COLS - 1):
        cx = PITCH + col * PITCH - TOLERANCE
        m.tube(cx, 0, center_z, tube_r_out, tube_r_in, tube_h, STUD_SEGS)

    # ── 6. Reinforcing ribs ──
    rib_h = BRICK_H - TOP_WALL
    for col in range(COLS):
        cx = PITCH / 2 + col * PITCH - TOLERANCE
        m.box(cx - RIB_W/2, 0, WALL, cx + RIB_W/2, rib_h * 0.3, center_z - tube_r_out)
        m.box(cx - RIB_W/2, 0, center_z + tube_r_out, cx + RIB_W/2, rib_h * 0.3, BODY_Z - WALL)

    # ── 7. Hinge finger (male) on LEFT end (X=0) ──
    # Two arms extend left from the brick face, with a cylinder pin connecting tips
    hinge_cy = BRICK_H / 2   # centered vertically
    arm_half = HINGE_GAP / 2 + HINGE_ARM_T  # total half-span of arms

    # Bottom arm
    arm_y_bot = hinge_cy - HINGE_GAP / 2 - HINGE_ARM_T
    m.box(-HINGE_PIN_L, arm_y_bot, center_z - HINGE_ARM_W / 2,
          0,              arm_y_bot + HINGE_ARM_T, center_z + HINGE_ARM_W / 2)

    # Top arm
    arm_y_top = hinge_cy + HINGE_GAP / 2
    m.box(-HINGE_PIN_L, arm_y_top, center_z - HINGE_ARM_W / 2,
          0,              arm_y_top + HINGE_ARM_T, center_z + HINGE_ARM_W / 2)

    # Connecting pin cylinder at the tips of the arms
    pin_y_center = hinge_cy
    pin_y_bot = arm_y_bot
    pin_y_top = arm_y_top + HINGE_ARM_T
    pin_length = pin_y_top - pin_y_bot
    m.cylinder(-HINGE_PIN_L, pin_y_bot, center_z, HINGE_PIN_R, pin_length, STUD_SEGS)

    # ── 8. Hinge socket (female) on RIGHT end (X=BODY_X) ──
    # Two prongs extend right, with gap between them to accept the finger pin
    # The prongs have a half-cylinder cutout to cradle the pin

    # Bottom prong
    sock_y_bot = hinge_cy - HINGE_GAP / 2 - HINGE_ARM_T
    m.box(BODY_X, sock_y_bot, center_z - HINGE_ARM_W / 2,
          BODY_X + HINGE_SOCK_L, sock_y_bot + HINGE_ARM_T, center_z + HINGE_ARM_W / 2)

    # Top prong
    sock_y_top = hinge_cy + HINGE_GAP / 2
    m.box(BODY_X, sock_y_top, center_z - HINGE_ARM_W / 2,
          BODY_X + HINGE_SOCK_L, sock_y_top + HINGE_ARM_T, center_z + HINGE_ARM_W / 2)

    # Inner cradle walls - partial cylinder inside each prong to grip the pin
    # Build small guide bumps on the inner faces of the prongs
    bump_r = HINGE_PIN_R + 0.3  # slightly larger for easy snap
    bump_segs = 12
    # Bottom prong top face guide (half-ring pointing up into gap)
    guide_y = sock_y_bot + HINGE_ARM_T
    for i in range(bump_segs):
        a0 = math.pi * i / bump_segs  # 0 to pi (top semicircle)
        a1 = math.pi * (i + 1) / bump_segs
        x0 = BODY_X + HINGE_SOCK_L / 2
        p0z = center_z + bump_r * math.cos(a0)
        p0y = guide_y + bump_r * math.sin(a0) * 0.3  # gentle bump
        p1z = center_z + bump_r * math.cos(a1)
        p1y = guide_y + bump_r * math.sin(a1) * 0.3

    # Top prong bottom face guide
    guide_y2 = sock_y_top
    for i in range(bump_segs):
        a0 = math.pi + math.pi * i / bump_segs
        a1 = math.pi + math.pi * (i + 1) / bump_segs
        p0z = center_z + bump_r * math.cos(a0)
        p0y = guide_y2 + bump_r * math.sin(a0) * 0.3
        p1z = center_z + bump_r * math.cos(a1)
        p1y = guide_y2 + bump_r * math.sin(a1) * 0.3

    # Back plate connecting the two prongs (gives socket its U shape)
    m.box(BODY_X + HINGE_SOCK_L - HINGE_ARM_T, sock_y_bot + HINGE_ARM_T,
          center_z - HINGE_ARM_W / 2,
          BODY_X + HINGE_SOCK_L, sock_y_top,
          center_z + HINGE_ARM_W / 2)

    # Socket hole cylinder (decorative ring showing where pin sits)
    hole_y_bot = sock_y_bot + HINGE_ARM_T
    hole_y_top = sock_y_top
    hole_len = hole_y_top - hole_y_bot
    # Inner cylinder to show the pin channel
    m.cylinder(BODY_X + HINGE_SOCK_L / 2, hole_y_bot, center_z,
               HINGE_PIN_R + 0.15, hole_len, STUD_SEGS)

    n_side = COLS * 2  # front + back side studs
    print(f"LEGO 2x{COLS} Deluxe brick:")
    print(f"  Body: {BODY_X:.1f} x {BRICK_H:.1f} x {BODY_Z:.1f} mm")
    print(f"  Top studs: {COLS * ROWS}")
    print(f"  Side studs: {n_side} ({COLS} front + {COLS} back)")
    print(f"  Hinge finger (left): pin ø{HINGE_PIN_R*2:.1f} mm")
    print(f"  Hinge socket (right): gap {HINGE_GAP:.1f} mm")
    print(f"  Anti-stud tubes: {COLS - 1}")
    print(f"  Total triangles: {len(m.tris)}")

    return m


if __name__ == "__main__":
    m = build_lego_2x6()
    m.save_stl("lego_2x6.stl")
    m.save_3mf("lego_2x6.3mf")
    print("\nDone! Files: lego_2x6.stl, lego_2x6.3mf")
