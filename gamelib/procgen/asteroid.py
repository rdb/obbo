"""Generate a random asteroid mesh."""

from panda3d.core import Vec3, Vec4, LVecBase3i  # pylint: disable=no-name-in-module
import numpy as np

from . import draw, mesh, noise


mesh_drawer = draw.Draw()


def _triangle_line_connect(upper, lower, wrap_around, ccw):
    """Actual triangle calculation. Only done once per combination of args."""
    steps = max(upper, lower)
    upper_edges = np.linspace(0, upper, steps, endpoint=False, dtype=np.int32)
    lower_edges = np.linspace(0, lower, steps, endpoint=False, dtype=np.int32)
    if ccw:
        upper_edges = upper_edges[::-1]
        lower_edges = lower_edges[::-1]

    triangles = []
    for i in range(steps - 0 if wrap_around else steps - 1):
        ida = i
        idb = (i + 1) % steps
        u_edge = upper_edges[ida] != upper_edges[idb]
        l_edge = lower_edges[ida] != lower_edges[idb]

        if u_edge:
            triangles.append(((upper_edges[ida], upper_edges[idb]),
                              (lower_edges[ida],)))
            if l_edge:
                triangles.append(((upper_edges[idb],),
                                  (lower_edges[idb], lower_edges[ida])))
                continue

        if l_edge:
            triangles.append(((upper_edges[ida],),
                              (lower_edges[idb], lower_edges[ida])))
    return triangles


_triangle_line_cache = {}


def triangle_line_connect(upper, lower, wrap_around=True, ccw=True):
    """Used to connect two rows of vertices to triangles."""
    k = (upper, lower, wrap_around, ccw)
    if k not in _triangle_line_cache:
        _triangle_line_cache[k] = _triangle_line_connect(*k)
    return _triangle_line_cache[k]


def populate_triangles(msh, verts, wrap, ccw=True, chk_illegal=False):
    """
    Populates a mesh with triangles, assuming the verts reflect single and
    consecutive rows of the mesh.
    """
    for i in range(len(verts) - 1):
        upper = verts[i + 1]
        lower = verts[i]
        tri_ids = triangle_line_connect(len(upper), len(lower), wrap, ccw)
        for upr, low in tri_ids:
            triangle = [upper[v] for v in upr] + [lower[v] for v in low]
            if chk_illegal:
                pts = []
                for vert in triangle:
                    pos = msh[vert].pos
                    if pos in pts:
                        break
                    pts.append(pos)
                if len(pts) < 3:
                    continue
            msh.add_triangle(*triangle)


def generate(bounds:Vec3, color1:Vec3, color2:Vec3, noise_radius=2.0, seed=None):
    """
    Generate a random asteroid mesh.

    Args:
        bounds: bounding box to fit asteroid in
        color1: first color
        color2: second color
        noise_radius: optional sphere radius for noise coordinates
        seed: optional random seed for reproducability

    Returns:
        A Node containing the mesh.
    """
    msh = mesh.Mesh('asteroid')
    mesh_drawer.setup(Vec3(0), Vec3(0, 1, 0))
    seg_len = min(bounds) / 4
    segments = LVecBase3i(*map(int, bounds / seg_len)) + 1
    h_segments = (sum(segments.xy) - 2) * 3
    p_segments = h_segments // 2 + 1
    h_noise, p_noise, radius_noise, color_noise = noise \
        .asteroid_noise(h_segments, p_segments, noise_radius, seed)
    h_noise = [i * 0.75 for i in h_noise]
    p_noise = [i * 0.75 for i in p_noise]
    radius_noise = [i * 0.5 for i in radius_noise]
    color_noise = [1 / (i.max() - i.min()) * (i - i.min()) for i in color_noise]
    base_radius = np.average(radius_noise[0])
    top_radius = np.average(radius_noise[-1])
    base_color = np.average(color_noise[0])
    top_color = np.average(color_noise[-1])
    p_steps = np.linspace(-90, 90, p_segments)
    p_step = (p_steps[1] - p_steps[0]) * 0.9
    h_steps = np.linspace(0, 360, h_segments, endpoint=False)
    h_step = (h_steps[1] - h_steps[0]) * 0.9

    verts = []
    for pid, p in enumerate(p_steps):  # pylint: disable=invalid-name
        if abs(p) == 90:
            radius = base_radius if p == -90 else top_radius
            radius = bounds.z + radius * bounds.z
            mesh_drawer.set_hp_r(0, p, radius)
            factor = base_color if p == -90 else top_color
            color = factor * color1 + (1 - factor) * color2
            color = Vec4(*color, 1)
            verts.append([msh.add_vertex(mesh_drawer.world_pos, color)] * h_segments)
            continue
        twopi = np.linspace(0, 2 * np.pi, h_segments, endpoint=False)
        zipped = (h_steps, h_noise[pid], p_noise[pid], radius_noise[pid],
                  color_noise[pid], np.abs(np.cos(twopi)),
                  np.abs(np.sin(twopi)))
        verts.append([])
        sin_p = abs(np.sin(np.radians(p)))
        cos_p = abs(np.cos(np.radians(p)))
        rad_z = sin_p * bounds.z
        for h, ho, po, ro, c, cos_h, sin_h in zip(*zipped):  # pylint: disable=invalid-name
            rad_x = cos_h * bounds.x
            rad_y = sin_h * bounds.y
            rad_h = np.sqrt(rad_x ** 2 + rad_y ** 2) * cos_p
            radius = np.sqrt(rad_h ** 2 + rad_z ** 2)
            mesh_drawer.set_hp_r(h + ho * h_step, p + po * p_step, radius + radius * ro)
            color = c * color1 + (1 - c) * color2
            verts[-1].append(msh.add_vertex(mesh_drawer.world_pos, Vec4(*color, 1)))

    populate_triangles(msh, verts, wrap=True)
    return msh.export()
