import math
import random

from panda3d import core
from direct.task.Task import Task
from direct.interval.LerpInterval import *
from direct.interval.IntervalGlobal import *

from .util import srgb_color


BASE_RADIUS = 1
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

        mat = core.Material("planet")
        mat.refractive_index = 1
        mat.base_color = (1, 0.238397, 0.238398, 1)
        mat.roughness = 1
        self.sphere.set_material(mat, 1)

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

        self.root.set_scale(BASE_RADIUS + 1)
        self.new_build_slots = 1
        self.build_slot_queue = []
        self.free_build_slots = 0
        self.set_size(1)

    def grow(self, player_face):
        new_size = self.size + 1
        self.new_build_slots = math.ceil(new_size * 2.4)  # Change factor to increase/decrease build_slots
        self.set_size(new_size, player_face)

    def set_size(self, size, player_face=None):
        self.size = size
        #self.root.set_scale(BASE_RADIUS + size ** 1.5)
        if size == 1:
            slots = [1]  # Also 5 would be a good choice, albeit more visible
        else:
            allowed_faces = [i for i in range(6)]
            allowed_faces.pop(player_face)
            random.shuffle(allowed_faces)
            slots = [allowed_faces[i % 5] for i in range(self.new_build_slots)]

        for i, side in enumerate(self.sides):
            side._size_changed(size, slots.count(i)) # pylint: disable=protected-access

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

        # Begin to sprout new cells when halfway done
        if growth >= 0.5:
            for side in self.sides:
                for row in side.grid:
                    for cell in row:
                        if cell.build_slot:
                            if cell not in self.build_slot_queue and not cell.sprouted:
                                self.build_slot_queue.append(cell)
                            continue
                        cell.sprout()

        return task.done if growth >= 1.0 else task.cont

    def sprout_build_slots(self, task):
        if self.size == 1 and self.free_build_slots == 1:
            return task.again
        if self.free_build_slots < 5 and self.build_slot_queue:
            self.build_slot_queue.pop(0).sprout()
            self.free_build_slots += 1
        if self.size == 5 and not self.build_slot_queue:
            return task.done
        return task.again


class PlanetSide:
    def __init__(self, planet, side):
        self.planet = planet
        self.root = planet.root.attach_new_node("side")
        self.side = side
        self.grid = []
        self.props = []

    def __grow_grid(self, build_slots):
        # No idea if this calculation works, it's a random guess at a formula
        # to roughly evenly distribute the new rows without spacing starting
        # buildings too far apart
        new_size = len(self.grid) + 1
        insert_at = ((len(self.grid) - 1) * 2) % new_size
        new_slots = []
        for row in self.grid:
            if build_slots > 0 and random.random() < 0.3:
                build_slots -= 1
                slot = AssetSlot(self.planet, True)
            else:
                slot = AssetSlot(self.planet)
            row.insert(insert_at, slot)
            new_slots.append(slot)

        build_slots = random.sample(list(range(new_size)), build_slots)
        new_row = [AssetSlot(self.planet, i in build_slots) for i in range(new_size)]
        self.grid.insert(insert_at, new_row)
        new_slots += new_row

        if new_size == 1:
            # Only crater 2 appears on the baby planet.
            pool = [
                "models/Environment/Craters/Crater2.bam",
            ]
        elif new_size == 2:
            # Only small objects
            pool = [
                "models/Environment/Bushes/Bush1.bam",
                "models/Environment/Bushes/Bush2.bam",
                "models/Environment/Flowers/Flower1.bam",
                "models/Environment/Flowers/Flower2.bam",
                "models/Environment/Grass/grass1.bam",
                "models/Environment/Grass/grass2.bam",
                "models/Environment/Rocks/mediumRock1.bam",
                "models/Environment/Rocks/mediumRock2.bam",
                "models/Environment/Rocks/smallRock1.bam",
                "models/Environment/Rocks/smallRock2.bam",
                "models/Environment/Rocks/smallRock3.bam",
                "models/Environment/Trees/Tree1.bam",
            ]
        elif new_size == 3:
            # Anything except mountains and some smallest objects
            pool = [
                "models/Environment/Bushes/Bush1.bam",
                "models/Environment/Rocks/mediumRock1.bam",
                "models/Environment/Rocks/mediumRock2.bam",
                "models/Environment/Rocks/smallRock1.bam",
                "models/Environment/Trees/Tree1.bam",
                "models/Environment/Trees/Tree2.bam",
                #"models/Environment/Trees/Tree3.bam",
                #"models/Environment/Trees/Tree4.bam",
            ]
        else:
            # Anything
            pool = [
                "models/Environment/Bushes/Bush1.bam",
                "models/Environment/Bushes/Bush2.bam",
                "models/Environment/Flowers/Flower1.bam",
                "models/Environment/Flowers/Flower2.bam",
                "models/Environment/Grass/grass1.bam",
                "models/Environment/Grass/grass2.bam",
                "models/Environment/Rocks/mediumRock1.bam",
                "models/Environment/Rocks/mediumRock2.bam",
                "models/Environment/Rocks/mountain1.bam",
                "models/Environment/Rocks/mountain2.bam",
                "models/Environment/Trees/Tree1.bam",
                "models/Environment/Trees/Tree2.bam",
                #"models/Environment/Trees/Tree3.bam",
                #"models/Environment/Trees/Tree4.bam",
            ]

        for slot in new_slots:
            slot.attach_model(random.choice(pool))

        # Also place a bunch of props
        #for n in range(new_size - 1):
        #    prop = PlanetProp(self.planet)
        #    prop.set_pos((random.random() - 0.5, random.random() - 0.5, random.random() - 0.5))
        #    self.props.append(prop)
        #    prop.sprout()

    def _size_changed(self, size, build_slots=0):
        while size > len(self.grid):
            self.__grow_grid(build_slots)

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
                slot = self.grid[x][y]
                if slot.sprouted:
                    slot.old_pos = slot.get_pos()
                else:
                    slot.old_pos = pos
                slot.new_pos = pos


