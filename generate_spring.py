"""
Coil Spring — Bambu Studio / FDM Printable
===========================================
Generates a parametric coil spring as STL + 3MF.

Print tips:
  - Orient vertically (Z-axis = spring axis) — no supports needed
  - 0.2 mm layer height, 3 walls, 15% gyroid infill
  - PLA or PETG work great

Tweak the parameters below to resize the spring.
"""
import math
import os
import zipfile

# ── Spring Parameters ──────────────────────────────────────────
COIL_R      = 15.0   # Coil center-line radius (mm)
WIRE_R      = 2.0    # Wire cross-section radius (mm) — min 1.5 for FDM
COILS       = 5      # Number of full coils
PITCH       = 8.0    # Height gained per coil (mm)
STEPS       = 72     # Path steps per coil — higher = smoother helix
CROSS_SEGS  = 16     # Sides of the wire cross-section polygon

# ── Output ─────────────────────────────────────────────────────
OUT_DIR  = os.path.dirname(os.path.abspath(__file__))
OUT_3MF  = os.path.join(OUT_DIR, "spring.3mf")
OUT_STL  = os.path.join(OUT_DIR, "spring.stl")


# ── Mesh ───────────────────────────────────────────────────────
class Mesh:
    def __init__(self):
        self.verts = []
        self.tris  = []
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

    def floor_to_z0(self):
        """Shift mesh so lowest vertex sits at z = 0."""
        if not self.verts:
            return
        z_min = min(v[2] for v in self.verts)
        if abs(z_min) > 1e-6:
            self.verts = [(x, y, z - z_min) for x, y, z in self.verts]
            self._vmap = {k: i for i, k in enumerate(self.verts)}

    def save_stl(self, path):
        with open(path, 'w') as f:
            f.write("solid spring\n")
            for ia, ib, ic in self.tris:
                n = self._normal(ia, ib, ic)
                a, b, c = self.verts[ia], self.verts[ib], self.verts[ic]
                f.write(f"  facet normal {n[0]:.6e} {n[1]:.6e} {n[2]:.6e}\n")
                f.write("    outer loop\n")
                for p in (a, b, c):
                    f.write(f"      vertex {p[0]:.6e} {p[1]:.6e} {p[2]:.6e}\n")
                f.write("    endloop\n  endfacet\n")
            f.write("endsolid spring\n")
        kb = os.path.getsize(path) // 1024
        print(f"  STL  {len(self.tris):>6} tris  {kb} KB  ->  {path}")

    def save_3mf(self, path):
        vl = [f'          <vertex x="{x}" y="{y}" z="{z}"/>'
              for x, y, z in self.verts]
        tl = [f'          <triangle v1="{a}" v2="{b}" v3="{c}"/>'
              for a, b, c in self.tris]
        model = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<model unit="millimeter"'
            ' xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">\n'
            '  <metadata name="Application">SpringGen</metadata>\n'
            '  <resources>\n    <object id="1" type="model">\n      <mesh>\n'
            '        <vertices>\n' + '\n'.join(vl) + '\n        </vertices>\n'
            '        <triangles>\n' + '\n'.join(tl) + '\n        </triangles>\n'
            '      </mesh>\n    </object>\n  </resources>\n'
            '  <build>\n    <item objectid="1"/>\n  </build>\n</model>')
        ct = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
            '  <Default Extension="rels"'
            ' ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n'
            '  <Default Extension="model"'
            ' ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>\n'
            '</Types>')
        rels = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<Relationships'
            ' xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
            '  <Relationship Target="/3D/3dmodel.model" Id="rel0"'
            ' Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n'
            '</Relationships>')
        with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr('[Content_Types].xml', ct)
            zf.writestr('_rels/.rels', rels)
            zf.writestr('3D/3dmodel.model', model)
        kb = os.path.getsize(path) // 1024
        print(f"  3MF  {len(self.tris):>6} tris  {kb} KB  ->  {path}")


