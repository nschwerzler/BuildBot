"""
Gauntlet Generator v5 — Sci-Fi Tech Armor
══════════════════════════════════════════
A proper sci-fi gauntlet that wraps around the forearm/hand.

Design:
  - Half-pipe shell wrapping around the arm (opens at palm side)
  - Surface ridges and raised spine for sci-fi tech look
  - Flared wrist cuff with lip/rim
  - Raised angular knuckle guard
  - Segmented finger armor plates (not tubes)
  - Thumb guard plate
  - Open palm for grip

Outputs:
  gauntlet.stl  — Universal STL
  gauntlet.3mf  — Bambu Studio project (tree supports auto-enabled)
"""
import math
import os
import zipfile

OUTPUT_STL = "gauntlet.stl"
OUTPUT_3MF = "gauntlet.3mf"


# ═══════════════════════════════════════════════════════════
# MESH CLASS
# ═══════════════════════════════════════════════════════════
class Mesh:
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
        self.tri(a, b, c)
        self.tri(a, c, d)

    def _normal(self, ia, ib, ic):
        a, b, c = self.verts[ia], self.verts[ib], self.verts[ic]
        ux, uy, uz = b[0]-a[0], b[1]-a[1], b[2]-a[2]
        vx, vy, vz = c[0]-a[0], c[1]-a[1], c[2]-a[2]
        nx = uy*vz - uz*vy
        ny = uz*vx - ux*vz
        nz = ux*vy - uy*vx
        ln = math.sqrt(nx*nx + ny*ny + nz*nz)
        if ln > 1e-12:
            return (nx/ln, ny/ln, nz/ln)
        return (0.0, 0.0, 1.0)

    def save_stl(self, path):
        with open(path, 'w') as f:
            f.write("solid gauntlet\n")
            for ia, ib, ic in self.tris:
                n = self._normal(ia, ib, ic)
                a = self.verts[ia]
                b = self.verts[ib]
                c = self.verts[ic]
                f.write(f"  facet normal {n[0]:.6e} {n[1]:.6e} {n[2]:.6e}\n")
                f.write("    outer loop\n")
                f.write(f"      vertex {a[0]:.6e} {a[1]:.6e} {a[2]:.6e}\n")
                f.write(f"      vertex {b[0]:.6e} {b[1]:.6e} {b[2]:.6e}\n")
                f.write(f"      vertex {c[0]:.6e} {c[1]:.6e} {c[2]:.6e}\n")
                f.write("    endloop\n  endfacet\n")
            f.write("endsolid gauntlet\n")
        print(f"  STL: {len(self.tris)} tris → {path}")

    def save_3mf(self, path):
        vlines = []
        for x, y, z in self.verts:
            vlines.append(f'          <vertex x="{x}" y="{y}" z="{z}"/>')
        tlines = []
        for a, b, c in self.tris:
            tlines.append(f'          <triangle v1="{a}" v2="{b}" v3="{c}"/>')

        model_xml = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<model unit="millimeter" '
            'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">\n'
            '  <metadata name="Application">GauntletGen</metadata>\n'
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

        slicer_cfg = (
            '; Gauntlet — tree supports\n'
            'enable_support = 1\n'
            'support_type = tree(auto)\n'
            'support_on_build_plate_only = 0\n'
            'support_threshold_angle = 30\n'
        )

        with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr('[Content_Types].xml', content_types)
            zf.writestr('_rels/.rels', rels)
            zf.writestr('3D/3dmodel.model', model_xml)
            zf.writestr('Metadata/Slic3r_PE.config', slicer_cfg)
        print(f"  3MF: {len(self.tris)} tris → {path}")


