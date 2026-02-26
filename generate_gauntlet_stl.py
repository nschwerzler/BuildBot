"""
Gauntlet STL Generator — Creates a 3D-printable armored gauntlet.
Output: gauntlet.stl (binary STL, ready for Bambu Studio)
No external libraries needed — uses only Python stdlib.
"""
import struct
import math
import os

# ─── CONFIG ───────────────────────────────────────────────
OUTPUT_FILE = "gauntlet.stl"
SCALE = 1.0  # Adjust scale (1.0 = adult medium, ~27cm long)
SEGMENTS = 48  # Smoothness of curved surfaces

# ─── STL WRITER ───────────────────────────────────────────
class STLWriter:
    def __init__(self):
        self.triangles = []

    def add_tri(self, v1, v2, v3):
        """Add a triangle with auto-calculated normal."""
        # Calculate normal
        u = (v2[0]-v1[0], v2[1]-v1[1], v2[2]-v1[2])
        v = (v3[0]-v1[0], v3[1]-v1[1], v3[2]-v1[2])
        nx = u[1]*v[2] - u[2]*v[1]
        ny = u[2]*v[0] - u[0]*v[2]
        nz = u[0]*v[1] - u[1]*v[0]
        length = math.sqrt(nx*nx + ny*ny + nz*nz)
        if length > 0:
            nx /= length; ny /= length; nz /= length
        self.triangles.append((nx, ny, nz, v1, v2, v3))

    def add_quad(self, v1, v2, v3, v4):
        """Add a quad as two triangles."""
        self.add_tri(v1, v2, v3)
        self.add_tri(v1, v3, v4)

    def save(self, filename):
        """Write ASCII STL file (maximum compatibility)."""
        with open(filename, 'w') as f:
            f.write("solid gauntlet\n")
            for (nx, ny, nz, v1, v2, v3) in self.triangles:
                f.write(f"  facet normal {nx:.6e} {ny:.6e} {nz:.6e}\n")
                f.write(f"    outer loop\n")
                f.write(f"      vertex {v1[0]:.6e} {v1[1]:.6e} {v1[2]:.6e}\n")
                f.write(f"      vertex {v2[0]:.6e} {v2[1]:.6e} {v2[2]:.6e}\n")
                f.write(f"      vertex {v3[0]:.6e} {v3[1]:.6e} {v3[2]:.6e}\n")
                f.write(f"    endloop\n")
                f.write(f"  endfacet\n")
            f.write("endsolid gauntlet\n")
        print(f"  Wrote {len(self.triangles)} triangles to {filename} (ASCII format)")


# ─── GEOMETRY HELPERS ─────────────────────────────────────
def ring(cx, cy, cz, rx, ry, angle_start, angle_end, segments):
    """Generate points around an elliptical ring."""
    pts = []
    for i in range(segments + 1):
        t = angle_start + (angle_end - angle_start) * i / segments
        x = cx + rx * math.cos(t)
        y = cy + ry * math.sin(t)
        z = cz
        pts.append((x, y, z))
    return pts


def tube_section(stl, ring1, ring2):
    """Connect two rings of points with quads."""
    n = min(len(ring1), len(ring2)) - 1
    for i in range(n):
        stl.add_quad(ring1[i], ring1[i+1], ring2[i+1], ring2[i])


def cap_ring(stl, ring_pts, center, flip=False):
    """Fill a ring with a fan of triangles from center."""
    n = len(ring_pts) - 1
    for i in range(n):
        if flip:
            stl.add_tri(center, ring_pts[i+1], ring_pts[i])
        else:
            stl.add_tri(center, ring_pts[i], ring_pts[i+1])