class PlanetObject:
    def __init__(self, planet):
        self.pivot = planet.root.attach_new_node("pivot")
        self.root = self.pivot.attach_new_node("root")
        self.root.set_pos(0, 1, 0)
        self.root.set_hpr(0, -90, 0)

    def destroy(self):
        self.root.remove_node()

    def apply_pos(self):
        """Call after you changed the root position via some other means in
        order to make it work correctly."""

        if self.root.get_pos() != (0, 1, 0):
            self.set_pos(self.root.get_pos(self.pivot.parent))
            self.root.set_pos(0, 1, 0)

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


class PlanetProp(PlanetObject):
    def __init__(self, planet):
        super().__init__(planet)

        self.model = loader.load_model(random.choice([
            "models/Environment/Flowers/Flower1.bam",
            "models/Environment/Flowers/Flower2.bam",
            "models/Environment/Grass/grass1.bam",
            "models/Environment/Grass/grass2.bam",
        ]))
        self.model.set_effect(core.CompassEffect.make(core.NodePath(),
                              core.CompassEffect.P_scale))
        self.model.reparent_to(self.root)
        self.model.set_scale(0.0000000001)
        self.model.hide()
        self.sprouted = False

    def sprout(self):
        if self.sprouted:
            return

        self.model.show()
        self.model.scaleInterval(SPROUT_TIME, 0.25).start()
        self.sprouted = True