# ═══════════════════════════════════════════════════════════
# PRIMITIVE: Watertight box (6 faces, 12 tris)
# ═══════════════════════════════════════════════════════════
def box(m, x0, y0, z0, x1, y1, z1):
    """Axis-aligned watertight box. All normals face outward."""
    p = [
        (x0, y0, z0),  # 0: left  front bottom
        (x1, y0, z0),  # 1: right front bottom
        (x1, y1, z0),  # 2: right back  bottom
        (x0, y1, z0),  # 3: left  back  bottom
        (x0, y0, z1),  # 4: left  front top
        (x1, y0, z1),  # 5: right front top
        (x1, y1, z1),  # 6: right back  top
        (x0, y1, z1),  # 7: left  back  top
    ]
    # Bottom (-Z)
    m.quad(p[0], p[3], p[2], p[1])
    # Top (+Z)
    m.quad(p[4], p[5], p[6], p[7])
    # Front (-Y)
    m.quad(p[0], p[1], p[5], p[4])
    # Back (+Y)
    m.quad(p[3], p[7], p[6], p[2])
    # Left (-X)
    m.quad(p[0], p[4], p[7], p[3])
    # Right (+X)
    m.quad(p[1], p[2], p[6], p[5])


# ═══════════════════════════════════════════════════════════
# PRIMITIVE: Watertight half-pipe shell
# ═══════════════════════════════════════════════════════════
def half_pipe(m, cx, y0, y1, rx0, rz0, rx1, rz1,
              wall=3.0, arc_deg=180, y_steps=8, segs=20):
    """
    Half-pipe shell (arch). Arch curves UP, opening faces DOWN at Z=0.
    arc_deg: how far around it wraps (180 = full semicircle).
    """
    arc_rad = math.radians(arc_deg)
    start_a = (math.pi - arc_rad) / 2

    def ring(y, rx, rz):
        rx_in = max(0.5, rx - wall)
        rz_in = max(0.5, rz - wall)
        outer = []
        inner = []
        for i in range(segs + 1):
            t = i / segs
            a = start_a + arc_rad * t
            ca, sa = math.cos(a), math.sin(a)
            outer.append((cx + rx * ca, y, rz * sa))
            inner.append((cx + rx_in * ca, y, rz_in * sa))
        return outer, inner

    rings = []
    for yi in range(y_steps + 1):
        t = yi / y_steps
        y = y0 + (y1 - y0) * t
        rx = rx0 + (rx1 - rx0) * t
        rz = rz0 + (rz1 - rz0) * t
        rings.append(ring(y, rx, rz))

    for yi in range(y_steps):
        o1, i1 = rings[yi]
        o2, i2 = rings[yi + 1]
        for si in range(segs):
            # Outer surface
            m.quad(o1[si], o2[si], o2[si+1], o1[si+1])
            # Inner surface
            m.quad(i1[si], i1[si+1], i2[si+1], i2[si])
        # Rim strips
        m.quad(i1[0], i2[0], o2[0], o1[0])
        m.quad(o1[-1], o2[-1], i2[-1], i1[-1])

    # Front end cap (y=y0)
    o_f, i_f = rings[0]
    for si in range(segs):
        m.quad(i_f[si], o_f[si], o_f[si+1], i_f[si+1])

    # Back end cap (y=y1)
    o_b, i_b = rings[-1]
    for si in range(segs):
        m.quad(o_b[si], i_b[si], i_b[si+1], o_b[si+1])


