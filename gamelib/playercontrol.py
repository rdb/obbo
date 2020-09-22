import math

from panda3d import core
from direct.interval.LerpInterval import *
from direct.interval.IntervalGlobal import *

from .player import Player
from .planet import PlanetObject
from .util import cfg_tuple


DEFAULT_POS = (0, -18, 10)
CAST_POS = (-12, 0, 7)
CAM_POS_SPEED = 70
AIM_SPEED_MULT = 25


class PlayerControl:
    def __init__(self, universe):
        self.traverser = core.CollisionTraverser()
        self.ray = core.CollisionRay()
        self.root = universe.root
        self.picker = base.cam.attach_new_node(core.CollisionNode("picker"))
        self.picker.node().add_solid(self.ray)
        self.picker.node().set_from_collide_mask(1)
        self.picker.node().set_into_collide_mask(0)

        self.picker_handler = core.CollisionHandlerQueue()
        self.traverser.add_collider(self.picker, self.picker_handler)

        self.player = Player(universe.planet)
        self.player.set_pos((0, 0, 1))
        self.crosshair = Crosshair()

        self.cursor_pos = None
        self.down_pos = None
        self.down_time = None
        self.is_hold = False
        self.cursor = Cursor(universe.planet)
        self.target = Cursor(universe.planet)

        self.cam_dummy = self.player.model.attach_new_node('cam')
        self.focus = self.player.model.attach_new_node('focus')
        self.target_mode = False
        self.mouse_delta = None
        self.mouse_last = None

        # FIXME: Not sure if we may need universe later again
        self.universe = universe

    def enter(self):
        base.cam.reparent_to(self.player.model_pos)
        self.toggle_cam_view()

    def exit(self):
        """Clean up?"""

    def toggle_cam_view(self, view='default'):
        pos = None
        if view == 'default':
            self.cam_dummy.reparent_to(self.player.model_pos)
            pos = DEFAULT_POS
            self.crosshair.hide()
            self.target_mode = False
        elif view == 'charging':
            self.cam_dummy.reparent_to(self.player.model)
            pos = CAST_POS
            self.crosshair.show()

        if pos is None:
            raise RuntimeError(f'Unknown view "{view}"')
        self.lerp_cam(cfg_tuple(f'cam-{view}-pos', pos))

    def lerp_cam(self, target_pos, view_offset=core.Vec3(0)):
        self.cam_dummy.set_pos(target_pos)
        self.focus.set_pos(self.player.model, view_offset)
        view_up = self.player.model.get_quat().get_up()
        self.cam_dummy.look_at(self.focus, view_up)

    def on_down(self):
        if self.cursor_pos:
            self.down_pos = self.cursor_pos
            self.down_time = 0

    def on_click(self):
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
            self.toggle_cam_view('charging')
            self.target_mode = True
        else:
            self.player.stop_charge()
            self.toggle_cam_view()
            self.start_cast()

    def start_cast(self):
        pass

    def update_cam(self, dt, mpos):
        delta = self.cam_dummy.get_pos(base.cam)
        if delta.length() > 0:
            offset = delta.normalized() * CAM_POS_SPEED * dt
            if offset.length() >= delta.length():
                base.cam.set_pos(self.cam_dummy, 0, 0, 0)
            else:
                base.cam.set_pos(base.cam, offset)
            base.cam.look_at(self.focus)
        elif mpos and self.target_mode:
            current = core.Vec2(mpos.x, mpos.y)
            if self.mouse_last:
                self.mouse_delta = current - self.mouse_last
                base.cam.set_h(base.cam, -self.mouse_delta.x * AIM_SPEED_MULT)
                base.cam.set_p(base.cam, self.mouse_delta.y * AIM_SPEED_MULT)
            self.mouse_last = current

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
                hold_threshold = core.ConfigVariableDouble('click-hold-threshold', 0.3).get_value()
                if self.down_time > hold_threshold:
                    self.set_aim(True)
                    self.is_hold = True
                    self.down_time = None
        else:
            self.cursor_pos = None
            self.cursor.model.hide()
            mpos = None

        self.update_cam(dt, mpos)
        self.player.update(dt)
        self.cursor.model.set_scale((5.0 + math.sin(globalClock.frame_time * 5)) / 3.0)


class Crosshair:
    def __init__(self):
        cardmaker = core.CardMaker("")
        cardmaker.set_frame(-2, 2, -2, 2)

        tex = loader.load_texture("textures/crosshair.png")
        tex.wrap_u = core.Texture.WM_clamp
        tex.wrap_v = core.Texture.WM_clamp

        mat = core.Material()
        mat.base_color = (1, 1, 1, 1)

        self.model = base.cam.attach_new_node(cardmaker.generate())
        self.model.set_material(mat)
        self.model.set_texture(tex)
        self.model.set_color((1, 1, 1, 1), 1)
        self.model.set_pos(0, 50, 8)
        #self.model.set_hpr(180, -90, 0)
        self.model.set_transparency(core.TransparencyAttrib.M_binary)
        #self.model.set_effect(core.CompassEffect.make(core.NodePath(), core.CompassEffect.P_all))

    def show(self):
        self.model.show()

    def hide(self):
        self.model.hide()


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
