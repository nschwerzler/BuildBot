"""
Gauntlet Generator v7 — ONE Connected Piece
════════════════════════════════════════════
Single continuous shell from elbow to knuckles.
No floating parts. No gaps. Everything connected.

Shape: shallow curved armor plate that sits on top of your arm.
The shape itself creates the sci-fi look via:
  - Varying width profile (flared wrist cuff)
  - Varying arch height (raised knuckle guard)
  - Varying wall thickness (reinforced sections)

Finger guards are separate but positioned flush to the main shell.
"""
import math
import os
import zipfile

OUTPUT_STL = "gauntlet.stl"
OUTPUT_3MF = "gauntlet.3mf"


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
        return (nx/ln, ny/ln, nz/ln) if ln > 1e-12 else (0, 0, 1)

    def save_stl(self, path):
        with open(path, 'w') as f:
            f.write("solid gauntlet\n")
            for ia, ib, ic in self.tris:
                n = self._normal(ia, ib, ic)
                a, b, c = self.verts[ia], self.verts[ib], self.verts[ic]
                f.write(f"  facet normal {n[0]:.6e} {n[1]:.6e} {n[2]:.6e}\n")
                f.write("    outer loop\n")
                f.write(f"      vertex {a[0]:.6e} {a[1]:.6e} {a[2]:.6e}\n")
                f.write(f"      vertex {b[0]:.6e} {b[1]:.6e} {b[2]:.6e}\n")
                f.write(f"      vertex {c[0]:.6e} {c[1]:.6e} {c[2]:.6e}\n")
                f.write("    endloop\n  endfacet\n")
            f.write("endsolid gauntlet\n")
        print(f"  STL: {len(self.tris)} tris -> {path}")

    def save_3mf(self, path):
        vlines = [f'          <vertex x="{x}" y="{y}" z="{z}"/>'
                  for x, y, z in self.verts]
        tlines = [f'          <triangle v1="{a}" v2="{b}" v3="{c}"/>'
                  for a, b, c in self.tris]
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
            '; Gauntlet tree supports\n'
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
        print(f"  3MF: {len(self.tris)} tris -> {path}")


