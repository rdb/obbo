"""
Provides the VertexArray class for easier writing a Geom and exporting as Node.
"""

# pylint: disable=no-name-in-module
from panda3d.core import (Geom, GeomNode, GeomVertexData,GeomVertexFormat,
                          GeomVertexWriter, GeomTriangles, Vec4)
# pylint: enable=no-name-in-module


NORMAL_AS_COLOR = False


class VertexArray:
    """
    Holds all necessary objects to turn vertex/triangle data into a Geom/Node.
    """
    def __init__(self):
        self._vdata = GeomVertexData('vertdata', GeomVertexFormat.get_v3n3c4(),
            Geom.UH_static)

        self._vwriter = GeomVertexWriter(self._vdata, 'vertex')
        self._nwriter = GeomVertexWriter(self._vdata, 'normal')
        self._cwriter = GeomVertexWriter(self._vdata, 'color')
        self._prim = GeomTriangles(Geom.UH_static)

        self._vid = 0
        self.set_num_rows = self._vdata.set_num_rows

    def add_row(self, pos, normal, color):
        """Add a row of vertex data."""
        self._vwriter.add_data3(pos)
        self._nwriter.add_data3(normal)
        self._cwriter.add_data4(Vec4(*normal, 1) if NORMAL_AS_COLOR else color)
        self._vid += 1
        return self._vid - 1

    def add_triangle(self, verta, vertb, vertc):
        """Add a triangle primitive."""
        self._prim.add_vertices(verta, vertb, vertc)

    def transform(self, mat):
        """Set a transform matrix for the vertex data."""
        self._vdata.transform_vertices(mat)

    def node(self, name='unnamed node'):
        """Retrieve a Node containing the Geom created."""
        geom = Geom(self._vdata)
        geom.add_primitive(self._prim)
        node = GeomNode(name)
        node.add_geom(geom)
        return node
