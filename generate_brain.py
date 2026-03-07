"""
Brain Model Generator
=====================
Generates a 3D printable human brain model with:
  - Two hemispheres with realistic proportions
  - Sulci (grooves/folds) on the surface via noise displacement
  - Longitudinal fissure (gap between hemispheres)
  - Cerebellum (smaller bumpy structure at the back-bottom)
  - Brain stem extending downward

Output: brain.stl + brain.3mf
Dimensions: ~100mm wide, ~120mm long, ~80mm tall (printable on most beds)
"""
import math
import os
import random
import zipfile

OUTPUT_STL = "brain.stl"
OUTPUT_3MF = "brain.3mf"


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
            f.write("solid brain\n")
            for ia, ib, ic in self.tris:
                n = self._normal(ia, ib, ic)
                a, b, c = self.verts[ia], self.verts[ib], self.verts[ic]
                f.write(f"  facet normal {n[0]:.6e} {n[1]:.6e} {n[2]:.6e}\n")
                f.write("    outer loop\n")
                f.write(f"      vertex {a[0]:.6e} {a[1]:.6e} {a[2]:.6e}\n")
                f.write(f"      vertex {b[0]:.6e} {b[1]:.6e} {b[2]:.6e}\n")
                f.write(f"      vertex {c[0]:.6e} {c[1]:.6e} {c[2]:.6e}\n")
                f.write("    endloop\n  endfacet\n")
            f.write("endsolid brain\n")
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
            '  <metadata name="Application">BrainGen</metadata>\n'
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
            zf.writestr("3D/3dmodel.model", model_xml)
            zf.writestr("[Content_Types].xml", content_types)
            zf.writestr("_rels/.rels", rels)
        kb = os.path.getsize(path) // 1024
        print(f"  3MF: {len(self.tris)} tris, {kb} KB -> {path}")


# ── Noise function for brain wrinkles ──────────────────────

def _hash_int(n):
    """Simple integer hash for deterministic noise."""
    n = ((n >> 13) ^ n) * 1274126177
    n = ((n >> 13) ^ n) * 1911520717
    n = (n >> 13) ^ n
    return n

def _noise3d(x, y, z, seed=0):
    """Simple value noise in 3D for organic surface displacement."""
    ix, iy, iz = int(math.floor(x)), int(math.floor(y)), int(math.floor(z))
    fx, fy, fz = x - ix, y - iy, z - iz
    # Smoothstep
    fx = fx * fx * (3 - 2 * fx)
    fy = fy * fy * (3 - 2 * fy)
    fz = fz * fz * (3 - 2 * fz)

    def _val(i, j, k):
        h = _hash_int(i * 73856093 ^ j * 19349663 ^ k * 83492791 ^ seed)
        return (h & 0xFFFF) / 65535.0

    v000 = _val(ix, iy, iz)
    v100 = _val(ix+1, iy, iz)
    v010 = _val(ix, iy+1, iz)
    v110 = _val(ix+1, iy+1, iz)
    v001 = _val(ix, iy, iz+1)
    v101 = _val(ix+1, iy, iz+1)
    v011 = _val(ix, iy+1, iz+1)
    v111 = _val(ix+1, iy+1, iz+1)

    v00 = v000 * (1-fx) + v100 * fx
    v10 = v010 * (1-fx) + v110 * fx
    v01 = v001 * (1-fx) + v101 * fx
    v11 = v011 * (1-fx) + v111 * fx

    v0 = v00 * (1-fy) + v10 * fy
    v1 = v01 * (1-fy) + v11 * fy

    return v0 * (1-fz) + v1 * fz

def brain_noise(x, y, z):
    """Multi-octave noise simulating sulci/gyri wrinkles."""
    val = 0.0
    val += 0.50 * _noise3d(x * 1.0, y * 1.0, z * 1.0, seed=42)
    val += 0.25 * _noise3d(x * 2.3, y * 2.3, z * 2.3, seed=137)
    val += 0.15 * _noise3d(x * 4.7, y * 4.7, z * 4.7, seed=271)
    val += 0.10 * _noise3d(x * 9.1, y * 9.1, z * 9.1, seed=419)
    return val


# ── Brain geometry ─────────────────────────────────────────

