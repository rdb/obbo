import math

from panda3d import core

from .player import Player
from .planet import Planet, PlanetObject
from .asteroid import Asteroid
from .util import srgb_color
from .skybox import Skybox

HOLD_THRESHOLD = 0.5

class Universe:
    def __init__(self):
        base.set_background_color(srgb_color(0x595961))

        self.root = base.render.attach_new_node("universe")

        self.traverser = core.CollisionTraverser()

        self.skybox = Skybox(self.root)

        self.planet = Planet()
        self.planet.root.reparent_to(self.root)

        self.dlight = core.DirectionalLight("light")
        self.dlight.color = (0.5, 0.5, 0.5, 1)
        self.dlight.direction = (1, 1, 0)
        self.root.set_light(self.root.attach_new_node(self.dlight))

        self.alight = core.AmbientLight("light")
        self.alight.color = (0.5, 0.5, 0.5, 1)
        self.root.set_light(self.root.attach_new_node(self.alight))

        self.player = Player(self.planet)
        self.player.set_pos((0, 0, 1))

        self.asteroids = [Asteroid(self.planet) for _ in range(10)]

        # Temporary
        base.cam.reparent_to(self.player.model_pos)
        base.cam.set_pos((0, -15, 30))
        base.cam.look_at(self.player.model_pos)

        self.ray = core.CollisionRay()
        self.picker = base.cam.attach_new_node(core.CollisionNode("picker"))
        self.picker.node().add_solid(self.ray)
        self.picker.node().set_from_collide_mask(1)
        self.picker.node().set_into_collide_mask(0)

        self.picker_handler = core.CollisionHandlerQueue()
        self.traverser.add_collider(self.picker, self.picker_handler)

        self.cursor_pos = None
        self.down_pos = None
        self.down_time = None
        self.is_hold = False
        self.cursor = Cursor(self.planet)
        self.target = Cursor(self.planet)

    def on_down(self):
        if self.cursor_pos:
            self.down_pos = self.cursor_pos
            self.down_time = 0

    def on_click(self):
        #XXX move elsewhere?
        if self.cursor_pos and not self.is_hold:
            self.target.set_pos(self.down_pos)
            self.player.move_to(self.down_pos)
            self.down_pos = None
            self.down_time = None
        if self.is_hold:
            self.set_aim(False)
        self.is_hold = False

    def set_aim(self, value):
        if value:
            self.player.start_charge()
        else:
            self.player.stop_charge()

    def update(self, dt):
        if base.mouseWatcherNode.has_mouse():
            mpos = base.mouseWatcherNode.get_mouse()
            self.ray.set_from_lens(base.cam.node(), mpos.x, mpos.y)

            self.traverser.traverse(self.root)

            if self.picker_handler.get_num_entries() > 0:
                self.picker_handler.sort_entries()
                point = self.picker_handler.get_entry(0).get_surface_point(self.root)
                point.normalize()
                self.cursor_pos = point

                self.cursor.set_pos(self.cursor_pos)
                self.cursor.model.show()
            else:
                self.cursor.model.hide()

            if self.down_time is not None:
                self.down_time += dt
                if self.down_time > HOLD_THRESHOLD:
                    self.set_aim(True)
                    self.is_hold = True
                    self.down_time = None
        else:
            self.cursor_pos = None
            self.cursor.model.hide()

        self.player.update(dt)
        self.cursor.model.set_scale((5.0 + math.sin(globalClock.frame_time * 5)) / 3.0)


class Cursor(PlanetObject):
    def __init__(self, planet):
        super().__init__(planet)

        self.model = loader.load_model("models/sphere.bam")
        self.model.reparent_to(self.root)
        self.model.set_scale(0.1, 0.1, 0.0001)
        self.model.flatten_light()

        self.model.set_shader_off(1)
        self.model.set_light_off(1)
        self.model.set_alpha_scale(0.5)
        self.model.set_transparency(core.TransparencyAttrib.M_alpha)
        self.model.set_effect(core.CompassEffect.make(core.NodePath(), core.CompassEffect.P_scale))