# ── Spring Geometry ────────────────────────────────────────────
def _frenet(t, R, ppr):
    """
    Frenet frame at helix parameter t.
      ppr  = pitch / (2π)   (rise per radian)
    Returns (position, tangent, normal, binormal) — all 3-tuples.
    """
    cos_t, sin_t = math.cos(t), math.sin(t)

    pos = (R * cos_t, R * sin_t, ppr * t)

    # Tangent (d pos / dt), normalised
    tx, ty, tz = -R * sin_t, R * cos_t, ppr
    tlen = math.sqrt(tx*tx + ty*ty + tz*tz)
    T = (tx/tlen, ty/tlen, tz/tlen)

    # Principal normal of the helix always points toward the Z-axis
    N = (-cos_t, -sin_t, 0.0)

    # Binormal = T × N
    B = (T[1]*N[2] - T[2]*N[1],
         T[2]*N[0] - T[0]*N[2],
         T[0]*N[1] - T[1]*N[0])

    return pos, T, N, B


def _ring(t, R, ppr, wr, segs):
    """Circle of `segs` vertices swept around the helix at parameter t."""
    pos, _, N, B = _frenet(t, R, ppr)
    pts = []
    for j in range(segs):
        a  = 2 * math.pi * j / segs
        ca, sa = math.cos(a), math.sin(a)
        ox = wr * (ca * N[0] + sa * B[0])
        oy = wr * (ca * N[1] + sa * B[1])
        oz = wr * (ca * N[2] + sa * B[2])
        pts.append((pos[0] + ox, pos[1] + oy, pos[2] + oz))
    return pts


def build_spring(mesh):
    ppr         = PITCH / (2 * math.pi)
    total_steps = COILS * STEPS

    # ── Sample rings along the entire helix ───────────────────
    rings = []
    for i in range(total_steps + 1):
        t = 2 * math.pi * i / STEPS
        rings.append(_ring(t, COIL_R, ppr, WIRE_R, CROSS_SEGS))

    # ── Tube surface — connect adjacent rings with quads ──────
    for i in range(total_steps):
        r0, r1 = rings[i], rings[i + 1]
        for j in range(CROSS_SEGS):
            k = (j + 1) % CROSS_SEGS
            # Winding: outward normals face away from helix axis
            mesh.quad(r0[j], r0[k], r1[k], r1[j])

    # ── End caps (flat disk closing off each wire end) ─────────
    pos_start = _frenet(0,                        COIL_R, ppr)[0]
    pos_end   = _frenet(2*math.pi*COILS,          COIL_R, ppr)[0]

    r_start = rings[0]
    r_end   = rings[-1]

    for j in range(CROSS_SEGS):
        k = (j + 1) % CROSS_SEGS
        # Start cap: normal points in -T direction (outward from wire start)
        mesh.tri(pos_start, r_start[k], r_start[j])
        # End cap: normal points in +T direction (outward from wire end)
        mesh.tri(pos_end,   r_end[j],   r_end[k])

    # Sit flat on print bed
    mesh.floor_to_z0()


# ── Main ───────────────────────────────────────────────────────
if __name__ == '__main__':
    outer_d  = 2 * (COIL_R + WIRE_R)
    height   = COILS * PITCH
    wire_d   = 2 * WIRE_R

    print("=== Coil Spring Generator ===")
    print(f"  Coils      : {COILS}")
    print(f"  Outer dia  : {outer_d:.1f} mm")
    print(f"  Wire dia   : {wire_d:.1f} mm")
    print(f"  Height     : {height:.1f} mm")
    print(f"  Pitch      : {PITCH:.1f} mm / coil")
    print(f"  Resolution : {STEPS} steps/coil x {CROSS_SEGS} cross-segs")
    print()

    mesh = Mesh()
    build_spring(mesh)

    mesh.save_stl(OUT_STL)
    mesh.save_3mf(OUT_3MF)

    print()
    print("Done! Open spring.3mf in Bambu Studio.")
    print("Suggested print settings:")
    print("  Layer height : 0.2 mm")
    print("  Walls        : 3")
    print("  Infill       : 15 % gyroid")
    print("  Material     : PLA or PETG")
