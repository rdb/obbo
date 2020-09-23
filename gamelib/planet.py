from panda3d import core
from direct.task.Task import Task

from .util import srgb_color


BASE_RADIUS = 3
GROWTH_TIME = 1.0
SPROUT_TIME = 1.0


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
            PlanetSide(self, '+x'),
            PlanetSide(self, '+y'),
            PlanetSide(self, '+z'),
            PlanetSide(self, '-x'),
            PlanetSide(self, '-y'),
            PlanetSide(self, '-z'),
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

    def grow(self):
        new_size = self.size + 1
        self.set_size(new_size)

    def set_size(self, size):
        self.size = size
        #self.root.set_scale(BASE_RADIUS + size ** 1.5)

        for side in self.sides:
            side._size_changed(size) # pylint: disable=protected-access

        self.root.scaleInterval(GROWTH_TIME, BASE_RADIUS + size ** 1.5, blendType='easeInOut').start()
        taskMgr.add(self.__resize)

    def __resize(self, task):
        # Take x seconds to grow fully
        growth = task.time / GROWTH_TIME
        growth = min(1.0, growth)

        for side in self.sides:
            for row in side.grid:
                for cell in row:
                    cell.set_pos(cell.new_pos * growth + cell.old_pos * (1 - growth))

        # Sprout new cells when done
        if growth >= 1.0:
            for side in self.sides:
                for row in side.grid:
                    for cell in row:
                        cell.sprout()

            return task.done
        else:
            return task.cont


class PlanetSide:
    def __init__(self, planet, side):
        self.planet = planet
        self.root = planet.root.attach_new_node("side")
        self.side = side
        self.grid = []

    def __grow_grid(self):
        # No idea if this calculation works, it's a random guess at a formula
        # to roughly evenly distribute the new rows without spacing starting
        # buildings too far apart
        new_size = len(self.grid) + 1
        insert_at = ((len(self.grid) - 1) * 2) % new_size
        for row in self.grid:
            row.insert(insert_at, BuildingSlot(self.planet))

        self.grid.insert(insert_at, [BuildingSlot(self.planet) for i in range(new_size)])

    def _size_changed(self, size):
        while size > len(self.grid):
            self.__grow_grid()

        for x in range(size):
            for y in range(size):
                u = ((x * 2 + 1) / size - 1) * (1 - 0.3 / size)
                v = ((y * 2 + 1) / size - 1) * (1 - 0.3 / size)

                if self.side == '+x':
                    pos = core.Vec3(1, u, v)
                elif self.side == '+y':
                    pos = core.Vec3(u, 1, v)
                elif self.side == '+z':
                    pos = core.Vec3(u, v, 1)
                elif self.side == '-x':
                    pos = core.Vec3(-1, u, v)
                elif self.side == '-y':
                    pos = core.Vec3(u, -1, v)
                elif self.side == '-z':
                    pos = core.Vec3(u, v, -1)

                pos.normalize()
                self.grid[x][y].old_pos = self.grid[x][y].get_pos()
                self.grid[x][y].new_pos = pos


class PlanetObject:
    def __init__(self, planet):
        self.pivot = planet.root.attach_new_node("pivot")
        self.root = self.pivot.attach_new_node("root")
        self.root.set_pos(0, 1, 0)
        self.root.set_hpr(0, -90, 0)

    def destroy(self):
        self.root.remove_node()

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


class BuildingSlot(PlanetObject):
    def __init__(self, planet):
        super().__init__(planet)

        model = loader.load_model("jack")
        model.reparent_to(self.root)
        model.set_scale(0.1)
        model.flatten_light()
        model.set_effect(core.CompassEffect.make(core.NodePath(),
                         core.CompassEffect.P_scale))
        self.model = model
        self.model.hide()
        self.model.set_scale(0.00000000001)
        self.sprouted = False

    def sprout(self):
        if self.sprouted:
            return

        self.model.show()
        self.model.scaleInterval(SPROUT_TIME, 1.0).start()
        self.sprouted = True