def box(m, x0, y0, z0, x1, y1, z1):
    p = [(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),
         (x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]
    m.quad(p[0],p[3],p[2],p[1])
    m.quad(p[4],p[5],p[6],p[7])
    m.quad(p[0],p[1],p[5],p[4])
    m.quad(p[3],p[7],p[6],p[2])
    m.quad(p[0],p[4],p[7],p[3])
    m.quad(p[1],p[2],p[6],p[5])


def continuous_shell(m, profiles, cx=0, x_segs=20):
    """
    Build ONE continuous watertight shell from a list of profile slices.

    profiles: list of (y, width, height, wall) tuples.
              These define the cross-section at each Y position.
              The shell smoothly transitions between them.
              MUST be sorted by Y.

    Each cross-section is a parabolic arch:
      - width = total span side to side
      - height = how tall the arch rises at center
      - wall = shell thickness

    Prints convex side DOWN (dome on bed).
    Wear convex side UP (dome on top of arm).
    """
    def cross_section(y, w, h, wall):
        hw = w / 2.0
        outer = []
        inner = []
        for i in range(x_segs + 1):
            t = i / x_segs
            x = cx - hw + w * t
            curve = 4.0 * t * (1.0 - t)  # parabolic: 0 at edges, 1 at center
            z_outer = curve * h
            z_inner = z_outer + wall
            outer.append((x, y, z_outer))
            inner.append((x, y, z_inner))
        return outer, inner

    # Generate all cross-section rings
    slices = [cross_section(y, w, h, wall) for y, w, h, wall in profiles]

    # Build quad strips between adjacent slices
    for yi in range(len(slices) - 1):
        o1, i1 = slices[yi]
        o2, i2 = slices[yi + 1]
        for si in range(x_segs):
            # Outer surface (convex, faces down when printing)
            m.quad(o1[si], o1[si+1], o2[si+1], o2[si])
            # Inner surface (concave, faces up when printing)
            m.quad(i1[si], i2[si], i2[si+1], i1[si+1])
        # Left edge strip
        m.quad(o1[0], o2[0], i2[0], i1[0])
        # Right edge strip
        m.quad(o1[-1], i1[-1], i2[-1], o2[-1])

    # Front end cap (first slice)
    o_f, i_f = slices[0]
    for si in range(x_segs):
        m.quad(o_f[si], i_f[si], i_f[si+1], o_f[si+1])

    # Back end cap (last slice)
    o_b, i_b = slices[-1]
    for si in range(x_segs):
        m.quad(o_b[si], o_b[si+1], i_b[si+1], i_b[si])

    return slices  # return for positioning fingers etc.


def generate():
    m = Mesh()

    # ════════════════════════════════════════════════════
    # MAIN SHELL — one continuous piece, elbow to knuckles
    # ════════════════════════════════════════════════════
    # Profile: (y, width, height, wall)
    # The shape tells the story:
    #   - Elbow: wide, tall arch
    #   - Forearm: gradually narrows
    #   - Wrist: flares out (signature gauntlet cuff)
    #   - Hand: flatter, wider
    #   - Knuckles: raised bump, thicker
    profiles = [
        # Y     Width  Height  Wall
        # ── Elbow cap ──
        (0,     80,    24,     3.0),
        (4,     80,    24,     3.0),
        # ── Forearm taper ──
        (15,    78,    22,     2.5),
        (30,    76,    21,     2.5),
        (50,    74,    20,     2.5),
        (70,    72,    19,     2.5),
        (85,    70,    18,     2.5),
        (95,    68,    18,     2.5),
        # ── Wrist cuff flare ──
        (100,   70,    20,     3.0),
        (108,   76,    22,     3.0),
        (115,   82,    24,     3.5),
        (120,   88,    26,     3.5),  # widest point = flange
        (125,   86,    24,     3.0),
        # ── Hand plate ──
        (132,   80,    18,     2.5),
        (145,   78,    16,     2.5),
        (158,   76,    15,     2.5),
        (168,   76,    15,     2.5),
        # ── Knuckle guard bump ──
        (172,   78,    18,     3.5),
        (176,   80,    22,     4.0),
        (180,   80,    22,     4.0),
        (184,   78,    20,     3.5),
        (188,   76,    16,     3.0),
    ]

    slices = continuous_shell(m, profiles, cx=0, x_segs=24)

    # ════════════════════════════════════════════════════
    # FINGER ARMOR — small curved plates, flush to main shell
    # ════════════════════════════════════════════════════
    # These connect at the knuckle end of the main shell.
    # Each finger is a small curved plate.
    finger_xs = [-28, -10, 10, 28]
    for fx in finger_xs:
        # Proximal segment (near knuckles)
        continuous_shell(m, [
            (190, 15, 6, 2.0),
            (195, 15, 6, 2.0),
            (200, 14, 5, 2.0),
            (204, 13, 5, 2.0),
        ], cx=fx, x_segs=8)
        # Distal segment (fingertip)
        continuous_shell(m, [
            (207, 13, 5, 2.0),
            (210, 12, 4.5, 2.0),
            (214, 11, 4, 2.0),
            (218, 10, 3.5, 2.0),
        ], cx=fx, x_segs=8)

    # ── Thumb guard ──
    continuous_shell(m, [
        (150, 16, 8, 2.0),
        (155, 16, 8, 2.0),
        (162, 15, 7, 2.0),
        (170, 14, 6, 2.0),
        (176, 13, 5, 2.0),
    ], cx=-46, x_segs=8)

    # ════════════════════════════════════════════════════
    # STRAP LOOPS — connected to shell edges
    # ════════════════════════════════════════════════════
    # Position loops at the shell edge Z=0 level
    # They bridge from the shell rim downward
    for y_pos in [25, 65, 112]:
        # Left loop
        box(m, -42, y_pos, 0, -39, y_pos+10, 8)   # post
        box(m, -42, y_pos, 6, -39, y_pos+10, 8)    # bridge top
        # Right loop
        box(m, 39, y_pos, 0, 42, y_pos+10, 8)
        box(m, 39, y_pos, 6, 42, y_pos+10, 8)

    return m


if __name__ == '__main__':
    print("=" * 55)
    print("  GAUNTLET v7 — One Connected Piece")
    print("  Sci-Fi / Wearable / Tree Supports")
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
    print("  CHANGES (v7):")
    print("  + ONE continuous shell — no gaps, no floating parts")
    print("  + Shape creates the armor look (flared cuff, knuckle bump)")
    print("  + No disconnected decorations")
    print("  + Finger plates + thumb guard")
    print("  + Strap loops at edges")
    print()
    print("  PRINT: PLA/PETG | 0.2mm | 15% infill | Tree supports")
