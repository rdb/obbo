# pylint: disable=invalid-name
import math

from panda3d import core
from direct.fsm.FSM import FSM
from direct.interval.LerpInterval import *
from direct.interval.IntervalGlobal import *
from direct.showbase.DirectObject import DirectObject

from .player import Player
from .planet import PlanetObject
from .util import cfg_tuple
from .pieMenu import PieMenu, PieMenuItem


CAM_ROTATE_SPEED = 4.0
CAM_CAST_X_SENSITIVITY = 1.0
CAM_START_HEADING = 180 + 45
SHIP_POSITION = (0.364267, -0.857099, 0.364267)

# How long it takes to reach maximum charge
CHARGE_MAX_TIME = 2.0

BOBBER_SPIN_SPEED = 0.1
MAGNET_RADIUS = 1.8

# How much distance Obbo keeps from buildings while building
BUILD_DIST = 1.0

# How long Obbo takes to build something, currently length of building animation
BUILD_TIME = 2.25

CAST_TIME = 1.0
CAST_MIN_DISTANCE = 3.0
CAST_MAX_DISTANCE = 15.0

MAGNET_SNAP_TIME = 0.15

REEL_SPEED = 8.0

# How close the bobber can get to Obbo before ending the reel
REEL_MIN_DISTANCE = 0.8

assert CAM_CAST_X_SENSITIVITY > 0.5


