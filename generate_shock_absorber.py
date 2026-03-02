"""
Coil-Spring Shock Absorber — Bambu Studio / FDM Printable
==========================================================
A shock absorber model with:
  - Bottom mounting plate
  - Main housing cylinder
  - Coil spring wrapped around the housing
  - Piston rod extending from the top
  - Top mounting plate

Prints as a single piece, no supports needed (vertical orientation).
Suggested: 0.2 mm layers, 3 walls, 15% infill, PLA or PETG.
"""
import math, os, zipfile

# ── Parameters ───────────────────────────────────────────────────────────────
BODY_R         = 10.0   # Housing outer radius (mm)
BODY_H         = 40.0   # Housing cylinder height

SHAFT_R        = 3.5    # Piston rod radius
SHAFT_EXTEND   = 22.0   # How far rod sticks up above housing

COLLAR_R       = 5.5    # Seal collar radius at rod exit
COLLAR_H       = 5.0    # Collar height

BOT_PLATE_R    = 14.0   # Bottom mounting plate radius
BOT_PLATE_H    = 4.0
TOP_PLATE_R    = 11.0   # Top mounting plate radius
TOP_PLATE_H    = 4.0

SPRING_COIL_R  = 12.8   # Spring coil center-line radius (clears housing by ~1mm)
SPRING_WIRE_R  = 1.8    # Wire cross-section radius
SPRING_COILS   = 5
SPRING_PITCH   = 7.0    # Rise per coil (mm)
SPRING_Z0      = 2.5    # Spring starts this far above body bottom

SEGS  = 44   # Cylinder polygon resolution
STEPS = 64   # Helix steps per coil
CS    = 14   # Wire cross-section segments

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_3MF = os.path.join(OUT_DIR, "shock_absorber.3mf")
OUT_STL = os.path.join(OUT_DIR, "shock_absorber.stl")


# ── Mesh ─────────────────────────────────────────────────────────────────────
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

    # ── Primitives ───────────────────────────────────────────────────────────

    def _circle_pts(self, cx, cy, z, r, segs):
        pts = []
        for i in range(segs):
            a = 2 * math.pi * i / segs
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a), z))
        return pts

    def disk(self, cx, cy, z, r, segs, flip=False):
        """Filled disk cap."""
        ctr = (cx, cy, z)
        pts = self._circle_pts(cx, cy, z, r, segs)
        for i in range(segs):
            j = (i + 1) % segs
            if flip:
                self.tri(ctr, pts[i], pts[j])
            else:
                self.tri(ctr, pts[j], pts[i])

    def cyl_wall(self, cx, cy, z0, z1, r, segs):
        """Open cylinder lateral surface (no caps)."""
        bot = self._circle_pts(cx, cy, z0, r, segs)
        top = self._circle_pts(cx, cy, z1, r, segs)
        for i in range(segs):
            j = (i + 1) % segs
            self.quad(bot[i], bot[j], top[j], top[i])

    def solid_cyl(self, cx, cy, z0, z1, r, segs):
        """Closed solid cylinder."""
        self.cyl_wall(cx, cy, z0, z1, r, segs)
        self.disk(cx, cy, z0, r, segs, flip=True)
        self.disk(cx, cy, z1, r, segs, flip=False)

    def tube_wall(self, cx, cy, z0, z1, r_out, r_in, segs):
        """Hollow cylinder tube (outer wall + inner wall + top/bottom annular rings)."""
        ob = self._circle_pts(cx, cy, z0, r_out, segs)
        ot = self._circle_pts(cx, cy, z1, r_out, segs)
        ib = self._circle_pts(cx, cy, z0, r_in,  segs)
        it_ = self._circle_pts(cx, cy, z1, r_in,  segs)
        for i in range(segs):
            j = (i + 1) % segs
            # Outer wall (normals out)
            self.quad(ob[i], ob[j], ot[j], ot[i])
            # Inner wall (normals in)
            self.quad(ib[j], ib[i], it_[i], it_[j])
            # Bottom ring
            self.quad(ob[j], ob[i], ib[i], ib[j])
            # Top ring
            self.quad(ot[i], ot[j], it_[j], it_[i])

    # ── Spring Helix ─────────────────────────────────────────────────────────

    def _frenet(self, t, R, ppr):
        cos_t, sin_t = math.cos(t), math.sin(t)
        pos = (R * cos_t, R * sin_t, ppr * t)
        tx, ty, tz = -R * sin_t, R * cos_t, ppr
        tlen = math.sqrt(tx*tx + ty*ty + tz*tz)
        T = (tx/tlen, ty/tlen, tz/tlen)
        N = (-cos_t, -sin_t, 0.0)
        B = (T[1]*N[2] - T[2]*N[1],
             T[2]*N[0] - T[0]*N[2],
             T[0]*N[1] - T[1]*N[0])
        return pos, T, N, B

    def _ring(self, t, R, ppr, wr, segs, z_offset=0):
        pos, _, N, B = self._frenet(t, R, ppr)
        pts = []
        for j in range(segs):
            a = 2 * math.pi * j / segs
            ca, sa = math.cos(a), math.sin(a)
            ox = wr * (ca * N[0] + sa * B[0])
            oy = wr * (ca * N[1] + sa * B[1])
            oz = wr * (ca * N[2] + sa * B[2])
            pts.append((pos[0]+ox, pos[1]+oy, pos[2]+oz+z_offset))
        return pts, pos

    def spring(self, coil_r, wire_r, coils, pitch, steps, cross_segs, z_offset=0):
        """Add a coil spring centered on Z axis."""
        ppr = pitch / (2 * math.pi)
        total = coils * steps
        rings = []
        centers = []
        for i in range(total + 1):
            t = 2 * math.pi * i / steps
            r, c = self._ring(t, coil_r, ppr, wire_r, cross_segs, z_offset)
            rings.append(r)
            centers.append(c)

        for i in range(total):
            r0, r1 = rings[i], rings[i+1]
            for j in range(cross_segs):
                k = (j + 1) % cross_segs
                self.quad(r0[j], r0[k], r1[k], r1[j])

        # End caps
        c0 = (centers[0][0], centers[0][1], centers[0][2] + z_offset)
        ce = (centers[-1][0], centers[-1][1], centers[-1][2] + z_offset)
        for j in range(cross_segs):
            k = (j + 1) % cross_segs
            self.tri(c0, rings[0][k],  rings[0][j])
            self.tri(ce, rings[-1][j], rings[-1][k])

    # ── Output ───────────────────────────────────────────────────────────────

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
        if not self.verts:
            return
        z_min = min(v[2] for v in self.verts)
        if abs(z_min) > 1e-6:
            self.verts = [(x, y, z - z_min) for x, y, z in self.verts]
            self._vmap = {k: i for i, k in enumerate(self.verts)}

    def save_stl(self, path):
        with open(path, 'w') as f:
            f.write("solid shock_absorber\n")
            for ia, ib, ic in self.tris:
                n = self._normal(ia, ib, ic)
                a, b, c = self.verts[ia], self.verts[ib], self.verts[ic]
                f.write(f"  facet normal {n[0]:.6e} {n[1]:.6e} {n[2]:.6e}\n")
                f.write("    outer loop\n")
                for p in (a, b, c):
                    f.write(f"      vertex {p[0]:.6e} {p[1]:.6e} {p[2]:.6e}\n")
                f.write("    endloop\n  endfacet\n")
            f.write("endsolid shock_absorber\n")
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
            '  <metadata name="Application">ShockAbsorberGen</metadata>\n'
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


