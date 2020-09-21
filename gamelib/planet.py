from panda3d import core
from direct.task.Task import Task

from .util import srgb_color


BASE_RADIUS = 3


class Planet:
    """
    Planet is divided up into six "sides", each of which is a grid of points.
    Each subdivision further extends the size of the grid, so each side goes
    from having 1 point, to 3, 9, 16, 25, 36, etc.
    """
    def __init__(self):
        self.root = core.NodePath("planet")
        self.sphere = loader.load_model("models/sphere.bam")
        self.sphere.reparent_to(self.root)

        self.sphere.set_color(srgb_color(0xffb2d4))

        csphere = core.CollisionSphere((0, 0, 0), 1)
        self.collide = self.root.attach_new_node(core.CollisionNode("collision"))
        self.collide.node().add_solid(csphere)
        self.collide.node().set_from_collide_mask(0)
        self.collide.node().set_into_collide_mask(1)

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

        self.left_eye = PlanetEye(self)
        self.left_eye.set_pos((-0.3, -1, 1))
        self.right_eye = PlanetEye(self)
        self.right_eye.set_pos((0.3, -1, 1))
        self.mouth = PlanetMouth(self)
        self.mouth.set_pos((0, -1.2, 1))

    async def grow(self):
        new_size = self.size + 2
        self.root.scaleInterval(0.5, BASE_RADIUS + new_size ** 1.5, blendType='easeInOut').start()
        await Task.pause(0.5)
        self.set_size(new_size)

    def set_size(self, size):
        self.size = size
        self.root.set_scale(BASE_RADIUS + self.size ** 1.5)

        for side in self.sides:
            side._size_changed(size) # pylint: disable=protected-access


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
        self.dots.set_color_scale((1, 0, 0, 0.5))
        self.dots.set_light_off(1)
        self.dots.set_bin('transparent', 10)
        self.dots.set_depth_write(False)
        self.dots.set_shader_off(1)


class PlanetObject:
    def __init__(self, planet):
        self.pivot = planet.root.attach_new_node("pivot")
        self.root = self.pivot.attach_new_node("root")
        self.root.set_pos(0, 1, 0)
        self.root.set_hpr(0, -90, 0)

    def get_pos(self):
        return self.pivot.get_quat().get_forward()

    def set_pos(self, pos):
        """Changes the position to the given vector, which is normalized
        (snapped to the planet surface)."""

        pos = core.Vec3(*pos).normalized()

        # Avoid gimbal lock by preserving the up vector near the poles, but
        # gradually lerping towards either (0, 0, 1) or (0, 0, -1) when nearing
        # the equator, so that the player doesn't get too disoriented.
        up_vector = self.pivot.get_quat().get_up()
        #equator_proximity = 1 - abs(pos.z)
        #equator_proximity *= 0.1
        #true_up_vector = core.Vec3(0, 0, 1 if up_vector[2] > 0 else -1)
        #up_vector = true_up_vector * equator_proximity + up_vector * (1 - equator_proximity)
        #up_vector.normalize()
        self.pivot.look_at(pos, up_vector)


class PlanetEye(PlanetObject):
    def __init__(self, planet):
        super().__init__(planet)

        self.model = loader.load_model("models/sphere.bam")
        self.model.set_scale(0.15/4, 0.15/4, 0.001/4)
        self.model.set_color((0, 0, 0, 1), 1)
        self.model.reparent_to(self.root)


class PlanetMouth(PlanetObject):
    def __init__(self, planet):
        super().__init__(planet)

        cardmaker = core.CardMaker("")
        cardmaker.set_frame(-0.1, 0.1, -0.1, 0.1)

        tex = loader.load_texture("textures/mouth.png")
        tex.wrap_u = core.Texture.WM_clamp
        tex.wrap_v = core.Texture.WM_clamp

        mat = core.Material()
        mat.base_color = (1, 1, 1, 1)

        self.model = self.root.attach_new_node(cardmaker.generate())
        self.model.set_material(mat)
        self.model.set_texture(tex)
        self.model.set_color((1, 1, 1, 1), 1)
        self.model.set_hpr(180, -90, 0)
        self.model.set_transparency(core.TransparencyAttrib.M_binary)
