from panda3d import core
from direct.actor.Actor import Actor

from .planet import PlanetObject
from .util import clamp_angle


PLAYER_WALK_SPEED = 0.4
PLAYER_ROTATE_SPEED = 10


class Player(PlanetObject):
    def __init__(self, planet):
        super().__init__(planet)

        # Temporary
        self.model_pos = self.root.attach_new_node('heading')
        self.model_pos.set_effect(core.CompassEffect.make(core.NodePath(),
                                  core.CompassEffect.P_scale))
        self.model_pos.set_z(0)
        model = Actor("models/obbo.bam")
        model.reparent_to(self.model_pos)
        self.model = model

        self.rod_tip = model.expose_joint(None, 'modelRoot', 'bobber')

        self.idle_ctr = self.model.get_anim_control('idle')
        self.walk_ctr = self.model.get_anim_control('walk')
        self.charge_ctr = self.model.get_anim_control('fish_charge')
        self.cast_ctr = self.model.get_anim_control('fish_cast')
        self.reel_ctr = self.model.get_anim_control('fish_reel')
        self.build_ctr = self.model.get_anim_control('build')

        self.collider = self.model.attach_new_node(core.CollisionNode("collision"))
        self.collider.node().add_solid(core.CollisionSphere((0, 0, 0.5), 0.5))
        self.collider.node().add_solid(core.CollisionSphere((0, 0, 1.2), 0.5))
        self.collider.node().set_from_collide_mask(0b0010)
        self.collider.node().set_into_collide_mask(0b0000)
        #self.collider.show()

        # Disable back-face culling on the face
        model.find('**/Plane.001').set_two_sided(True)

    def move_toward(self, target_pos, dt):
        """Moves towards the given pos.  If arrived, returns True."""

        # Not quite correct, but probably good enough
        scale = self.root.get_scale(core.NodePath())[0] * 0.1
        pos = self.get_pos() * scale
        target = target_pos * scale
        delta = (target - pos)

        dummy_np = core.NodePath("dummy")
        dummy_np.look_at(target - pos)
        target_h = dummy_np.get_h(self.root)
        delta_h = ((target_h - self.model.get_h()) + 180) % 360 - 180
        dist = delta.length()
        if dist != 0:
            self.model.set_h(self.model.get_h() + delta_h * min(dt * PLAYER_ROTATE_SPEED, 1))

            delta *= PLAYER_WALK_SPEED / dist

            if (delta * dt).length() <= dist:
                self.set_pos(pos + delta * dt)
                if not self.walk_ctr.playing:
                    self.walk_ctr.play()
                return False

        self.set_pos(target_pos)
        self.model.set_h(target_h)

        if self.walk_ctr.playing:
            # Finish the animation
            start_frame = self.walk_ctr.frame
            if start_frame <= 6:
                end_frame = 6
            elif start_frame <= 16:
                end_frame = 16
            else:
                end_frame = self.walk_ctr.num_frames + 6
            self.walk_ctr.stop()
            if start_frame != end_frame:
                self.walk_ctr.play(start_frame, end_frame)
        return True