# ─── GAUNTLET PROFILE ────────────────────────────────────
def generate_gauntlet():
    """
    Generate a wearable gauntlet with:
    - Forearm tube (tapered cylinder, open at elbow end)
    - Flared wrist cuff
    - Hand plate (wider, flatter)
    - Knuckle ridge
    - Four finger guards
    - Thumb guard
    - Raised armor ridges/details
    All dimensions in mm.
    """
    stl = STLWriter()
    S = SCALE
    segs = SEGMENTS

    # The gauntlet runs along the Z axis:
    #   Z=0   = elbow opening
    #   Z=270 = fingertip

    # ─── FOREARM SECTION (Z=0 to Z=150) ──────────────
    # Tapered tube, slightly oval cross-section
    # Opens wider at elbow, narrows toward wrist
    forearm_profiles = []
    forearm_steps = 12
    for step in range(forearm_steps + 1):
        t = step / forearm_steps
        z = t * 150 * S
        # Taper from elbow to wrist
        rx = (48 - t * 8) * S   # Width: 48mm at elbow → 40mm at wrist
        ry = (38 - t * 6) * S   # Height: 38mm at elbow → 32mm at wrist
        # Wall thickness via inner+outer rings
        wall = 3.0 * S
        outer = ring(0, 0, z, rx, ry, 0, 2*math.pi, segs)
        inner = ring(0, 0, z, rx - wall, ry - wall, 0, 2*math.pi, segs)
        forearm_profiles.append((outer, inner, z))

    # Connect forearm outer and inner surfaces
    for i in range(len(forearm_profiles) - 1):
        tube_section(stl, forearm_profiles[i][0], forearm_profiles[i+1][0])  # outer
        tube_section(stl, forearm_profiles[i+1][1], forearm_profiles[i][1])  # inner (reversed)

    # Cap the elbow opening (connect outer to inner ring)
    elbow_outer = forearm_profiles[0][0]
    elbow_inner = forearm_profiles[0][1]
    tube_section(stl, elbow_inner, elbow_outer)

    # ─── WRIST CUFF FLARE (Z=145 to Z=165) ───────────
    cuff_profiles = []
    cuff_steps = 6
    for step in range(cuff_steps + 1):
        t = step / cuff_steps
        z = (145 + t * 20) * S
        # Flare out, then back in
        flare = math.sin(t * math.pi) * 6 * S
        rx = (40 + flare) * S
        ry = (32 + flare * 0.7) * S
        wall = (3.0 + math.sin(t * math.pi) * 1.5) * S
        outer = ring(0, 0, z, rx, ry, 0, 2*math.pi, segs)
        inner = ring(0, 0, z, rx - wall, ry - wall, 0, 2*math.pi, segs)
        cuff_profiles.append((outer, inner, z))

    for i in range(len(cuff_profiles) - 1):
        tube_section(stl, cuff_profiles[i][0], cuff_profiles[i+1][0])
        tube_section(stl, cuff_profiles[i+1][1], cuff_profiles[i][1])

    # Connect forearm end to cuff start
    tube_section(stl, forearm_profiles[-1][0], cuff_profiles[0][0])
    tube_section(stl, cuff_profiles[0][1], forearm_profiles[-1][1])

    # ─── HAND PLATE (Z=165 to Z=210) ─────────────────
    hand_profiles = []
    hand_steps = 8
    for step in range(hand_steps + 1):
        t = step / hand_steps
        z = (165 + t * 45) * S
        # Hand is wider and flatter
        rx = (42 + math.sin(t * math.pi) * 8) * S    # Wider at knuckles
        ry = (25 + math.sin(t * math.pi) * 3) * S    # Flatter
        wall = 3.0 * S
        outer = ring(0, 0, z, rx, ry, 0, 2*math.pi, segs)
        inner = ring(0, 0, z, rx - wall, ry - wall, 0, 2*math.pi, segs)
        hand_profiles.append((outer, inner, z))

    for i in range(len(hand_profiles) - 1):
        tube_section(stl, hand_profiles[i][0], hand_profiles[i+1][0])
        tube_section(stl, hand_profiles[i+1][1], hand_profiles[i][1])

    # Connect cuff to hand
    tube_section(stl, cuff_profiles[-1][0], hand_profiles[0][0])
    tube_section(stl, hand_profiles[0][1], cuff_profiles[-1][1])

    # ─── KNUCKLE RIDGE (Z=200 to Z=215) ──────────────
    # A raised ridge across the knuckles (top side only)
    ridge_profiles = []
    ridge_steps = 6
    for step in range(ridge_steps + 1):
        t = step / ridge_steps
        z = (200 + t * 15) * S
        bump = math.sin(t * math.pi) * 5 * S
        pts = []
        for i in range(segs + 1):
            angle = 2 * math.pi * i / segs
            # Base ellipse matching hand section at this z
            base_rx = (50 + math.sin(t * math.pi) * (-2)) * S
            base_ry = (28 + math.sin(t * math.pi) * (-1)) * S
            x = base_rx * math.cos(angle)
            y = base_ry * math.sin(angle)
            # Add bump only on the top (y > 0)
            if y > 0:
                radial_bump = bump * (y / (base_ry if base_ry > 0 else 1))
                x *= (1 + radial_bump / base_rx * 0.3)
                y += radial_bump * 0.8
            pts.append((x, y, z))
        ridge_profiles.append(pts)

    for i in range(len(ridge_profiles) - 1):
        tube_section(stl, ridge_profiles[i], ridge_profiles[i+1])

    # ─── FINGER GUARDS (Z=210 to Z=255) ──────────────
    # Four finger channels
    finger_spacing = 18 * S
    finger_start_x = -1.5 * finger_spacing  # Center 4 fingers
    finger_radius = 7.5 * S
    finger_length = 45 * S
    finger_wall = 2.5 * S

    for fi in range(4):
        fcx = finger_start_x + fi * finger_spacing
        fcy = 0
        # Each finger is a half-tube (open on palm side, y < 0)
        finger_profiles_out = []
        finger_profiles_in = []
        fsteps = 8
        for step in range(fsteps + 1):
            t = step / fsteps
            fz = (210 + t * finger_length / S) * S
            # Taper finger slightly toward tip
            fr = finger_radius * (1.0 - t * 0.15)
            fr_in = (finger_radius - finger_wall) * (1.0 - t * 0.15)
            outer_pts = []
            inner_pts = []
            # Half-tube: only top half (0 to pi)
            for si in range(segs // 2 + 1):
                angle = math.pi * si / (segs // 2)
                ox = fcx + fr * math.cos(angle)
                oy = fcy + fr * math.sin(angle)
                outer_pts.append((ox, oy, fz))
                ix = fcx + fr_in * math.cos(angle)
                iy = fcy + fr_in * math.sin(angle)
                inner_pts.append((ix, iy, fz))
            finger_profiles_out.append(outer_pts)
            finger_profiles_in.append(inner_pts)

        for i in range(fsteps):
            tube_section(stl, finger_profiles_out[i], finger_profiles_out[i+1])
            tube_section(stl, finger_profiles_in[i+1], finger_profiles_in[i])
            # Side walls: connect outer edge to inner edge on both sides
            for side in [0, -1]:
                stl.add_quad(
                    finger_profiles_out[i][side],
                    finger_profiles_out[i+1][side],
                    finger_profiles_in[i+1][side],
                    finger_profiles_in[i][side]
                )

        # Cap fingertip
        tip_outer = finger_profiles_out[-1]
        tip_inner = finger_profiles_in[-1]
        tube_section(stl, tip_outer, tip_inner)

    # ─── THUMB GUARD (angled off to the side) ─────────
    thumb_cx = -55 * S
    thumb_cy = 5 * S
    thumb_radius = 9 * S
    thumb_wall = 2.5 * S
    thumb_length = 35 * S
    thumb_angle = math.radians(30)  # Angled outward

    thumb_profiles_out = []
    thumb_profiles_in = []
    tsteps = 7
    for step in range(tsteps + 1):
        t = step / tsteps
        tz = (180 + t * thumb_length / S) * S
        tx = thumb_cx + t * 15 * S * math.cos(thumb_angle)
        ty = thumb_cy
        tr = thumb_radius * (1.0 - t * 0.12)
        tr_in = (thumb_radius - thumb_wall) * (1.0 - t * 0.12)
        outer_pts = []
        inner_pts = []
        for si in range(segs // 2 + 1):
            angle = math.pi * si / (segs // 2)
            ox = tx + tr * math.cos(angle)
            oy = ty + tr * math.sin(angle)
            outer_pts.append((ox, oy, tz))
            ix = tx + tr_in * math.cos(angle)
            iy = ty + tr_in * math.sin(angle)
            inner_pts.append((ix, iy, tz))
        thumb_profiles_out.append(outer_pts)
        thumb_profiles_in.append(inner_pts)

    for i in range(tsteps):
        tube_section(stl, thumb_profiles_out[i], thumb_profiles_out[i+1])
        tube_section(stl, thumb_profiles_in[i+1], thumb_profiles_in[i])
        for side in [0, -1]:
            stl.add_quad(
                thumb_profiles_out[i][side],
                thumb_profiles_out[i+1][side],
                thumb_profiles_in[i+1][side],
                thumb_profiles_in[i][side]
            )
    # Thumb tip cap
    tube_section(stl, thumb_profiles_out[-1], thumb_profiles_in[-1])

    # ─── ARMOR RIDGE LINES (decorative raised lines) ──
    # Add 3 longitudinal ridges on top of forearm
    for ridge_angle in [-0.3, 0.0, 0.3]:
        ridge_pts_outer = []
        ridge_pts_inner = []
        for step in range(20):
            t = step / 19
            z = t * 150 * S
            base_rx = (48 - t * 8) * S
            base_ry = (38 - t * 6) * S
            cx = base_rx * math.cos(math.pi/2 + ridge_angle)
            cy = base_ry * math.sin(math.pi/2 + ridge_angle)
            # Raised ridge
            ridge_h = 2.0 * S
            ridge_w = 3.0 * S
            nx = math.cos(math.pi/2 + ridge_angle)
            ny = math.sin(math.pi/2 + ridge_angle)
            # Four corners of ridge cross-section
            p1 = (cx - ny*ridge_w/2, cy + nx*ridge_w/2, z)
            p2 = (cx + ny*ridge_w/2, cy - nx*ridge_w/2, z)
            p3 = (cx + nx*ridge_h + ny*ridge_w/2, cy + ny*ridge_h - nx*ridge_w/2, z)
            p4 = (cx + nx*ridge_h - ny*ridge_w/2, cy + ny*ridge_h + nx*ridge_w/2, z)
            ridge_pts_outer.append((p1, p2, p3, p4))

        for i in range(len(ridge_pts_outer) - 1):
            p1a, p2a, p3a, p4a = ridge_pts_outer[i]
            p1b, p2b, p3b, p4b = ridge_pts_outer[i+1]
            # Top face
            stl.add_quad(p4a, p3a, p3b, p4b)
            # Left face
            stl.add_quad(p1a, p4a, p4b, p1b)
            # Right face
            stl.add_quad(p3a, p2a, p2b, p3b)

    # ─── HAND PLATE TOP CAP ──────────────────────────
    # Close the gap between hand section end and finger starts
    # Simple plate connecting hand to finger bases
    hand_end_z = 210 * S
    plate_pts = []
    for i in range(segs + 1):
        angle = 2 * math.pi * i / segs
        rx = 50 * S
        ry = 28 * S
        x = rx * math.cos(angle)
        y = ry * math.sin(angle)
        plate_pts.append((x, y, hand_end_z))

    # Cap hand end with inner ring
    hand_end_inner = []
    for i in range(segs + 1):
        angle = 2 * math.pi * i / segs
        rx = (50 - 3.0) * S
        ry = (28 - 3.0) * S
        x = rx * math.cos(angle)
        y = ry * math.sin(angle)
        hand_end_inner.append((x, y, hand_end_z))

    tube_section(stl, hand_profiles[-1][0], plate_pts)
    tube_section(stl, hand_end_inner, hand_profiles[-1][1])

    return stl


# ─── MAIN ─────────────────────────────────────────────────
if __name__ == '__main__':
    print("=" * 50)
    print("  GAUNTLET STL GENERATOR")
    print("  For Bambu Studio / 3D Printing")
    print("=" * 50)
    print()
    print(f"  Scale: {SCALE}x")
    print(f"  Segments: {SEGMENTS}")
    print(f"  Output: {OUTPUT_FILE}")
    print()
    print("Generating gauntlet geometry...")

    stl = generate_gauntlet()

    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUTPUT_FILE)
    stl.save(output_path)

    file_size = os.path.getsize(output_path)
    print(f"\n  File size: {file_size / 1024:.1f} KB")
    print(f"  Triangles: {len(stl.triangles)}")
    print(f"\n  Done! Open '{OUTPUT_FILE}' in Bambu Studio.")
    print(f"  Full path: {output_path}")
    print()
    print("  Print tips:")
    print("  - Material: PLA or PETG")
    print("  - Layer height: 0.2mm")
    print("  - Infill: 15-20%")
    print("  - Supports: Yes (for finger guards)")
    print("  - Wall loops: 3-4 for strength")
