"""
Simple 3D vertex drawing rig.
"""

from panda3d.core import NodePath, Vec3  # pylint: disable=no-name-in-module


class Draw:
    """A NodePath structure, rigged up to draw arbitrary shapes in 3D."""
    def __init__(self, debug:NodePath = None, dbg_shape:NodePath = None):
        self._world = NodePath('world')
        self._origin = self._world.attach_new_node('origin')
        self._orientation = self._origin.attach_new_node('orientation')
        self._orientation_offset = self._orientation.attach_new_node('o_offset')
        self._draw = self._orientation_offset.attach_new_node('draw')
        if debug is not None and dbg_shape is not None:
            self._world.reparent_to(debug)
            dbg_shape.copy_to(self._world)
            dbg_shape.copy_to(self._origin)
            dbg_shape.copy_to(self._orientation)
            dbg_shape.copy_to(self._orientation_offset)
            dbg_shape.copy_to(self._draw)
            self._world.clear_texture()
            self._world.set_color(Vec3(1, 0, 0))
            self._origin.clear_texture()
            self._origin.set_color(Vec3(0, 1, 0))
            self._orientation.clear_texture()
            self._orientation.set_color(Vec3(0, 0, 1))
            self._orientation_offset.clear_texture()
            self._orientation_offset.set_color(Vec3(1, 0, 1))
            self._draw.clear_texture()
            self._draw.set_color(Vec3(1, 1, 1))

    @property
    def world_pos(self):
        """Get the position of the draw node relative to the world node."""
        return self._draw.get_pos(self._world)

    @property
    def origin_pos(self):
        """Get the position of the draw node relative to the origin node."""
        return self._draw.get_pos(self._origin)

    @property
    def transform(self):
        """Get the transformation, applied to the orientation node."""
        return self._orientation.get_transform(self._world).get_mat()

    def setup(self, origin, direction):
        """Setup the rig."""
        self._orientation.set_pos_hpr(0, 0, 0, 0, 0, 0)
        self._orientation_offset.set_pos_hpr(0, 0, 0, 0, 0, 0)
        self._draw.set_pos_hpr(0, 0, 0, 0, 0, 0)
        self._origin.look_at(direction)
        self._origin.set_pos(origin)

    def set_hp_r(self, heading, pitch, radius):
        """
        Set heading and pitch of orientation node and set drawing distance
        (=radius).
        """
        self._orientation.set_hpr(heading, pitch, 0)
        self._draw.set_y(radius)

    def set_pos_hp_r(self, pos, heading, pitch, radius):
        """
        Set position, heading and pitch of orientation node and set drawing
        distance (=radius).
        """
        self._orientation.set_pos_hpr(*tuple(pos), heading, pitch, 0)
        self._draw.set_y(radius)
