# pylint: disable=invalid-name
import math

from panda3d import core
from direct.fsm.FSM import FSM
from direct.interval.LerpInterval import *
from direct.interval.IntervalGlobal import *

from .player import Player
from .planet import PlanetObject
from .util import cfg_tuple


DEFAULT_POS = (0, -18, 10)
CAST_POS = (-12, 0, 7)
CAM_POS_SPEED = 70
AIM_SPEED_MULT = 50
CAM_ROTATE_SPEED = 5.0


class PlayerControl(FSM):
    def __init__(self, universe):
        super().__init__('Normal')
        self.traverser = core.CollisionTraverser()
        self.ray = core.CollisionRay()
        self.root = universe.root
        self.picker = base.cam.attach_new_node(core.CollisionNode("picker"))
        self.picker.node().add_solid(self.ray)
        self.picker.node().set_from_collide_mask(0b0001)
        self.picker.node().set_into_collide_mask(0b0000)

        self.picker_handler = core.CollisionHandlerQueue()
        self.traverser.add_collider(self.picker, self.picker_handler)

        self.player = Player(universe.planet)
        self.player.set_pos((0, 0, 1))
        self.crosshair = Crosshair()

        self.pusher = core.CollisionHandlerPusher()
        self.pusher.add_collider(self.player.collider, self.player.root)
        self.traverser.add_collider(self.player.collider, self.pusher)
        #self.traverser.show_collisions(render)

        self.bobber = base.loader.load_model('models/Environment/Rocks/smallRock1.bam')
        self.bobber.reparent_to(self.player.model)
        self.bobber.stash()
        bobbercol = core.CollisionNode('Bobber')
        bobbercol.add_solid(core.CollisionSphere(center=(0, 0, 0), radius=1.0))
        bobbercol.set_from_collide_mask(0b0100)
        bobbercol.set_into_collide_mask(0b0000)
        self.bobber_collider = self.bobber.attach_new_node(bobbercol)
        self.asteroid_handler = core.CollisionHandlerQueue()

        self.cursor_pos = None
        self.down_pos = None
        self.down_time = None
        self.is_hold = False
        self.cursor = Cursor(universe.planet)
        self.target = Cursor(universe.planet)

        self.cam_dummy = self.player.root.attach_new_node('cam')
        self.cam_dummy.set_effect(core.CompassEffect.make(core.NodePath(),
                                  core.CompassEffect.P_scale))
        self.cam_target_h = 0
        self.cam_target_p = 0
        self.focus = self.player.root.attach_new_node('focus')
        self.aim_mode = False
        self.mouse_delta = None
        self.mouse_last = None

        self.request('Normal')

        # FIXME: Not sure if we may need universe later again
        self.universe = universe

    def enter(self):
        base.camera.reparent_to(self.cam_dummy)
        base.camera.set_pos((0, -20, 20))
        base.camera.look_at(self.cam_dummy)

    def exit(self):
        """Clean up?"""

    def toggle_cam_view(self, view='default'):
        pos = None
        if view == 'default':
            self.cam_dummy.reparent_to(self.player.root)
            self.aim_mode = False
            self.crosshair.hide()
        elif view == 'charging':
            self.cam_dummy.reparent_to(self.player.model_pos)
            self.crosshair.show()
        else:
            raise RuntimeError(f'Unknown view "{view}"')

    def on_down(self):
        if self.cursor_pos:
            self.down_pos = self.cursor_pos
            self.down_time = 0

    def on_click(self):
        if self.state == 'Charge':
            self.request('Cast')

        if self.cursor_pos and not self.is_hold:
            if self.down_pos:
                self.target.set_pos(self.down_pos)
                self.player.move_to(self.down_pos)
            self.down_pos = None
            self.down_time = None
        self.is_hold = False

    def cancel(self):
        self.request('Normal')

    def enterNormal(self):
        self.crosshair.hide()
        self.toggle_cam_view()

    def updateNormal(self, dt):
        if base.mouseWatcherNode.has_mouse():
            mpos = base.mouseWatcherNode.get_mouse()
            self.ray.set_from_lens(base.cam.node(), mpos.x, mpos.y)

            self.cam_target_h = mpos.x * -10
            self.cam_target_p = mpos.y * -45

            self.traverser.traverse(self.root)

            # Make sure position is normalized, in case pusher acted on it
            self.player.apply_pos()

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
                    self.request('Charge')
                    self.is_hold = True
                    self.down_time = None
        else:
            self.cursor_pos = None
            self.cursor.model.hide()
            mpos = None

    def exitNormal(self):
        self.cursor.model.hide()

    def enterCharge(self):
        self.player.start_charge()
        self.toggle_cam_view('charging')
        self.cam_target_p = 45
        self.crosshair.show()

    def updateCharge(self, dt):
        if base.mouseWatcherNode.has_mouse():
            mpos = base.mouseWatcherNode.get_mouse()

            self.cam_target_h = mpos.x * -180
            self.cam_target_p = mpos.y * -45 + 45

        self.player.model.set_h(self.cam_dummy.get_h() + 45)

    def exitCharge(self):
        self.player.stop_charge()
        self.toggle_cam_view()
        self.crosshair.hide()

    def enterCast(self):
        # FIXME: Make proper mechanic, this is just a test
        self.bobber.unstash()
        self.bobber.set_pos((-1, 0, 1))
        self.traverser.add_collider(self.bobber_collider, self.asteroid_handler)
        direction = self.crosshair.model.get_pos(self.player.model).normalized()
        LerpPosInterval(self.bobber, 2.5, direction * 50, blendType='easeOut').start()
        #cam_pos = base.camera.get_pos(self.bobber)
        #base.camera.reparent_to(self.bobber)
        #base.camera.set_pos(cam_pos)
        def stop_cast(task):
            if self.state == 'Cast':
                self.request('Reel')
            return task.done
        base.taskMgr.do_method_later(1, stop_cast, 'stop_cast')

    def updateCast(self, _dt):
        self.traverser.traverse(self.universe.root)
        self.asteroid_handler.sort_entries()

        hit_asteroids = [
            i.into_node_path.get_python_tag('asteroid') for i in
            self.asteroid_handler.entries
            if i.into_node_path.has_python_tag('asteroid')
        ]

        if hit_asteroids:
            self.request('Reel', hit_asteroids[0])

    def exitCast(self):
        self.traverser.remove_collider(self.bobber_collider)
        self.bobber.stash()

    def enterReel(self, asteroid=None):
        if asteroid is not None:
            print('hit an asteroid!')
            asteroid.destroy()

    def updateReel(self, _dt):
        self.request('Normal')

    def update(self, dt):
        if base.mouseWatcherNode.has_mouse():
            mpos = base.mouseWatcherNode.get_mouse()
        else:
            mpos = None

        if self.state and hasattr(self, f'update{self.state}'):
            getattr(self, f'update{self.state}')(dt)

        self.player.update(dt)
        self.cursor.model.set_scale((5.0 + math.sin(globalClock.frame_time * 5)) / 3.0)

        cur_h = self.cam_dummy.get_h()
        dist = self.cam_target_h - cur_h
        dist = (dist + 180) % 360 - 180
        if abs(dist) > 0:
            sign = dist / abs(dist)
            self.cam_dummy.set_h(cur_h + dist * CAM_ROTATE_SPEED * dt)

        cur_p = self.cam_dummy.get_p()
        dist = self.cam_target_p - cur_p
        if abs(dist) > 0:
            sign = dist / abs(dist)
            self.cam_dummy.set_p(cur_p + dist * CAM_ROTATE_SPEED * dt)