# ═══════════════════════════════════════════════════════════
# GAUNTLET ASSEMBLY
# ═══════════════════════════════════════════════════════════
def generate():
    m = Mesh()

    # Y = arm length (elbow at Y=0, fingertips at Y=220)
    # X = width (centered on 0)
    # Z = height (bed at Z=0, top of gauntlet is positive Z)
    # Arch opens downward — arm slides in from below

    # ════════════════════════════════════════════════════
    # MAIN ARMOR SHELL
    # ════════════════════════════════════════════════════

    # ── FOREARM ── (Y=0..100)
    half_pipe(m, cx=0, y0=0, y1=100,
              rx0=42, rz0=30, rx1=36, rz1=26,
              wall=2.5, arc_deg=180, y_steps=12, segs=24)

    # ── WRIST CUFF ── (Y=102..126)
    half_pipe(m, cx=0, y0=102, y1=126,
              rx0=38, rz0=32, rx1=44, rz1=30,
              wall=3.5, arc_deg=180, y_steps=6, segs=24)

    # ── Wrist flange/lip ── (Y=124..128)
    half_pipe(m, cx=0, y0=124, y1=128,
              rx0=47, rz0=32, rx1=47, rz1=32,
              wall=4.0, arc_deg=180, y_steps=2, segs=24)

    # ── HAND PLATE ── (Y=130..168)
    half_pipe(m, cx=0, y0=130, y1=168,
              rx0=42, rz0=22, rx1=40, rz1=20,
              wall=2.5, arc_deg=170, y_steps=8, segs=24)

    # ── KNUCKLE GUARD ── (Y=170..182)
    half_pipe(m, cx=0, y0=170, y1=182,
              rx0=43, rz0=26, rx1=42, rz1=25,
              wall=4.0, arc_deg=170, y_steps=4, segs=24)

    # ════════════════════════════════════════════════════
    # FINGER ARMOR — segmented plates
    # ════════════════════════════════════════════════════

    finger_positions = [-26, -9, 8, 25]
    fw = 14.0   # plate width
    ft = 3.5    # plate thickness

    for fx in finger_positions:
        z_base = 18
        # Proximal segment
        box(m,
            fx - fw/2, 184, z_base,
            fx + fw/2, 200, z_base + ft)
        # Distal segment (slightly narrower)
        box(m,
            fx - fw/2 + 1, 202, z_base + 0.5,
            fx + fw/2 - 1, 216, z_base + ft - 0.2)

    # ── THUMB GUARD ──
    box(m, -48, 148, 8, -36, 170, 12)
    box(m, -47, 172, 8.5, -37, 184, 11.5)

    # ════════════════════════════════════════════════════
    # SCI-FI SURFACE DETAILS
    # ════════════════════════════════════════════════════

    # Central spine ridge
    box(m, -3, 5, 29, 3, 95, 33)
    # Spine glow channel
    box(m, -1.5, 10, 33, 1.5, 90, 34.5)

    # Horizontal tech ridges on forearm
    for ry in [15, 35, 55, 75]:
        box(m, -30, ry, 24, 30, ry + 3, 27)

    # Diagonal accent lines on hand plate
    box(m, -25, 135, 20, -5, 138, 22.5)
    box(m, 5, 135, 20, 25, 138, 22.5)
    box(m, -20, 150, 19, 20, 153, 21.5)

    # Knuckle bumps
    for kx in finger_positions:
        box(m, kx - 5, 172, 24, kx + 5, 180, 28)

    # Wrist accent plates
    box(m, -46, 108, 10, -40, 122, 18)
    box(m, 40, 108, 10, 46, 122, 18)

    # Elbow guard bump
    box(m, -12, 0, 28, 12, 8, 34)

    # Strap slot guides (inside)
    box(m, -35, 30, 0, -28, 36, 2)
    box(m, 28, 30, 0, 35, 36, 2)
    box(m, -35, 70, 0, -28, 76, 2)
    box(m, 28, 70, 0, 35, 76, 2)

    return m


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════
if __name__ == '__main__':
    print("=" * 55)
    print("  GAUNTLET v5 — Sci-Fi Tech Armor")
    print("  Tree Supports / Bambu A1 + P1S")
    print("=" * 55)
    print()

    m = generate()
    base = os.path.dirname(os.path.abspath(__file__))

    stl_path = os.path.join(base, OUTPUT_STL)
    m.save_stl(stl_path)

    mf_path = os.path.join(base, OUTPUT_3MF)
    m.save_3mf(mf_path)

    print(f"\n  Vertices: {len(m.verts)}")
    print(f"  Triangles: {len(m.tris)}")
    print()
    print("  DESIGN:")
    print("  + Wrapping half-pipe armor shell")
    print("  + Flared wrist cuff with lip")
    print("  + Raised knuckle guard")
    print("  + Segmented finger armor plates")
    print("  + Central spine ridge + tech ridges")
    print("  + Sci-fi surface details")
    print("  + Open palm for grip")
    print("  + Strap slots for fit")
    print()
    print("  PRINT: PLA/PETG | 0.2mm | 15% infill")
    print("         3 walls | Tree supports: AUTO")
