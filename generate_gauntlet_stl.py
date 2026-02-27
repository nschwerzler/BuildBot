"""
Gauntlet Generator v6 — Sci-Fi Top-Shell Armor
═══════════════════════════════════════════════
Wearable 3D-printed gauntlet that sits ON TOP of the forearm/hand.

Key insight: A rigid 3D print can't flex to wrap around an arm.
Instead, this is a shallow curved SHELL that covers the top and
sides, with a wide-open bottom. Arm rests into it, secured by
straps through built-in loops.

    ╭━━━━━━━━━━╮   ← armor shell (top)
    │  forearm  │
    ╰──────────╯   ← open bottom (straps hold it on)

Design:
  - Shallow curved shell (~120° arc) — NOT a full half-pipe
  - Prints FLAT (concave side up) — minimal supports needed
  - Forearm bracer → wrist cuff → hand plate → finger guards
  - Sci-fi surface details: spine, ridges, channels
  - Strap loops on sides for elastic/velcro bands
  - Open palm, open bottom — easy on/off

Outputs:
  gauntlet.stl  — Universal
  gauntlet.3mf  — Bambu Studio (tree supports auto)
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


# ═══════════════════════════════════════════════════════════
# BOX primitive
# ═══════════════════════════════════════════════════════════
def box(m, x0, y0, z0, x1, y1, z1):
    p = [(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),
         (x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]
    m.quad(p[0],p[3],p[2],p[1])  # bottom
    m.quad(p[4],p[5],p[6],p[7])  # top
    m.quad(p[0],p[1],p[5],p[4])  # front
    m.quad(p[3],p[7],p[6],p[2])  # back
    m.quad(p[0],p[4],p[7],p[3])  # left
    m.quad(p[1],p[2],p[6],p[5])  # right


# ═══════════════════════════════════════════════════════════
# SHELL: Shallow curved armor plate
# ═══════════════════════════════════════════════════════════
def armor_shell(m, cx, y0, y1, width0, width1, height0, height1,
                wall=2.5, y_steps=10, x_segs=16):
    """
    Curved armor shell — shallow arch that sits on top of arm.
    Printed CONCAVE SIDE UP (like a boat hull).

    The shell is a gentle curve in X-Z plane:
      - width = total side-to-side span
      - height = how tall the arch rises at center
      - wall = shell thickness
      - Opens at the bottom (Z=0 level = edges of shell)

    Orientation for printing:
      - The shell prints with its CONVEX side down on the bed
      - Z=0 is the bed, the outer surface curves up
      - Inner surface is on top (concave facing up)

    Actually — for wearing, we want:
      - Convex (outer armor) faces outward/up when worn
      - Concave (inner) cups the arm

    For printing: lay it CONVEX SIDE DOWN (dome down).
    The outer dome surface rests on the bed, inner cavity faces up.
    This means: outer surface at LOW Z, inner surface at HIGH Z.
    """
    def cross_section(y, w, h):
        """Generate outer and inner curve points at a given Y slice.
        Returns (outer_pts, inner_pts) from left edge to right edge.
        Outer is at lower Z (on bed), inner is at higher Z.
        """
        hw = w / 2.0
        outer = []
        inner = []
        for i in range(x_segs + 1):
            t = i / x_segs  # 0..1 across width
            x = cx - hw + w * t
            # Parabolic arch: peak at center (t=0.5), zero at edges
            curve = 4.0 * t * (1.0 - t)  # 0 at edges, 1 at center
            z_outer = curve * h  # outer surface (lower, on bed)
            z_inner = z_outer + wall  # inner surface (higher)
            outer.append((x, y, z_outer))
            inner.append((x, y, z_inner))
        return outer, inner

    # Generate cross-sections along Y
    slices = []
    for yi in range(y_steps + 1):
        t = yi / y_steps
        y = y0 + (y1 - y0) * t
        w = width0 + (width1 - width0) * t
        h = height0 + (height1 - height0) * t
        slices.append(cross_section(y, w, h))

    # Build quad strips between adjacent Y slices
    for yi in range(y_steps):
        o1, i1 = slices[yi]      # front slice
        o2, i2 = slices[yi + 1]  # back slice

        for si in range(x_segs):
            # Outer surface (convex, faces DOWN = outward normals)
            m.quad(o1[si], o1[si+1], o2[si+1], o2[si])
            # Inner surface (concave, faces UP)
            m.quad(i1[si], i2[si], i2[si+1], i1[si+1])

        # Left edge strip (connect outer to inner at left)
        m.quad(o1[0], o2[0], i2[0], i1[0])
        # Right edge strip
        m.quad(o1[-1], i1[-1], i2[-1], o2[-1])

    # Front end cap (y=y0)
    o_f, i_f = slices[0]
    for si in range(x_segs):
        m.quad(o_f[si], i_f[si], i_f[si+1], o_f[si+1])

    # Back end cap (y=y1)
    o_b, i_b = slices[-1]
    for si in range(x_segs):
        m.quad(o_b[si], o_b[si+1], i_b[si+1], i_b[si])


# ═══════════════════════════════════════════════════════════
# STRAP LOOP — rectangular loop on the side for straps
# ═══════════════════════════════════════════════════════════
def strap_loop(m, x, y, z, loop_w=8, loop_h=6, bar_thick=2.5):
    """
    A rectangular loop/bridge on the side of the shell.
    Strap threads through the opening.
    """
    # Two vertical posts
    box(m, x, y, z, x + bar_thick, y + loop_w, z + loop_h)
    box(m, x, y, z, x + bar_thick, y + loop_w, z + bar_thick)
    # Top bridge connecting them
    box(m, x, y, z + loop_h - bar_thick, x + bar_thick, y + loop_w, z + loop_h)


# ═══════════════════════════════════════════════════════════
# GAUNTLET ASSEMBLY
# ═══════════════════════════════════════════════════════════
def generate():
    m = Mesh()

    # Coordinate system (for printing & wearing):
    # Y = arm length direction (elbow=0, fingers=220)
    # X = width (centered on 0, left/right)
    # Z = vertical (bed=0, up)
    #
    # The shell prints DOME DOWN: convex outer on bed,
    # concave inner faces up. When you pick it up and flip
    # it over onto your arm, the dome is on top.

    # ════════════════════════════════════════════════════
    # MAIN ARMOR SECTIONS
    # ════════════════════════════════════════════════════

    # ── FOREARM BRACER ── (Y=0..100)
    # Widest at elbow, narrows toward wrist
    armor_shell(m, cx=0, y0=0, y1=100,
                width0=80, width1=70, height0=22, height1=18,
                wall=2.5, y_steps=12, x_segs=20)

    # ── WRIST CUFF ── (Y=104..130)
    # Flares out slightly — signature gauntlet look
    armor_shell(m, cx=0, y0=104, y1=130,
                width0=72, width1=82, height0=20, height1=24,
                wall=3.0, y_steps=8, x_segs=20)

    # ── WRIST FLANGE ── (Y=128..134)
    # Extra-wide lip at end of cuff
    armor_shell(m, cx=0, y0=128, y1=134,
                width0=88, width1=88, height0=24, height1=24,
                wall=3.5, y_steps=2, x_segs=20)

    # ── HAND PLATE ── (Y=138..174)
    # Flatter, covers back of hand
    armor_shell(m, cx=0, y0=138, y1=174,
                width0=80, width1=76, height0=16, height1=14,
                wall=2.5, y_steps=8, x_segs=20)

    # ── KNUCKLE GUARD ── (Y=176..188)
    # Raised ridge across knuckles
    armor_shell(m, cx=0, y0=176, y1=188,
                width0=78, width1=76, height0=20, height1=18,
                wall=3.5, y_steps=4, x_segs=20)

    # ════════════════════════════════════════════════════
    # FINGER ARMOR — flat articulated plates
    # ════════════════════════════════════════════════════
    finger_xs = [-28, -10, 10, 28]  # 4 finger center positions
    fw = 15.0   # finger plate width
    ft = 3.0    # finger plate thickness

    for fx in finger_xs:
        # Proximal plate (near hand)
        armor_shell(m, cx=fx, y0=190, y1=204,
                    width0=fw, width1=fw-1, height0=6, height1=5,
                    wall=2.0, y_steps=4, x_segs=8)
        # Distal plate (fingertip, slightly narrower)
        armor_shell(m, cx=fx, y0=206, y1=218,
                    width0=fw-2, width1=fw-4, height0=5, height1=4,
                    wall=2.0, y_steps=4, x_segs=8)

    # ── THUMB GUARD ── offset to left side
    armor_shell(m, cx=-46, y0=150, y1=172,
                width0=16, width1=14, height0=8, height1=6,
                wall=2.0, y_steps=4, x_segs=8)

    # ════════════════════════════════════════════════════
    # SCI-FI SURFACE DETAILS (raised features on outer shell)
    # ════════════════════════════════════════════════════

    # Central spine ridge (runs down forearm)
    # Sits at the peak of the dome (highest Z point)
    box(m, -3, 4, 20, 3, 96, 24)

    # Spine glow channel
    box(m, -1.2, 8, 24, 1.2, 92, 25.5)

    # Horizontal tech ridges on forearm
    for ry in [12, 30, 50, 70, 88]:
        box(m, -32, ry, 16, 32, ry+2.5, 19)

    # Hand plate accent lines
    box(m, -28, 142, 13, -6, 145, 15)
    box(m, 6, 142, 13, 28, 145, 15)
    box(m, -22, 158, 12, 22, 161, 14)

    # Knuckle bumps
    for kx in finger_xs:
        box(m, kx-5, 178, 17, kx+5, 186, 21)

    # Side accent plates
    box(m, -42, 108, 6, -38, 126, 14)
    box(m, 38, 108, 6, 42, 126, 14)

    # Elbow guard cap
    box(m, -14, 0, 20, 14, 6, 26)

    # ════════════════════════════════════════════════════
    # STRAP LOOPS — hold the gauntlet on your arm
    # ════════════════════════════════════════════════════
    # Left side loops (2)
    strap_loop(m, x=-43, y=25, z=0, loop_w=10, loop_h=8, bar_thick=2.5)
    strap_loop(m, x=-43, y=65, z=0, loop_w=10, loop_h=8, bar_thick=2.5)

    # Right side loops (2)
    strap_loop(m, x=40.5, y=25, z=0, loop_w=10, loop_h=8, bar_thick=2.5)
    strap_loop(m, x=40.5, y=65, z=0, loop_w=10, loop_h=8, bar_thick=2.5)

    # Extra loops at wrist
    strap_loop(m, x=-44, y=110, z=0, loop_w=10, loop_h=8, bar_thick=2.5)
    strap_loop(m, x=41.5, y=110, z=0, loop_w=10, loop_h=8, bar_thick=2.5)

    return m


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════
if __name__ == '__main__':
    print("=" * 55)
    print("  GAUNTLET v6 — Sci-Fi Top-Shell Armor")
    print("  Wearable / Printable / Tree Supports")
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
    print("  HOW TO WEAR:")
    print("  1. Print dome-down (as oriented)")
    print("  2. Flip over — dome faces up, concave cups arm")
    print("  3. Thread elastic/velcro straps through loops")
    print("  4. Slide arm in, tighten straps")
    print()
    print("  DESIGN:")
    print("  + Shallow curved shell (not a tube!)")
    print("  + Wide open bottom — easy on/off")
    print("  + 6 strap loops for secure fit")
    print("  + Flared wrist cuff with lip")
    print("  + Segmented finger plates")
    print("  + Sci-fi spine + tech ridges")
    print("  + Open palm for grip")
    print()
    print("  PRINT: PLA/PETG | 0.2mm | 15% infill")
    print("         3 walls | Tree supports: AUTO")