# ── Build the shock absorber ──────────────────────────────────────────────────
def build(mesh):
    # z layout:
    #   -BOT_PLATE_H  .. 0          bottom mounting plate
    #   0             .. BODY_H     housing cylinder
    #   BODY_H        .. BODY_H+COLLAR_H  seal collar
    #   BODY_H+COLLAR_H .. top      piston rod
    #   top           .. top+TOP_PLATE_H  top mounting plate

    z0 = 0.0
    z_body_top   = z0 + BODY_H
    z_collar_top = z_body_top + COLLAR_H
    z_shaft_top  = z_collar_top + SHAFT_EXTEND
    z_plate_top  = z_shaft_top + TOP_PLATE_H

    # -- Bottom mounting plate --
    mesh.solid_cyl(0, 0, -BOT_PLATE_H, z0, BOT_PLATE_R, SEGS)

    # -- Housing cylinder --
    mesh.solid_cyl(0, 0, z0, z_body_top, BODY_R, SEGS)

    # -- Seal collar (slightly wider, smooth transition at rod exit) --
    mesh.solid_cyl(0, 0, z_body_top, z_collar_top, COLLAR_R, SEGS)

    # -- Piston rod --
    mesh.solid_cyl(0, 0, z_collar_top, z_shaft_top, SHAFT_R, SEGS)

    # -- Top mounting plate --
    mesh.solid_cyl(0, 0, z_shaft_top, z_plate_top, TOP_PLATE_R, SEGS)

    # -- Coil spring (wrapped around housing) --
    spring_h = SPRING_COILS * SPRING_PITCH
    mesh.spring(
        coil_r    = SPRING_COIL_R,
        wire_r    = SPRING_WIRE_R,
        coils     = SPRING_COILS,
        pitch     = SPRING_PITCH,
        steps     = STEPS,
        cross_segs= CS,
        z_offset  = SPRING_Z0,
    )

    mesh.floor_to_z0()


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    spring_h   = SPRING_COILS * SPRING_PITCH
    total_h    = BOT_PLATE_H + BODY_H + COLLAR_H + SHAFT_EXTEND + TOP_PLATE_H
    outer_dia  = 2 * max(BOT_PLATE_R, SPRING_COIL_R + SPRING_WIRE_R, TOP_PLATE_R)

    print("=== Shock Absorber Generator ===")
    print(f"  Total height   : {total_h:.1f} mm")
    print(f"  Outer dia      : {outer_dia:.1f} mm")
    print(f"  Housing dia    : {2*BODY_R:.1f} mm")
    print(f"  Shaft dia      : {2*SHAFT_R:.1f} mm")
    print(f"  Spring coils   : {SPRING_COILS} x {SPRING_PITCH:.0f} mm pitch")
    print(f"  Spring height  : {spring_h:.1f} mm")
    print()

    mesh = Mesh()
    build(mesh)

    mesh.save_stl(OUT_STL)
    mesh.save_3mf(OUT_3MF)

    print()
    print("Done! Open shock_absorber.3mf in Bambu Studio.")
    print("Print vertically, no supports needed.")