class Crosshair:
    def __init__(self):
        cardmaker = core.CardMaker("")
        cardmaker.set_frame(-2, 2, -2, 2)

        tex = loader.load_texture("textures/crosshair.png")
        tex.wrap_u = core.Texture.WM_clamp
        tex.wrap_v = core.Texture.WM_clamp

        mat = core.Material()
        mat.base_color = (1, 1, 1, 1)

        self.model = base.camera.attach_new_node(cardmaker.generate())
        self.model.set_material(mat)
        self.model.set_texture(tex)
        self.model.set_color((1, 1, 1, 1), 1)
        self.model.set_pos(0, 50, 8)
        self.model.set_transparency(core.TransparencyAttrib.M_binary)
        self.model.hide()

    def show(self):
        self.model.show()

    def hide(self):
        self.model.hide()


class Cursor(PlanetObject):
    def __init__(self, planet):
        super().__init__(planet)

        self.model = loader.load_model("models/cursor.bam")
        self.model.reparent_to(self.root)

        self.model.set_shader_off(1)
        self.model.set_light_off(1)
        self.model.set_alpha_scale(0.5)
        self.model.set_transparency(core.TransparencyAttrib.M_alpha)
        self.model.set_effect(core.CompassEffect.make(core.NodePath(), core.CompassEffect.P_scale))
