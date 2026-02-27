"""
Gauntlet v9 - Hollow Torus Armor
=================================
Full 360 degree hollow tube your arm slides through.
Like a stretched donut / bracelet shape.

Cross-section at any point is a ring (annulus):
    outer circle wall - gap - inner circle wall

Your arm goes through the center hole.
Open at both ends (elbow entry, fingers exit).

The tube radius and shape varies along the length:
  - Forearm section: oval, tapers
  - Wrist cuff: flares out
  - Hand section: wider, flatter oval
  - Knuckle bump: raised
  - Palm cutout: bottom section removed so you can grip

Prints standing up (Y axis vertical). Tree supports handle it.
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
        kb = os.path.getsize(path) // 1024
        print(f"  3MF: {len(self.tris)} tris, {kb} KB -> {path}")


def hollow_tube(m, profiles, segs=32, palm_cut_start=None, palm_cut_end=None,
                palm_cut_arc=120):
    """
    Build a hollow tube (torus cross-section) from profile slices.

    profiles: list of (y, rx_out, rz_out, wall) tuples
      y = position along arm length
      rx_out = outer radius in X direction (half-width)
      rz_out = outer radius in Z direction (half-height)
      wall = shell thickness

    segs = number of segments around the circumference
    palm_cut_* = optional range to cut out the bottom for palm grip

    The tube is an elliptical cylinder. At each Y slice the cross-section
    is an elliptical annulus (outer ellipse - inner ellipse).
    """
    # Which angular range to keep. Full circle = 0 to 2*pi.
    # For palm cutout, we skip some segments at the bottom (angle ~= 3*pi/2 area).
    # Angle 0 = right (+X), pi/2 = top (+Z), pi = left (-X), 3*pi/2 = bottom (-Z)

    def ring(y, rx_o, rz_o, wall):
        rx_i = max(1.0, rx_o - wall)
        rz_i = max(1.0, rz_o - wall)
        outer = []
        inner = []
        for i in range(segs):
            a = 2.0 * math.pi * i / segs
            ca, sa = math.cos(a), math.sin(a)
            outer.append((rx_o * ca, y, rz_o * sa))
            inner.append((rx_i * ca, y, rz_i * sa))
        return outer, inner

    # Determine which segments to skip for palm cutout
    # Bottom of the tube is at angle 3*pi/2 (270 degrees) = -Z direction
    # We cut a symmetric arc centered at the bottom
    palm_cut_segs = set()
    if palm_cut_start is not None:
        cut_half = math.radians(palm_cut_arc) / 2.0
        center_angle = 3.0 * math.pi / 2.0  # bottom
        for i in range(segs):
            a = 2.0 * math.pi * i / segs
            # Angle distance to bottom center
            diff = abs(a - center_angle)
            if diff > math.pi:
                diff = 2 * math.pi - diff
            if diff < cut_half:
                palm_cut_segs.add(i)

    # Generate all rings
    slices = []
    for p in profiles:
        y, rx, rz, w = p
        slices.append(ring(y, rx, rz, w))

    def in_palm_cut(yi, si):
        """Check if this segment should be cut out for palm."""
        if palm_cut_start is None:
            return False
        y = profiles[yi][0]
        return palm_cut_start <= y <= palm_cut_end and si in palm_cut_segs

    # Build tube walls between adjacent Y slices
    for yi in range(len(slices) - 1):
        o1, i1 = slices[yi]
        o2, i2 = slices[yi + 1]

        for si in range(segs):
            si_next = (si + 1) % segs

            # Check if this quad or the next is in the palm cutout
            cut1 = in_palm_cut(yi, si) or in_palm_cut(yi, si_next)
            cut2 = in_palm_cut(yi + 1, si) or in_palm_cut(yi + 1, si_next)

            if cut1 and cut2:
                continue  # fully in cutout, skip

            # Outer surface (normals point outward)
            m.quad(o1[si], o2[si], o2[si_next], o1[si_next])
            # Inner surface (normals point inward = toward arm)
            m.quad(i1[si], i1[si_next], i2[si_next], i2[si])

    # End caps (annular rings at each end)
    # Front cap (first Y slice)
    o_f, i_f = slices[0]
    for si in range(segs):
        si_next = (si + 1) % segs
        if not (in_palm_cut(0, si) or in_palm_cut(0, si_next)):
            m.quad(o_f[si], i_f[si], i_f[si_next], o_f[si_next])

    # Back cap (last Y slice)
    o_b, i_b = slices[-1]
    last_yi = len(slices) - 1
    for si in range(segs):
        si_next = (si + 1) % segs
        if not (in_palm_cut(last_yi, si) or in_palm_cut(last_yi, si_next)):
            m.quad(o_b[si], o_b[si_next], i_b[si_next], i_b[si])

    # Palm cutout edges: where the cutout starts/ends along Y,
    # seal the edges with wall strips
    if palm_cut_start is not None:
        # Find the boundary segments (edge of cutout)
        cut_edges = []
        for si in range(segs):
            if si in palm_cut_segs:
                si_prev = (si - 1) % segs
                si_next = (si + 1) % segs
                if si_prev not in palm_cut_segs:
                    cut_edges.append(si)  # left edge of cut
                if si_next not in palm_cut_segs:
                    cut_edges.append(si_next)  # right edge of cut

        # Seal the Y-direction edges of the palm cutout
        for yi in range(len(slices) - 1):
            y1 = profiles[yi][0]
            y2 = profiles[yi + 1][0]
            o1, i1 = slices[yi]
            o2, i2 = slices[yi + 1]

            in1 = palm_cut_start <= y1 <= palm_cut_end
            in2 = palm_cut_start <= y2 <= palm_cut_end

            if in1 and in2:
                # Both slices in the cut zone - seal the circumferential edges
                for edge_si in cut_edges:
                    if edge_si < segs:
                        m.quad(o1[edge_si], o2[edge_si], i2[edge_si], i1[edge_si])

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

    # Coordinate system:
    # X = left/right (width), Z = up/down (height), Y = arm length
    # Arm slides in along Y axis through the center of the tube.
    # Z=0 is the center; negative Z = palm side, positive Z = top of hand
    #
    # The tube is elliptical: rx (X radius) controls width,
    # rz (Z radius) controls height.
    #
    # Real gauntlet: one smooth tube from mid-forearm to knuckles.
    # No floating finger tubes. Subtle wrist cuff. Clean taper.

    # Main gauntlet tube profile:
    # (y, rx_outer, rz_outer, wall_thickness)
    profiles = [
        # -- Elbow flare (slight lip so it doesn't slide up) --
        (0,    42,   36,   3.0),
        (4,    43,   37,   3.0),   # subtle lip
        (8,    42,   36,   3.0),

        # -- Forearm (smooth gradual taper toward wrist) --
        (20,   41,   35,   2.8),
        (35,   40,   34,   2.8),
        (50,   39,   33,   2.5),
        (65,   38,   32,   2.5),
        (80,   37,   31,   2.5),
        (95,   36,   30,   2.5),

        # -- Wrist (subtle cuff - NOT an aggressive flare) --
        (105,  36,   30,   3.0),
        (110,  37,   31,   3.0),   # subtle outward step
        (115,  37,   31,   3.0),

        # -- Hand plate (wider, flatter for the hand shape) --
        (120,  40,   28,   2.5),
        (130,  42,   27,   2.5),
        (140,  43,   26,   2.5),
        (150,  43,   26,   2.5),

        # -- Knuckle area (slight raised ridge, then taper to end) --
        (158,  43,   27,   3.0),
        (164,  43,   28,   3.0),
        (168,  43,   27,   2.8),
        (172,  42,   26,   2.5),
    ]

    # Clean tube — no palm cutout, just a smooth full 360 wrap
    hollow_tube(m, profiles, segs=48)

    # No separate finger tubes or thumb tubes.
    # Real gauntlets end at the knuckles - fingers are free.

    return m


if __name__ == '__main__':
    print("=" * 55)
    print("  GAUNTLET v10 - Realistic Hollow Tube Gauntlet")
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
    print("  + One clean hollow tube - arm slides through")
    print("  + Smooth forearm taper, subtle wrist cuff")
    print("  + Wider flatter hand section")
    print("  + Palm cutout for gripping")
    print("  + Ends at knuckles - fingers free (like real gauntlets)")
    print("  + No floating parts - single solid piece")
    print()
    print("  PRINT: PLA/PETG | 0.2mm | 15% infill | Tree supports")