def make_hemisphere(mesh, cx, cy, cz, rx, ry, rz, side, res_u=48, res_v=32):
    """
    Generate one brain hemisphere as a wrinkly half-ellipsoid.
    side: +1 for right hemisphere, -1 for left hemisphere.
    The flat face (medial) is on the side facing x=cx.
    """
    pts = []
    for iv in range(res_v + 1):
        v = iv / res_v  # 0..1
        phi = v * math.pi  # 0..pi (top to bottom)
        row = []
        for iu in range(res_u + 1):
            u = iu / res_u  # 0..1
            # theta goes from front to back to medial face
            if side > 0:
                theta = u * math.pi  # 0..pi (right hemisphere)
            else:
                theta = math.pi + u * math.pi  # pi..2pi (left hemisphere)

            # Base ellipsoid point
            sp = math.sin(phi)
            cp_ = math.cos(phi)
            st = math.sin(theta)
            ct = math.cos(theta)

            bx = rx * st * sp
            by = ry * cp_
            bz = rz * ct * sp

            # Brain shape modifications:
            # 1) Flatten the bottom slightly
            if by < -ry * 0.3:
                by = -ry * 0.3 + (by + ry * 0.3) * 0.4

            # 2) Frontal lobe bulge (front = +z direction)
            frontal = max(0, bz / rz)
            bx *= 1.0 + 0.08 * frontal
            by *= 1.0 + 0.05 * frontal

            # 3) Temporal lobe bulge (sides, lower)
            temporal = max(0, abs(bx) / rx - 0.3) * max(0, -by / ry)
            bx *= 1.0 + 0.15 * temporal

            # 4) Occipital lobe (back = -z) slight bump
            occipital = max(0, -bz / rz - 0.5)
            bz *= 1.0 + 0.1 * occipital

            # 5) Longitudinal fissure: flatten medial face
            # Make the inner face (near x=0) flatter
            medial_dist = abs(bx) / rx
            if medial_dist < 0.15:
                bx *= 0.6 + 0.4 * (medial_dist / 0.15)

            # 6) Wrinkle displacement via noise
            nx_ = (cx + bx) * 0.08
            ny_ = (cy + by) * 0.08
            nz_ = (cz + bz) * 0.08
            wrinkle = brain_noise(nx_, ny_, nz_) - 0.5  # centered around 0
            # Scale wrinkle: deeper grooves on top, shallower on bottom
            top_factor = max(0.2, (by + ry) / (2 * ry))
            disp = wrinkle * 3.0 * top_factor
            # Displace along the surface normal direction (approximate = radial)
            ln = math.sqrt(bx*bx + by*by + bz*bz)
            if ln > 0.01:
                bx += disp * bx / ln
                by += disp * by / ln
                bz += disp * bz / ln

            row.append((cx + bx, cy + by, cz + bz))
        pts.append(row)

    # Triangulate the grid
    for iv in range(res_v):
        for iu in range(res_u):
            a = pts[iv][iu]
            b = pts[iv][iu + 1]
            c = pts[iv + 1][iu + 1]
            d = pts[iv + 1][iu]
            mesh.quad(a, b, c, d)

    # Cap the flat medial face
    medial_pts = []
    for iv in range(res_v + 1):
        if side > 0:
            medial_pts.append(pts[iv][res_u])  # last column
        else:
            medial_pts.append(pts[iv][res_u])  # last column wraps to medial
    # Fan triangulate the medial face
    center = [0.0, 0.0, 0.0]
    for p in medial_pts:
        center[0] += p[0]
        center[1] += p[1]
        center[2] += p[2]
    n = len(medial_pts)
    center = (center[0]/n, center[1]/n, center[2]/n)
    for i in range(n - 1):
        if side > 0:
            mesh.tri(center, medial_pts[i+1], medial_pts[i])
        else:
            mesh.tri(center, medial_pts[i], medial_pts[i+1])


