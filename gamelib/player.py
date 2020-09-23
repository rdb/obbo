from panda3d import core
from direct.actor.Actor import Actor

from .planet import PlanetObject
from .util import clamp_angle


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
        self.from_np = core.NodePath('from')
        self.to_np = core.NodePath('to')
        self.model = model
        self.walk_ctr = self.model.get_anim_control('walk')
        self.cast_ctr = self.model.get_anim_control('fish_charge')

        self.collider = self.model.attach_new_node(core.CollisionNode("collision"))
        self.collider.node().add_solid(core.CollisionSphere((0, 0, 0.5), 0.5))
        self.collider.node().add_solid(core.CollisionSphere((0, 0, 1.2), 0.5))
        self.collider.node().set_from_collide_mask(0b0010)
        self.collider.node().set_into_collide_mask(0b0000)
        #self.collider.show()

        # Disable back-face culling on the face
        model.find('**/Plane.001').set_two_sided(True)

        self.target_pos = None

    def start_charge(self):
        self.cast_ctr.set_play_rate(2.0)
        self.cast_ctr.play()

    def stop_charge(self):
        self.cast_ctr.set_play_rate(-2.0)
        self.cast_ctr.play()

    def move_to(self, pos):
        self.target_pos = core.Vec3(*pos)
        self.target_pos.normalize()
        if not self.walk_ctr.is_playing():
            self.walk_ctr.loop('walk')

    def update(self, dt):
        if self.target_pos:
            # Not quite correct, but probably good enough
            scale = self.root.get_scale(core.NodePath())[0] * 0.1
            pos = self.get_pos() * scale
            target = self.target_pos * scale
            delta = (target - pos)

            # FIXME: This is a hack!! Needs at least angle clamping or a smarter
            # way to correctly orient Obbo...
            self.from_np.set_pos(pos)
            self.to_np.set_pos(target)
            self.from_np.look_at(self.to_np)
            delta_h = clamp_angle(self.from_np.get_h(self.root)) - clamp_angle(self.model.get_h())
            dist = delta.length()
            if dist == 0:
                self.target_pos = None
                self.model.set_h(delta_h)
            else:
                delta *= 1.0 / dist
                if (delta * dt).length() > dist:
                    self.set_pos(self.target_pos)
                    self.target_pos = None
                else:
                    self.set_pos(pos + delta * dt)

                # FIXME: Figure out rotation speed          vv
                self.model.set_h(self.model, delta_h * dt * 40)
        elif self.walk_ctr.is_playing():
            self.walk_ctr.pose(self.walk_ctr.get_frame())
