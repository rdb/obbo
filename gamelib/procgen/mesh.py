"""
Provides the Mesh class to populate with verts/tris and export to a Node.
"""

from typing import Dict, List, Union

from panda3d.core import LMatrix4, Vec3, Vec4  # pylint: disable=no-name-in-module

from . import vertarr


ColorT = Union[Vec4, Vec3]


def compute_triangle_normal(pta:Vec3, ptb:Vec3, ptc:Vec3, normalized=True):
    """Return triangle face normal for ccw wound triangle pta, ptb, ptc"""
    # pylint: disable=invalid-name
    u = ptb - pta
    v = ptc - pta
    n = u.cross(v)
    if normalized:
        n.normalize()
    return n


class Mesh:
    """Representation of a mesh, exportable to a Panda3D Node."""
    def __init__(self, name='unnamed'):
        self._name = name
        self._points:Dict[Vec3, Point] = {}
        self._verts:Dict[int, Vertex] = {}
        self._tris:List[Triangle] = []
        self._vid = 0

    def add_vertex(self, pos:Vec3, color:ColorT):
        """Adds a Vertex to the mesh and returns the corresponding id."""
        if pos not in self._points:
            self._points[pos] = Point(pos, self)
        return self._points[pos].add_vertex(color)

    def add_triangle(self, verta, vertb, vertc):
        """Adds a Vertex to the mesh and returns the corresponding id."""
        self._tris.append(Triangle(self[verta], self[vertb], self[vertc]))

    def insert_vertex(self, pos:Vec3, color:ColorT):
        """Force duplication of vertices"""
        if color.num_components == 3:
            color = Vec4(*tuple(color), 1)
        self._verts[self._vid] = Vertex(self._vid, pos, color)
        self._vid += 1
        return self._vid - 1

    def _compute_smooth_normals(self):
        for point in self._points.values():
            normal = Vec3(0)
            for vert in point.vertices:
                for tris in vert.triangles:
                    normal += tris.normal_mag
                vert.normal = normal.normalized()

    def export(self, transform:LMatrix4 = None):
        """Returns a Node containing the mesh as Geom."""
        self._compute_smooth_normals()
        varr = vertarr.VertexArray()
        varr.set_num_rows(self._vid)
        mesh_to_varr:Dict[Vertex, int] = {}

        for vert in self._verts.values():
            if not vert.triangles:
                continue
            mesh_to_varr[vert] = varr.add_row(vert.pos, vert.normal, vert.color)
        for tri in self._tris:
            triangle = [mesh_to_varr[vert] for vert in tri]
            varr.add_triangle(*triangle)
        if transform is not None:
            varr.transform(transform)
        return varr.node()

    def __getitem__(self, item):
        if 0 <= item < self._vid:
            return self._verts[item]
        raise IndexError


class Point:
    """
    Unique point in 3D space that can hold multiple Vertex objs of different
    colors.
    """
    def __init__(self, pos:Vec3, mesh:Mesh):
        self.pos = pos
        self.mesh = mesh
        self._verts:Dict[ColorT, int] = {}

    def add_vertex(self, color:ColorT):
        """Add a Vertex to this point with color."""
        if color not in self._verts:
            self._verts[color] = self.mesh.insert_vertex(self.pos, color)
        return self._verts[color]

    @property
    def vertices(self):
        """Return all vertex ids contained by this Point."""
        return [self.mesh[i] for i in self._verts.values()]


class Vertex:
    """Representation of a single vertex."""
    def __init__(self, vid, pos:Vec3, color:ColorT=Vec4(1)):
        self.vid:int = vid
        self.pos:Vec3 = pos
        self.color:ColorT = color
        self.normal:Union[None, Vec3] = None
        self.triangles:List[Triangle] = []

    def add_triangle(self, triangle):
        """Add a Triangle to this Vertex."""
        # if triangle in self.triangles:
        #     raise ValueError('Triangle is already present in this Vertex')
        self.triangles.append(triangle)

    def remove_triangle(self, triangle):
        """Remove a prev. added Triangle from this Vertex."""
        try:
            self.triangles.pop(self.triangles.index(triangle))
        except ValueError:
            raise ValueError('Triangle is not present in this Vertex') from ValueError


class Triangle:
    """Triangle made up of 3 Vertex in CCW order."""
    def __init__(self, va:Vertex, vb:Vertex, vc:Vertex):
        self._va = va
        self._vb = vb
        self._vc = vc
        va.add_triangle(self)
        vb.add_triangle(self)
        vc.add_triangle(self)
        self._normal_mag = compute_triangle_normal(va.pos, vb.pos, vc.pos,
                                                   False)
        self._normal = self._normal_mag.normalized()

    @property
    def normal(self):
        """Return normalized face normal."""
        return self._normal

    @property
    def normal_mag(self):
        """Return face normal with magnitudes (useful for smooth normal comp)."""
        return self._normal_mag

    def __getitem__(self, item):
        # type: (int) -> Vertex
        if item == 0:
            return self._va
        elif item == 1:
            return self._vb
        elif item == 2:
            return self._vc
        else:
            raise IndexError