class AssetSlot(PlanetObject):

    _asset_cache = {}
    _slot_num = 0

    def __init__(self, planet, build_slot=False):
        super().__init__(planet)

        self.slot_node = self.root.attach_new_node("slot")
        self.slot_node.set_effect(core.CompassEffect.make(core.NodePath(),
                                  core.CompassEffect.P_scale))
        self.slot_node.hide()
        self.slot_node.set_scale(0.00000000001)

        model = core.NodePath('placeholder')
        model.reparent_to(self.slot_node)
        self.placeholder = model
        self.collider = None

        self.build_slot = build_slot
        self.building_placed = False
        self.sprouted = False
        self.slot_num = AssetSlot._slot_num

        self.planet = planet
        AssetSlot._slot_num += 1

    def attach_model(self, fn):
        self.placeholder.remove_node()

        potato_mode = panda3d.core.ConfigVariableBool('potato-mode', False).get_value()
        if not self.build_slot and potato_mode and random.randint(0, 1):
            return

        if self.build_slot:
            fn = "models/BuildSpaceSign.bam"

        if fn in self._asset_cache:
            cached_asset = self._asset_cache[fn]
        else:
            cached_asset = loader.load_model(fn)
            cached_asset.set_scale(0.25)
            cached_asset.clear_model_nodes()
            cached_asset.flatten_strong()
            self._asset_cache[fn] = cached_asset

        if self.build_slot:
            model = cached_asset.copy_to(self.slot_node)
            model.set_scale(0.8)
            model.set_z(0.6)
            Parallel(
                Sequence(
                    LerpPosInterval(model, 0.75, (0, 0, 0.8), startPos=(0, 0, 0.6), blendType='easeInOut'),
                    LerpPosInterval(model, 0.75, (0, 0, 0.6), startPos=(0, 0, 0.8), blendType='easeInOut'),
                ),
                LerpHprInterval(model, 1.5, (360, 0, 0),
                    startHpr=(0, 0, 0)),
            ).loop()
        else:
            model = cached_asset.instance_to(self.slot_node)
            model.set_h(random.random() * 360)

        self.model = model

        lower = fn.lower()
        mfilter = (
            'flower',
            'grass',
            'smallrock',
            'crater',
            'buildspacesign',
            'mediumrock',
        )
        if sum([i in lower for i in mfilter]) == 0:
            radius = 0.5
            if 'mountain' in lower:
                radius *= 4
            self.collider = self.slot_node.attach_new_node(core.CollisionNode("collider"))
            self.collider.node().add_solid(core.CollisionSphere((0, 0, 0.25), radius))
            self.collider.node().set_from_collide_mask(0b0000)
            self.collider.node().set_into_collide_mask(0b0010)
            #self.collider.show()
        elif 'buildspacesign' in lower:
            radius = 0.65
            self.collider = self.model.attach_new_node(core.CollisionNode("build_spot"))
            self.collider.node().add_solid(core.CollisionSphere((0, 0, -0.6), radius))
            self.collider.node().set_from_collide_mask(0b0000)
            self.collider.node().set_into_collide_mask(0b0001)
            self.collider.node().set_tag('pick_type', 'build_spot')
            self.collider.node().set_python_tag('asset', self)
            #self.collider.show()
        if self.collider:
            self.collider.set_pos(model.get_pos())

        face = model.find("**/Face/+GeomNode")
        if face:
            self.face = face
            self.randomize_face()
            # Change face every 3-9 seconds
            taskMgr.do_method_later(random.random() * 6 + 3, self.__cycle_face, 'cycle-face')

    def on_hover(self):
        if self.build_slot:
            self.model.scaleInterval(0.15, 1.0, blendType='easeInOut').start()
            self.model.colorScaleInterval(0.15, (2, 2, 2, 1), blendType='easeInOut').start()

    def on_blur(self):
        if self.build_slot:
            self.model.scaleInterval(0.15, 0.8, blendType='easeInOut').start()
            self.model.colorScaleInterval(0.15, (1, 1, 1, 1), blendType='easeInOut').start()

    def randomize_face(self):
        offset = random.choice([(0, 0), (0.5, 0), (0, 0.25), (0, 0.5), (0, 0.75)])
        self.face.set_shader_input('uv_shift', offset, priority=1)

    def __cycle_face(self, task):
        self.randomize_face()
        return task.again

    def sprout(self):
        if self.sprouted:
            return

        self.slot_node.show()
        self.slot_node.scaleInterval(SPROUT_TIME, 1.0).start()
        self.sprouted = True

    def build(self, building_name, time):
        if self.building_placed:
            raise RuntimeError('Cannot build here, slot already has a building')
        building = loader.loadModel("models/buildings.bam").find(f'**/{building_name}')
        self.collider.remove_node()
        self.model.remove_node()
        # self.model = core.NodePath(building_name)
        self.collider = building.attach_new_node(core.CollisionNode("collider"))
        self.collider.node().add_solid(core.CollisionSphere((0, 0, 0.25), 1))
        self.collider.node().set_from_collide_mask(0b0000)
        self.collider.node().set_into_collide_mask(0b0010)
        building.set_pos(0, 0, 0)
        building.reparent_to(self.slot_node)
        self.slot_node.set_scale(0.1)
        h = random.randrange(360) + 720
        h = random.choice((h, -h))
        self.slot_node.set_scale(0.000001)
        #Parallel(
        self.slot_node.scaleInterval(time, 1).start()
        #    self.slot_node.hprInterval(time, (h, 0, 0), blendType='easeInOut'),
        #).start()
        self.building_placed = True
        self.planet.free_build_slots -= 1
        messenger.send('built', [building_name])
