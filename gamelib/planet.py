from panda3d import core
from direct.task.Task import Task

from .util import srgb_color


base_radius = 3


class Planet:
    """
    Planet is divided up into six "sides", each of which is a grid of points.
    Each subdivision further extends the size of the grid, so each side goes
    from having 1 point, to 3, 9, 16, 25, 36, etc.
    """
    def __init__(self):
        self.root = core.NodePath("planet")
        self.sphere = loader.load_model("models/planet.blend")
        self.sphere.reparent_to(self.root)

        self.sphere.set_color(srgb_color(0xffb2d4))

        self.sides = [
            PlanetSide(self, (1, 0, 0)),
            PlanetSide(self, (0, 1, 0)),
            PlanetSide(self, (0, 0, 1)),
            PlanetSide(self, (-1, 0, 0)),
            PlanetSide(self, (0, -1, 0)),
            PlanetSide(self, (0, 0, -1)),
        ]

        self.set_size(1)

        #FIXME remove, just for debugging
        base.accept('space', self.grow)

    async def grow(self):
        new_size = self.size + 2
        self.root.scaleInterval(0.5, base_radius + new_size ** 1.5, blendType='easeInOut').start()
        await Task.pause(0.5)
        self.set_size(new_size)

    def set_size(self, size):
        self.size = size
        self.root.set_scale(base_radius + self.size ** 1.5)

        for side in self.sides:
            side._size_changed(size)


class PlanetSide:
    def __init__(self, planet, normal):
        self.root = planet.root.attach_new_node("side")
        self.root.look_at(normal)
        self.dots = None

    def _size_changed(self, size):
        # This is just for visualization, may remove later
        if self.dots:
            self.dots.remove_node()

        vdata = core.GeomVertexData('dots', core.GeomVertexFormat.get_v3(), core.Geom.UH_static)
        vdata.unclean_set_num_rows(size ** 2)

        writer = core.GeomVertexWriter(vdata, 'vertex')

        for x in range(size):
            for y in range(size):
                u = ((x * 2 + 1) / size - 1) * (1 - 0.3 / size)
                v = ((y * 2 + 1) / size - 1) * (1 - 0.3 / size)
                pos = core.Vec3(u, 1, v)
                pos.normalize()
                pos *= 1.001
                writer.set_data3(pos)

        del writer

        points = core.GeomPoints(core.Geom.UH_static)
        points.add_next_vertices(size ** 2)
        geom = core.Geom(vdata)
        geom.add_primitive(points)
        gnode = core.GeomNode("dots")
        gnode.add_geom(geom)

        self.dots = self.root.attach_new_node(gnode)
        self.dots.set_render_mode_thickness(0.01)
        self.dots.set_render_mode_perspective(True)
        self.dots.set_antialias(core.AntialiasAttrib.M_point)
        self.dots.set_color_scale((1, 1, 1, 0.5))
        self.dots.set_light_off(1)
        self.dots.set_bin('transparent', 10)


class PlanetObject:
    def __init__(self, planet):
        self.pivot = planet.root.attach_new_node("pivot")
        self.root = self.pivot.attach_new_node("root")
        self.root.set_pos(0, 0, 1)

    def set_pos(self, hpr):
        self.pivot.set_hpr(hpr)