class PlayerControl(FSM, DirectObject):
    def __init__(self, universe):
        FSM.__init__(self, 'Normal')
        DirectObject.__init__(self)
        self.universe = universe

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
        self.player.model.set_h(180)
        self.player.root.hide()
        self.crosshair = Crosshair()

        self.pusher = core.CollisionHandlerPusher()
        self.pusher.add_collider(self.player.collider, self.player.root)
        self.traverser.add_collider(self.player.collider, self.pusher)
        #self.traverser.show_collisions(render)

        self.bobber = base.loader.load_model('models/bobber.bam')
        self.bobber.reparent_to(self.player.model)
        self.bobber.set_scale(0.05)
        self.bobber.flatten_light()
        self.bobber.stash()
        self.magnet_snap_point = core.Point3(0, 1.6, 0)
        bobbercol = core.CollisionNode('Bobber')
        bobbercol.add_solid(core.CollisionSphere(center=(-0.3, 1.2, 0), radius=MAGNET_RADIUS))
        bobbercol.add_solid(core.CollisionSphere(center=(0.3, 1.2, 0), radius=MAGNET_RADIUS))
        bobbercol.set_from_collide_mask(0b0100)
        bobbercol.set_into_collide_mask(0b0000)
        self.bobber_collider = self.bobber.attach_new_node(bobbercol)
        # self.bobber_collider.show()
        self.asteroid_handler = core.CollisionHandlerQueue()

        # Create fishing line.
        vdata = core.GeomVertexData("line", core.GeomVertexFormat.get_v3(), core.Geom.UH_stream)
        vdata.set_num_rows(2)
        lines = core.GeomLines(core.Geom.UH_static)
        lines.add_next_vertices(2)
        geom = core.Geom(vdata)
        geom.add_primitive(lines)
        self.line = self.player.root.attach_new_node(core.GeomNode('line'))
        self.line.node().add_geom(geom)
        self.line.stash()
        self.line.set_shader_off(1)
        self.line.node().set_bounds(core.OmniBoundingVolume())
        self.line.node().set_final(True)
        self.line.set_render_mode_thickness(2)
        self.line.set_antialias(core.AntialiasAttrib.M_line)

        self.cursor_pos = None
        self.cursor_asset_slot = None
        self.pie_menu = None
        self.down_pos = None
        self.down_time = None
        self.cursor = Cursor(universe.planet)
        self.target = Cursor(universe.planet)
        self.target.root.hide()
        self.target_pos = None

        self.cam_dummy = self.player.root.attach_new_node('cam')
        self.cam_dummy.set_effect(core.CompassEffect.make(core.NodePath(),
                                  core.CompassEffect.P_scale))
        self.cam_dummy.set_h(CAM_START_HEADING)
        self.cam_target_h = 0
        self.cam_target_p = 0
        self.focus = self.player.root.attach_new_node('focus')
        self.aim_mode = False
        self.mouse_delta = None
        self.mouse_last = None
        self.catch = None

        confine_mouse = core.ConfigVariableBool('confine-mouse', False).get_value()
        if confine_mouse:
            self.default_mouse_mode = core.WindowProperties.M_confined
        else:
            self.default_mouse_mode = core.WindowProperties.M_absolute

        props = core.WindowProperties()
        props.set_cursor_hidden(False)
        props.set_mouse_mode(self.default_mouse_mode)
        base.win.request_properties(props)
        base.messenger.send("reset_cursor")

        self.player.charge_ctr.play_rate = (self.player.charge_ctr.num_frames / self.player.charge_ctr.frame_rate) / CHARGE_MAX_TIME

        self.ship_root = self.universe.planet.root.attach_new_node("ship_root")
        ship_model = loader.load_model("models/ship.bam")
        self.ship = ship_model.find("**/ship")
        self.ship.clear_transform()
        self.ship.set_scale(0.2)

        self.crashed_ship = CrashedShip(self.universe.planet)
        self.crashed_ship.root.hide()
        self.crashed_ship.set_pos(self.crashed_ship.new_pos)
        self.universe.planet.sides[4].grid[0][0].destroy()
        self.universe.planet.sides[4].grid[0][0] = self.crashed_ship

        self.request('Intro')

        if core.ConfigVariableBool('space-to-grow', False).get_value():
            base.accept('space', self.grow)
        self.grown = 0
        base.accept('planet_grow', self.grow)

        self.profile_mode = panda3d.core.ConfigVariableBool('profile-mode', False).get_value()
        if self.profile_mode:
            for i in range(4):
                self.grow()

        sfx = [
            "menu_accept",
            "menu_hover",
            "menu_spam",
            "astroid_attaches",
            "astroid_collected",
            "building_placed",
            "catched_nothing",
            "obbo_build",
            "obbo_cast",
            "obbo_charge",
            "obbo_reel_in",
            "obbo_walk",
            "planet_grows",
        ]
        self.sfx = {}
        for sfx_name in sfx:
            self.sfx[sfx_name] = loader.load_sfx("sfx/"+sfx_name+".wav")
        self.sfx["obbo_walk"].set_loop(True)
        self.sfx["menu_spam"].set_volume(0.4)

    def enterIntro(self):
        self.ship.reparent_to(self.ship_root)

        base.camera.reparent_to(self.cam_dummy)
        base.camera.set_pos((0, -30, 30))
        base.camera.look_at(self.cam_dummy)

        self.player.set_pos((-0.235157, -0.874935, 0.42331))
        self.player.model.set_h(45)

        skip_main_menu = panda3d.core.ConfigVariableBool('skip-main-menu', False).get_value()
        if skip_main_menu:
            return

        sfx = loader.load_sfx("sfx/crash.wav")
        if sfx:
            sfx.play()

        base.camera.set_pos((0, -60, 60))

        self.ship.set_pos(core.Point3(SHIP_POSITION) * 30)
        self.ship.look_at(SHIP_POSITION)
        self.ship.set_r(-60)
        self.ship.posInterval(3.0, SHIP_POSITION).start()
        base.transitions.setFadeColor(1, 1, 1)
        Sequence(
            Wait(2.85),
            base.transitions.getFadeOutIval(0.1),
            Wait(1.0),
            Func(self.request, 'Normal'),
        ).start()

    def updateIntro(self, dt):
        skip_main_menu = panda3d.core.ConfigVariableBool('skip-main-menu', False).get_value()
        if skip_main_menu:
            self.request('Normal')

    def exitIntro(self):
        self.ship.detach_node()
        self.crashed_ship.root.show()
        self.player.root.show()
        base.transitions.fadeIn(2.0)
        base.camera.set_pos((0, -30, 30))

        taskMgr.do_method_later(1, self.universe.planet.sprout_build_slots, 'bs_spawner')

    def grow(self):
        ppos = list(self.player.get_pos())
        offset = 0
        idx = None
        current_max = -1
        for i, val in enumerate(ppos):
            if abs(val) > current_max:
                idx = i
                current_max = abs(val)
                if val > 0:
                    offset = 0
                else:
                    offset = 3
        player_face = idx + offset
        self.universe.planet.grow(player_face)
        self.grown += 1
        if self.grown >= 4:
            base.ignore('space')  # FIXME: remove before release
            base.ignore('planet_grow')
        else:
            self.sfx["planet_grows"].play()


        self.bobber_collider.set_scale(max(1, self.universe.planet.size * 0.6))

    def exit(self):
        """Clean up?"""

    def toggle_cam_view(self, view='default'):
        if view == 'default':
            self.cam_dummy.reparent_to(self.player.root)
            self.aim_mode = False
            self.crosshair.hide()
        elif view == 'charging':
            self.cam_dummy.reparent_to(self.player.model_pos)
            self.crosshair.show()
        else:
            raise RuntimeError(f'Unknown view "{view}"')

    def on_mouse_down(self):
        if self.cursor_pos:
            self.down_pos = self.cursor_pos
        self.down_time = globalClock.frame_time

        if self.state == 'Cast' and not self.cursor_asset_slot:
            self.player.reel_ctr.play()
            self.sfx["obbo_reel_in"].play()
        elif self.state == 'Build' and not self.cursor_asset_slot:
            self.request('Normal')

    def on_mouse_up(self):
        if self.down_time is None:
            return

        if self.cursor_asset_slot and self.state == 'Normal':
            self.request('Build', self.cursor_asset_slot)
            self.cursor_asset_slot.on_blur()
            self.cursor_asset_slot = None

        elif self.state == 'Cast':
            self.player.reel_ctr.stop()
            self.sfx["obbo_reel_in"].stop()

        elif self.state == 'Charge':
            time = globalClock.frame_time - self.down_time
            self.request('Cast', time / CHARGE_MAX_TIME)

        self.down_time = None

        if self.cursor_pos and self.state == 'Normal':
            if self.down_pos:
                self.target.set_pos(self.down_pos)
                self.target.root.show()
                self.target_pos = core.Vec3(*self.down_pos)
                self.target_pos.normalize()
                if not self.player.walk_ctr.is_playing():
                    self.player.walk_ctr.loop('walk')
            self.down_pos = None

    def cancel(self):
        self.sfx["catched_nothing"].play()
        self.request('Normal')

    def enterNormal(self):
        self.crosshair.hide()
        self.toggle_cam_view()
        self.bobber.stash()
        self.line.stash()
        self.player.reel_ctr.stop()
        self.player.idle_ctr.loop(True)

        self.accept('mouse1', self.on_mouse_down)
        self.accept('mouse1-up', self.on_mouse_up)

        # Interrupt mouse hold if we just came in here holding the mouse,
        # so that we don't re-cast the line right away.
        self.down_time = None

    def updateNormal(self, dt):
        if self.target_pos is not None:
            if not self.sfx["obbo_walk"].status() == self.sfx["obbo_walk"].PLAYING:
                self.sfx["obbo_walk"].play()
            if self.player.move_toward(self.target_pos, dt):
                # Arrived.
                self.sfx["menu_spam"].play()
                self.sfx["obbo_walk"].stop()
                self.target_pos = None
                self.target.root.hide()
        else:
            if not self.player.walk_ctr.playing and not self.player.idle_ctr.playing:
                self.player.idle_ctr.loop(True)

        if base.mouseWatcherNode.has_mouse():
            mpos = base.mouseWatcherNode.get_mouse()
            self.ray.set_from_lens(base.cam.node(), mpos.x, mpos.y)

            if self.profile_mode:
                self.cam_target_h = 0
                self.cam_target_p = -40
            else:
                self.cam_target_h = mpos.x * -10
                self.cam_target_p = mpos.y * -45

            self.traverser.traverse(self.root)

            # Make sure position is normalized, in case pusher acted on it
            self.player.apply_pos()

            if self.picker_handler.get_num_entries() > 0:
                self.picker_handler.sort_entries()
                point = self.picker_handler.get_entry(0).get_surface_point(self.root)
                point.normalize()
                nd = self.picker_handler.get_entry(0).get_into_node_path().node()
                pick_type = nd.get_tag('pick_type')

                if pick_type == 'build_spot':
                    # TODO: I'm not sure why sort_entries doesn't sort by closest,
                    # maybe with more insight into the picker_handler can improve this?
                    assets = []
                    for i in range(self.picker_handler.get_num_entries()):
                        nd = self.picker_handler.get_entry(i).get_into_node_path().node()
                        if nd.get_tag('pick_type') == 'build_spot':
                            assets.append(nd.get_python_tag('asset'))
                    asset = None
                    min_dist = float('inf')
                    for i in assets:
                        dist = (point - i.get_pos()).length()
                        if dist < min_dist:
                            min_dist = dist
                            asset = i

                    if self.cursor_asset_slot != asset:
                        asset.on_hover()
                    self.cursor_asset_slot = asset
                    self.cursor_pos = None
                    self.cursor.model.hide()
                else:
                    if self.cursor_asset_slot:
                        self.cursor_asset_slot.on_blur()
                        self.cursor_asset_slot = None
                    self.cursor_pos = point
                    self.cursor.set_pos(self.cursor_pos)
                    self.cursor.model.show()
            else:
                self.cursor.model.hide()

                if self.cursor_asset_slot:
                    self.cursor_asset_slot.on_blur()
                    self.cursor_asset_slot = None

            if self.down_time is not None:
                cur_time = globalClock.frame_time
                hold_threshold = core.ConfigVariableDouble('click-hold-threshold', 0.3).get_value()
                if cur_time - self.down_time > hold_threshold:
                    self.down_time = cur_time
                    self.request('Charge')
        else:
            self.cursor_pos = None
            self.cursor.model.hide()
            mpos = None

    def exitNormal(self):
        self.cursor.model.hide()
        self.player.walk_ctr.stop()
        self.player.idle_ctr.stop()

    def enterCharge(self):
        self.sfx["obbo_charge"].play()
        self.player.charge_ctr.play()
        self.toggle_cam_view('charging')
        self.cam_target_p = 45
        self.crosshair.show()

        self.bobber.unstash()
        self.line.unstash()
        self.bobber.reparent_to(self.player.rod_tip)
        self.bobber.set_pos(0, 0, 0)
        self.bobber.set_hpr(0, 0, 0)

        props = core.WindowProperties()
        props.set_cursor_hidden(True)
        props.set_mouse_mode(core.WindowProperties.M_relative)
        base.win.request_properties(props)

        self.accept('mouse3-up', self.cancel)

    def updateCharge(self, dt):
        self.update_cast_cam()
        self.update_line()
        self.player.model.set_h(self.cam_dummy.get_h())

    def exitCharge(self):
        self.sfx["obbo_charge"].stop()
        self.player.charge_ctr.play()
        self.toggle_cam_view()
        self.crosshair.hide()
        props = core.WindowProperties()
        props.set_cursor_hidden(False)
        props.set_mouse_mode(self.default_mouse_mode)
        base.win.request_properties(props)
        base.messenger.send("reset_cursor")

        self.ignore('mouse3-up')

    def enterCast(self, power):
        self.sfx["obbo_cast"].play()
        distance = max(min(power, 1) * CAST_MAX_DISTANCE, CAST_MIN_DISTANCE)
        self.bobber.set_pos(0, 0, 0)
        self.bobber.set_hpr(0, 0, 0)

        self.player.cast_ctr.play()
        Sequence(
            Wait(5 / self.player.cast_ctr.frame_rate),
            Func(self.fling_bobber, distance),
        ).start()

        self.down_time = None
        props = core.WindowProperties()
        props.set_cursor_hidden(True)
        props.set_mouse_mode(core.WindowProperties.M_relative)
        base.win.request_properties(props)

    def fling_bobber(self, distance):
        self.bobber.wrt_reparent_to(self.player.model)

        rod_tip_pos = self.player.rod_tip.get_pos(self.player.model)
        direction = self.crosshair.model.get_pos(self.player.model).normalized()
        self.bobber.set_pos(rod_tip_pos + direction * 3)
        self.bobber.look_at(rod_tip_pos + direction * distance)

        self.traverser.add_collider(self.bobber_collider, self.asteroid_handler)
        Sequence(
            Parallel(
                LerpPosInterval(self.bobber, CAST_TIME, rod_tip_pos + direction * distance, blendType='easeOut'),
                LerpHprInterval(self.bobber, CAST_TIME, (self.bobber.get_h(), self.bobber.get_p(), 360 * distance * BOBBER_SPIN_SPEED), blendType='easeOut'),
            ),
            Func(self.sfx["obbo_cast"].stop),
        ).start()

    def updateCast(self, dt):
        self.update_cast_cam()
        self.update_line()

        if self.down_time is not None:
            self.updateReel(dt)

        self.traverser.traverse(self.universe.root)
        self.asteroid_handler.sort_entries()

        hit_asteroids = [
            i.into_node_path.get_python_tag('asteroid') for i in
            self.asteroid_handler.entries
            if i.into_node_path.has_python_tag('asteroid')
        ]

        if hit_asteroids:
            self.sfx["obbo_reel_in"].play()
            self.request('Reel', hit_asteroids[0])

    def exitCast(self):
        self.sfx["obbo_cast"].stop()
        self.traverser.remove_collider(self.bobber_collider)
        props = core.WindowProperties()
        props.set_cursor_hidden(False)
        props.set_mouse_mode(self.default_mouse_mode)
        base.win.request_properties(props)
        base.messenger.send("reset_cursor")

    def enterReel(self, asteroid=None):
        if asteroid is not None:
            self.sfx["astroid_attaches"].play()
            print('hit an asteroid!')
            asteroid.stop()
            asteroid.asteroid.wrt_reparent_to(self.bobber)

            asteroid.asteroid.posInterval(MAGNET_SNAP_TIME, self.magnet_snap_point).start()
            self.catch = asteroid

        if not self.player.reel_ctr.playing:
            self.player.reel_ctr.play()

    def updateReel(self, dt):
        self.update_cast_cam()
        self.update_line()

        # Reel in
        rod_tip_pos = self.player.rod_tip.get_pos(self.bobber.parent)
        bobber_pos = self.bobber.get_pos() - rod_tip_pos
        bobber_dst = bobber_pos.length()
        if bobber_dst > REEL_MIN_DISTANCE:
            bobber_dir = bobber_pos / bobber_dst
            self.bobber.set_pos(self.bobber.get_pos() - bobber_dir * min(bobber_dst, REEL_SPEED * dt))
        elif self.catch:
            self.request('Consume', self.catch)
            self.catch = None
        else:
            self.sfx["obbo_reel_in"].stop()
            self.sfx["catched_nothing"].play()
            self.request('Normal')

    def exitReel(self):
        self.player.reel_ctr.stop()

    def enterConsume(self, catch):
        self.sfx["astroid_collected"].play()
        Sequence(
            catch.asteroid.scaleInterval(1.0, 0.0001),
            Func(catch.destroy),
            Func(lambda: self.request('Normal')),
        ).start()
        messenger.send('caught_asteroid')
        start_pos = base.camera.get_pos()
        x = start_pos.x
        y = start_pos.y
        Sequence(
            base.camera.posInterval(0.1, (x - 0.05, y + 0.05, start_pos.z), start_pos),
            base.camera.posInterval(0.1, (x + 0.05, y - 0.05, start_pos.z)),
            base.camera.posInterval(0.1, (x - 0.05, y + 0.05, start_pos.z)),
            base.camera.posInterval(0.1, (x + 0.05, y - 0.05, start_pos.z)),
            base.camera.posInterval(0.1, (x - 0.05, y + 0.05, start_pos.z)),
            base.camera.posInterval(0.1, (x + 0.05, y - 0.05, start_pos.z)),
            base.camera.posInterval(0.1, (x - 0.05, y + 0.05, start_pos.z)),
            base.camera.posInterval(0.1, start_pos),
        ).start()

    def enterBuild(self, asset_slot):
        self.sfx["menu_accept"].play()
        self.ignore('mouse1')
        self.ignore('mouse1-up')
        self.target_pos = None
        self.target.root.hide()
        # TODO: Maybe modify PieMenu to accept a dict with categories? Definitely is too much for more than 5/6 items
        buildable = [j for i in self.universe.game_logic.get_unlocked().values() for j in i]
        items = []
        blocks = self.universe.game_logic.blocks_available()
        power_have = self.universe.game_logic.power_available()
        for model in buildable:
            cost = self.universe.game_logic.get_cost(model)
            power = self.universe.game_logic.get_power(model)
            not_enough_power = power < 0 and abs(power) > power_have
            items.append(PieMenuItem(model.capitalize(), f'build_{model}', model, cost, power, cost > blocks, not_enough_power))
        self.pie_menu = PieMenu(items, lambda: self.request('Normal'))
        for item in items:
            self.accept_once(item.event, self.build, [item.event, asset_slot])
        self.down_pos = None
        self.pie_menu.show()

    def updateBuild(self, dt):
        def finish_building(task):
            self.sfx["building_placed"].play()
            self.player.build_ctr.stop()
            self.request('Normal')
            return task.done

        if self.target_pos is not None and self.build_asset_slot:
            if self.player.move_toward(self.target_pos, dt):
                # Arrived.
                self.player.look_toward(self.build_asset_slot.get_pos())
                self.target_pos = None
                self.player.build_ctr.loop('build')
                self.build_asset_slot.build(self.build_building, BUILD_TIME)
                taskMgr.do_method_later(BUILD_TIME, finish_building, 'finish')
                self.build_asset_slot = None
                self.build_building = None
                self.sfx["obbo_build"].play()

    def exitBuild(self):
        self.accept('mouse1', self.on_mouse_down)
        self.accept('mouse1-up', self.on_mouse_up)

    def build(self, building, asset_slot):
        if self.universe.game_logic.can_build(building[6:]):
            self.sfx["menu_accept"].play()
            self.target_pos = core.Vec3(asset_slot.get_pos())
            dir = core.Vec3(self.target_pos - self.player.get_pos())
            dir.normalize()
            self.target_pos -= dir * BUILD_DIST / self.universe.planet.root.get_scale()[0]
            self.target_pos.normalize()
            self.build_asset_slot = asset_slot
            self.build_building = building[6:]
            self.pie_menu.hide(ignore_callback=True)
        else:
            self.sfx["catched_nothing"].play()

    def update_line(self):
        writer = core.GeomVertexWriter(self.line.node().modify_geom(0).modify_vertex_data(), 'vertex')
        writer.set_data3(self.player.rod_tip.get_pos(self.player.root))
        writer.set_data3(self.bobber.get_pos(self.player.root))

    def update_cast_cam(self):
        if self.state == 'Build':
            return
        ptr = base.win.get_pointer(0)
        if ptr.in_window:
            mpos = core.Point2(ptr.x / base.win.get_x_size() * 2 - 1,
                               -(ptr.y / base.win.get_x_size() * 2 - 1))

            self.cam_target_h = mpos.x * -1 * (360 * CAM_CAST_X_SENSITIVITY)
            self.cam_target_p = mpos.y * -45 + 45

            border = 0.5 / CAM_CAST_X_SENSITIVITY
            if mpos.x > 1 - border or mpos.x < -1 + border:
                if mpos.x > 0:
                    new_x = mpos.x - 1.0 / CAM_CAST_X_SENSITIVITY
                else:
                    new_x = mpos.x + 1.0 / CAM_CAST_X_SENSITIVITY
                base.win.move_pointer(0, int((new_x * 0.5 + 0.5) * base.win.get_x_size()), int(ptr.y))

    def update(self, dt):
        if base.mouseWatcherNode.has_mouse():
            mpos = base.mouseWatcherNode.get_mouse()
        else:
            mpos = None

        if self.state and hasattr(self, f'update{self.state}'):
            getattr(self, f'update{self.state}')(dt)

        self.cursor.model.set_scale((5.0 + math.sin(globalClock.frame_time * 5)) / 3.0)

        cur_h = self.cam_dummy.get_h()
        dist = (self.cam_target_h - 180) - cur_h
        dist = (dist + CAM_START_HEADING) % 360 - 180
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
        self.model.set_pos(0, 50, 4)
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


class CrashedShip(PlanetObject):
    def __init__(self, planet):
        super().__init__(planet)

        self.model = loader.load_model("models/ship.bam").find("**/crashed_ship")
        self.model.reparent_to(self.root)
        self.model.clear_transform()
        self.model.set_scale(0.4)
        self.model.set_hpr(0, 270, 90)
        self.model.set_effect(core.CompassEffect.make(core.NodePath(),
                              core.CompassEffect.P_scale))
        self.model.find("**/crashed_ship_roof").set_two_sided(True)
        collider = self.model.attach_new_node(core.CollisionNode("ship"))
        collider.node().add_solid(core.CollisionCapsule((-3, 0, 0.5), (3, 0, 0.5), 1))
        collider.node().add_solid(core.CollisionCapsule((0, -2, 0.5), (0, 2, 0.5), 1))
        #collider.node().add_solid(core.CollisionSphere((1, 2, 2), 1.2))
        collider.node().set_from_collide_mask(0)
        collider.node().set_into_collide_mask(0b0010)
        #collider.show()

        self.old_pos = core.Vec3(*SHIP_POSITION)
        self.new_pos = self.old_pos
        self.build_slot = False
        self.sprouted = True

    def sprout(self):
        pass