def make_cerebellum(mesh, cx, cy, cz, rx, ry, rz, res_u=32, res_v=20):
    """
    Generate the cerebellum: smaller bumpy structure at back-bottom of brain.
    Uses higher-frequency noise for the characteristic layered look.
    """
    pts = []
    for iv in range(res_v + 1):
        v = iv / res_v
        phi = v * math.pi
        row = []
        for iu in range(res_u + 1):
            u = iu / res_u
            theta = u * 2 * math.pi

            sp = math.sin(phi)
            cp_ = math.cos(phi)
            st = math.sin(theta)
            ct = math.cos(theta)

            bx = rx * st * sp
            by = ry * cp_
            bz = rz * ct * sp

            # Flatten top where it meets the cerebrum
            if by > ry * 0.3:
                by = ry * 0.3

            # Cerebellum ridges: horizontal lines (folia)
            ridge = math.sin(by * 3.0) * 0.8
            nx_ = (cx + bx) * 0.15
            nz_ = (cz + bz) * 0.15
            ridge += _noise3d(nx_, by * 0.2, nz_, seed=999) * 0.5
            ln = math.sqrt(bx*bx + by*by + bz*bz)
            if ln > 0.01:
                bx += ridge * bx / ln
                by += ridge * by / ln
                bz += ridge * bz / ln

            row.append((cx + bx, cy + by, cz + bz))
        pts.append(row)

    for iv in range(res_v):
        for iu in range(res_u):
            a = pts[iv][iu]
            b = pts[iv][iu + 1]
            c = pts[iv + 1][iu + 1]
            d = pts[iv + 1][iu]
            mesh.quad(a, b, c, d)


def make_brain_stem(mesh, cx, cy, cz, radius, length, res=16):
    """
    Generate the brain stem: a tapered cylinder extending downward.
    """
    rings = 12
    pts = []
    for ir in range(rings + 1):
        t = ir / rings
        y = cy - t * length
        # Taper: wider at top, narrower at bottom
        r = radius * (1.0 - 0.4 * t)
        # Slight bulge in the middle (pons)
        pons = math.sin(t * math.pi) * radius * 0.2
        r += pons
        ring = []
        for iu in range(res + 1):
            u = iu / res
            theta = u * 2 * math.pi
            x = cx + r * math.cos(theta)
            z = cz + r * math.sin(theta)
            ring.append((x, y, z))
        pts.append(ring)

    for ir in range(rings):
        for iu in range(res):
            a = pts[ir][iu]
            b = pts[ir][iu + 1]
            c = pts[ir + 1][iu + 1]
            d = pts[ir + 1][iu]
            mesh.quad(a, b, c, d)

    # Cap the bottom
    bottom_ring = pts[rings]
    center = (cx, cy - length, cz)
    for i in range(res):
        mesh.tri(center, bottom_ring[i+1], bottom_ring[i])


def build_brain():
    """Assemble the full brain model."""
    m = Mesh()

    # Brain dimensions (mm)
    # Full brain ~140mm long, ~100mm wide, ~80mm tall
    hemi_rx = 24.0   # half-width of each hemisphere (lateral)
    hemi_ry = 35.0   # half-height
    hemi_rz = 55.0   # half-length (front-to-back)

    # Gap between hemispheres (longitudinal fissure)
    gap = 2.0

    print("Generating right hemisphere...")
    make_hemisphere(m, gap/2 + hemi_rx * 0.15, 10, 0,
                    hemi_rx, hemi_ry, hemi_rz, side=+1)

    print("Generating left hemisphere...")
    make_hemisphere(m, -(gap/2 + hemi_rx * 0.15), 10, 0,
                    hemi_rx, hemi_ry, hemi_rz, side=-1)

    # Cerebellum: sits at back-bottom, behind and below the cerebrum
    cb_rx = 22.0
    cb_ry = 14.0
    cb_rz = 16.0
    print("Generating cerebellum...")
    make_cerebellum(m, 0, -18, -38, cb_rx, cb_ry, cb_rz)

    # Brain stem: extends downward from center-bottom
    print("Generating brain stem...")
    make_brain_stem(m, 0, -25, -30, radius=6.0, length=25.0)

    return m


def main():
    print("=== Brain Model Generator ===")
    print()
    m = build_brain()
    print()
    print(f"Total: {len(m.verts)} vertices, {len(m.tris)} triangles")
    print()
    m.save_stl(OUTPUT_STL)
    m.save_3mf(OUTPUT_3MF)
    print()
    print("Done! Files ready for slicing.")


if __name__ == "__main__":
    main()
