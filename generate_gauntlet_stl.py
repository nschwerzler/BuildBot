"""
Gauntlet v8 — Angular Flat-Panel Armor
═══════════════════════════════════════
NO MORE DOMES. Flat top, angled sides, sharp edges.

Cross-section:
       ┌──────────────┐       ← flat top plate
      /                \      ← angled side walls
     │                  │     ← short vertical rim
     └──────────────────┘     ← open bottom (arm goes here)

This is built entirely from flat quads — no curves.
One connected piece from elbow to hand.
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


def angular_shell(m, profiles):
    """
    Build a connected angular armor shell from profile slices.

    Each profile defines the cross-section at a Y position:
        (y, top_w, bot_w, height, side_drop, wall)

    Cross-section (looking from front, Y pointing into screen):

          outer_tl ────────── outer_tr        ← top plate (width = top_w)
          /                        \          ← angled side walls
    outer_bl                     outer_br     ← bottom edge (width = bot_w)
    outer_ll ──────────────── outer_lr        ← vertical rim (side_drop deep)

    Inner surface is offset inward by 'wall' thickness.

    Z coordinates:
      - outer_lr/outer_ll at Z=0 (bottom rim, sits on bed when printing upside down)
      - outer_bl/outer_br at Z=side_drop
      - outer_tl/outer_tr at Z=height (top of armor)
    """
    def cross(y, top_w, bot_w, h, sd, wall):
        """Returns 8 outer points and 8 inner points for the cross-section.
        Going: left-rim-bottom, left-bottom, left-top, right-top, right-bottom, right-rim-bottom
        That's 6 outer points and 6 inner points.
        """
        tw, bw = top_w / 2, bot_w / 2
        tw_i = (top_w - 2*wall) / 2
        bw_i = (bot_w - 2*wall) / 2

        # Outer points (counterclockwise from bottom-left rim)
        outer = [
            (-bw, y, 0),          # 0: left rim bottom
            (-bw, y, sd),         # 1: left bottom (end of vertical rim)
            (-tw, y, h),          # 2: left top
            ( tw, y, h),          # 3: right top
            ( bw, y, sd),         # 4: right bottom
            ( bw, y, 0),          # 5: right rim bottom
        ]
        # Inner points (same shape, inset by wall)
        inner = [
            (-bw_i, y, wall),         # 0: left rim bottom inner
            (-bw_i, y, sd),           # 1: left bottom inner
            (-tw_i, y, h - wall),     # 2: left top inner
            ( tw_i, y, h - wall),     # 3: right top inner
            ( bw_i, y, sd),           # 4: right bottom inner
            ( bw_i, y, wall),         # 5: right rim bottom inner
        ]
        return outer, inner

    slices = [cross(*p) for p in profiles]

    n_pts = 6  # points per cross-section side

    for yi in range(len(slices) - 1):
        o1, i1 = slices[yi]
        o2, i2 = slices[yi + 1]

        # Outer surface: connect adjacent profile segments
        for si in range(n_pts - 1):
            m.quad(o1[si], o1[si+1], o2[si+1], o2[si])

        # Inner surface: reversed winding
        for si in range(n_pts - 1):
            m.quad(i1[si], i2[si], i2[si+1], i1[si+1])

        # Bottom rim strip (connect outer[0] to inner[0] and outer[5] to inner[5])
        # Left bottom edge
        m.quad(o1[0], o2[0], i2[0], i1[0])
        # Right bottom edge
        m.quad(i1[-1], i2[-1], o2[-1], o1[-1])

    # Front end cap (first slice) — close the opening
    o_f, i_f = slices[0]
    for si in range(n_pts - 1):
        m.quad(o_f[si], i_f[si], i_f[si+1], o_f[si+1])
    # Bottom strip of front cap
    m.quad(o_f[0], o_f[-1], i_f[-1], i_f[0])

    # Back end cap (last slice)
    o_b, i_b = slices[-1]
    for si in range(n_pts - 1):
        m.quad(o_b[si], o_b[si+1], i_b[si+1], i_b[si])
    # Bottom strip of back cap
    m.quad(o_b[0], i_b[0], i_b[-1], o_b[-1])

    return slices


def box(m, x0, y0, z0, x1, y1, z1):
    p = [(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),
         (x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]
    m.quad(p[0],p[3],p[2],p[1])
    m.quad(p[4],p[5],p[6],p[7])
    m.quad(p[0],p[1],p[5],p[4])
    m.quad(p[3],p[7],p[6],p[2])
    m.quad(p[0],p[4],p[7],p[3])
    m.quad(p[1],p[2],p[6],p[5])


def generate():
    m = Mesh()

    # Profile: (y, top_width, bottom_width, height, side_drop, wall)
    #
    # top_width: width of the flat top plate
    # bottom_width: width at the bottom edge (wider = more coverage)
    # height: total height from bed to top
    # side_drop: height of the vertical rim at bottom edges
    # wall: shell thickness
    #
    # Cross-section shape:
    #     ┌──top_w──┐
    #    /            \      ← angled walls
    #   │   bot_w      │
    #   └──────────────┘     ← side_drop rim

    profiles = [
        # ── Elbow guard (wider, taller) ──
        # y    top_w  bot_w  height  side_drop  wall
        (0,    50,    80,    35,     8,         3.0),
        (5,    50,    80,    35,     8,         3.0),
        (10,   48,    78,    34,     8,         2.5),

        # ── Forearm (tapers gradually) ──
        (25,   46,    76,    32,     8,         2.5),
        (40,   44,    74,    30,     7,         2.5),
        (55,   42,    72,    28,     7,         2.5),
        (70,   40,    70,    27,     7,         2.5),
        (85,   38,    68,    26,     7,         2.5),
        (95,   36,    66,    25,     6,         2.5),

        # ── Wrist cuff (flares out — signature look) ──
        (100,  38,    68,    26,     6,         3.0),
        (106,  42,    74,    28,     7,         3.0),
        (112,  48,    82,    32,     8,         3.5),
        (118,  52,    88,    34,     10,        3.5),  # flange peak
        (122,  50,    86,    33,     9,         3.0),
        (126,  46,    80,    30,     8,         3.0),

        # ── Hand plate (flatter, wide) ──
        (132,  44,    78,    24,     6,         2.5),
        (142,  42,    76,    22,     6,         2.5),
        (152,  42,    76,    22,     6,         2.5),
        (162,  42,    76,    22,     6,         2.5),

        # ── Knuckle guard (raised bump) ──
        (168,  44,    78,    26,     7,         3.5),
        (173,  46,    80,    30,     8,         4.0),
        (178,  46,    80,    30,     8,         4.0),
        (183,  44,    78,    26,     7,         3.5),
        (188,  42,    76,    22,     6,         2.5),
    ]

    angular_shell(m, profiles)

    # ── FINGER PLATES ── (small angular shells, touching main body)
    finger_xs = [-27, -9, 9, 27]
    for fx in finger_xs:
        fp = [
            # y    top_w  bot_w  height  sd   wall
            (190,  12,    16,    20,     4,   2.0),
            (196,  12,    16,    19,     4,   2.0),
            (202,  11,    15,    18,     4,   2.0),
        ]
        # Offset X by shifting all points
        fp_shifted = [(y, tw, bw, h, sd, w) for y, tw, bw, h, sd, w in fp]
        # Build each finger as small shell, X-shifted
        # Need to manually build since angular_shell is centered at x=0
        # Use profile but with center offset
        for yi in range(len(fp_shifted) - 1):
            y1, tw1, bw1, h1, sd1, w1 = fp_shifted[yi]
            y2, tw2, bw2, h2, sd2, w2 = fp_shifted[yi + 1]
            # Front slice
            thw1, bhw1 = tw1/2, bw1/2
            thw1i, bhw1i = (tw1-2*w1)/2, (bw1-2*w1)/2
            # Back slice
            thw2, bhw2 = tw2/2, bw2/2
            thw2i, bhw2i = (tw2-2*w2)/2, (bw2-2*w2)/2

            o1 = [(fx-bhw1,y1,0),(fx-bhw1,y1,sd1),(fx-thw1,y1,h1),
                  (fx+thw1,y1,h1),(fx+bhw1,y1,sd1),(fx+bhw1,y1,0)]
            i1 = [(fx-bhw1i,y1,w1),(fx-bhw1i,y1,sd1),(fx-thw1i,y1,h1-w1),
                  (fx+thw1i,y1,h1-w1),(fx+bhw1i,y1,sd1),(fx+bhw1i,y1,w1)]
            o2 = [(fx-bhw2,y2,0),(fx-bhw2,y2,sd2),(fx-thw2,y2,h2),
                  (fx+thw2,y2,h2),(fx+bhw2,y2,sd2),(fx+bhw2,y2,0)]
            i2 = [(fx-bhw2i,y2,w2),(fx-bhw2i,y2,sd2),(fx-thw2i,y2,h2-w2),
                  (fx+thw2i,y2,h2-w2),(fx+bhw2i,y2,sd2),(fx+bhw2i,y2,w2)]

            for si in range(5):
                m.quad(o1[si], o1[si+1], o2[si+1], o2[si])
                m.quad(i1[si], i2[si], i2[si+1], i1[si+1])
            m.quad(o1[0], o2[0], i2[0], i1[0])
            m.quad(i1[-1], i2[-1], o2[-1], o1[-1])

        # Front cap
        y1, tw1, bw1, h1, sd1, w1 = fp_shifted[0]
        thw1, bhw1 = tw1/2, bw1/2
        thw1i, bhw1i = (tw1-2*w1)/2, (bw1-2*w1)/2
        o_f = [(fx-bhw1,y1,0),(fx-bhw1,y1,sd1),(fx-thw1,y1,h1),
               (fx+thw1,y1,h1),(fx+bhw1,y1,sd1),(fx+bhw1,y1,0)]
        i_f = [(fx-bhw1i,y1,w1),(fx-bhw1i,y1,sd1),(fx-thw1i,y1,h1-w1),
               (fx+thw1i,y1,h1-w1),(fx+bhw1i,y1,sd1),(fx+bhw1i,y1,w1)]
        for si in range(5):
            m.quad(o_f[si], i_f[si], i_f[si+1], o_f[si+1])
        m.quad(o_f[0], o_f[-1], i_f[-1], i_f[0])

        # Back cap
        y2, tw2, bw2, h2, sd2, w2 = fp_shifted[-1]
        thw2, bhw2 = tw2/2, bw2/2
        thw2i, bhw2i = (tw2-2*w2)/2, (bw2-2*w2)/2
        o_b = [(fx-bhw2,y2,0),(fx-bhw2,y2,sd2),(fx-thw2,y2,h2),
               (fx+thw2,y2,h2),(fx+bhw2,y2,sd2),(fx+bhw2,y2,0)]
        i_b = [(fx-bhw2i,y2,w2),(fx-bhw2i,y2,sd2),(fx-thw2i,y2,h2-w2),
               (fx+thw2i,y2,h2-w2),(fx+bhw2i,y2,sd2),(fx+bhw2i,y2,w2)]
        for si in range(5):
            m.quad(o_b[si], o_b[si+1], i_b[si+1], i_b[si])
        m.quad(o_b[0], i_b[0], i_b[-1], o_b[-1])

        # Fingertip plate (smaller)
        ftp = [
            (205, 10, 14, 17, 3, 2.0),
            (210, 9, 12, 16, 3, 2.0),
            (216, 8, 10, 15, 3, 2.0),
        ]
        for yi in range(len(ftp) - 1):
            y1, tw1, bw1, h1, sd1, w1 = ftp[yi]
            y2, tw2, bw2, h2, sd2, w2 = ftp[yi + 1]
            thw1, bhw1 = tw1/2, bw1/2
            thw1i, bhw1i = (tw1-2*w1)/2, (bw1-2*w1)/2
            thw2, bhw2 = tw2/2, bw2/2
            thw2i, bhw2i = (tw2-2*w2)/2, (bw2-2*w2)/2

            o1 = [(fx-bhw1,y1,0),(fx-bhw1,y1,sd1),(fx-thw1,y1,h1),
                  (fx+thw1,y1,h1),(fx+bhw1,y1,sd1),(fx+bhw1,y1,0)]
            i1 = [(fx-bhw1i,y1,w1),(fx-bhw1i,y1,sd1),(fx-thw1i,y1,h1-w1),
                  (fx+thw1i,y1,h1-w1),(fx+bhw1i,y1,sd1),(fx+bhw1i,y1,w1)]
            o2 = [(fx-bhw2,y2,0),(fx-bhw2,y2,sd2),(fx-thw2,y2,h2),
                  (fx+thw2,y2,h2),(fx+bhw2,y2,sd2),(fx+bhw2,y2,0)]
            i2 = [(fx-bhw2i,y2,w2),(fx-bhw2i,y2,sd2),(fx-thw2i,y2,h2-w2),
                  (fx+thw2i,y2,h2-w2),(fx+bhw2i,y2,sd2),(fx+bhw2i,y2,w2)]

            for si in range(5):
                m.quad(o1[si], o1[si+1], o2[si+1], o2[si])
                m.quad(i1[si], i2[si], i2[si+1], i1[si+1])
            m.quad(o1[0], o2[0], i2[0], i1[0])
            m.quad(i1[-1], i2[-1], o2[-1], o1[-1])

        # Tip front cap
        y1, tw1, bw1, h1, sd1, w1 = ftp[0]
        thw1, bhw1 = tw1/2, bw1/2
        thw1i, bhw1i = (tw1-2*w1)/2, (bw1-2*w1)/2
        o_f = [(fx-bhw1,y1,0),(fx-bhw1,y1,sd1),(fx-thw1,y1,h1),
               (fx+thw1,y1,h1),(fx+bhw1,y1,sd1),(fx+bhw1,y1,0)]
        i_f = [(fx-bhw1i,y1,w1),(fx-bhw1i,y1,sd1),(fx-thw1i,y1,h1-w1),
               (fx+thw1i,y1,h1-w1),(fx+bhw1i,y1,sd1),(fx+bhw1i,y1,w1)]
        for si in range(5):
            m.quad(o_f[si], i_f[si], i_f[si+1], o_f[si+1])
        m.quad(o_f[0], o_f[-1], i_f[-1], i_f[0])

        # Tip back cap
        y2, tw2, bw2, h2, sd2, w2 = ftp[-1]
        thw2, bhw2 = tw2/2, bw2/2
        thw2i, bhw2i = (tw2-2*w2)/2, (bw2-2*w2)/2
        o_b = [(fx-bhw2,y2,0),(fx-bhw2,y2,sd2),(fx-thw2,y2,h2),
               (fx+thw2,y2,h2),(fx+bhw2,y2,sd2),(fx+bhw2,y2,0)]
        i_b = [(fx-bhw2i,y2,w2),(fx-bhw2i,y2,sd2),(fx-thw2i,y2,h2-w2),
               (fx+thw2i,y2,h2-w2),(fx+bhw2i,y2,sd2),(fx+bhw2i,y2,w2)]
        for si in range(5):
            m.quad(o_b[si], o_b[si+1], i_b[si+1], i_b[si])
        m.quad(o_b[0], i_b[0], i_b[-1], o_b[-1])

    # ── THUMB GUARD ── (small angular shell, offset left)
    thumb_profiles = [
        (148, 14, 18, 18, 4, 2.0),
        (158, 14, 18, 17, 4, 2.0),
        (168, 12, 16, 16, 3, 2.0),
        (176, 10, 14, 14, 3, 2.0),
    ]
    # Build thumb shell manually with X offset
    tx = -46
    thumb_slices = []
    for y, tw, bw, h, sd, w in thumb_profiles:
        thw, bhw = tw/2, bw/2
        thwi, bhwi = (tw-2*w)/2, (bw-2*w)/2
        outer = [(tx-bhw,y,0),(tx-bhw,y,sd),(tx-thw,y,h),
                 (tx+thw,y,h),(tx+bhw,y,sd),(tx+bhw,y,0)]
        inner = [(tx-bhwi,y,w),(tx-bhwi,y,sd),(tx-thwi,y,h-w),
                 (tx+thwi,y,h-w),(tx+bhwi,y,sd),(tx+bhwi,y,w)]
        thumb_slices.append((outer, inner))

    for yi in range(len(thumb_slices) - 1):
        o1, i1 = thumb_slices[yi]
        o2, i2 = thumb_slices[yi + 1]
        for si in range(5):
            m.quad(o1[si], o1[si+1], o2[si+1], o2[si])
            m.quad(i1[si], i2[si], i2[si+1], i1[si+1])
        m.quad(o1[0], o2[0], i2[0], i1[0])
        m.quad(i1[-1], i2[-1], o2[-1], o1[-1])
    # Front/back caps
    o_f, i_f = thumb_slices[0]
    for si in range(5):
        m.quad(o_f[si], i_f[si], i_f[si+1], o_f[si+1])
    m.quad(o_f[0], o_f[-1], i_f[-1], i_f[0])
    o_b, i_b = thumb_slices[-1]
    for si in range(5):
        m.quad(o_b[si], o_b[si+1], i_b[si+1], i_b[si])
    m.quad(o_b[0], i_b[0], i_b[-1], o_b[-1])

    # ═══════════════════════════════════════════
    # STRAP LOOPS (connected to side walls)
    # ═══════════════════════════════════════════
    for yp in [20, 60, 110]:
        # Left
        box(m, -44, yp, 0, -40, yp+12, 2.5)
        box(m, -44, yp, 6, -40, yp+12, 8.5)
        # Right
        box(m, 40, yp, 0, 44, yp+12, 2.5)
        box(m, 40, yp, 6, 44, yp+12, 8.5)

    return m


if __name__ == '__main__':
    print("=" * 55)
    print("  GAUNTLET v8 — Angular Flat-Panel Armor")
    print("=" * 55)
    print()

    m = generate()
    base = os.path.dirname(os.path.abspath(__file__))

    stl_path = os.path.join(base, OUTPUT_STL)
    m.save_stl(stl_path)
    mf_path = os.path.join(base, OUTPUT_3MF)
    m.save_3mf(mf_path)

    print(f"\n  Verts: {len(m.verts)}  Tris: {len(m.tris)}")
    print()
    print("  SHAPE:")
    print("  + Flat top plate with angled side walls")
    print("  + NOT a dome — angular armor panels")
    print("  + One connected main shell")
    print("  + Flared wrist cuff + raised knuckle guard")
    print("  + Finger armor plates + thumb guard")
    print("  + Strap loops for fit")
    print("  + Open palm")
