from panda3d import core

from .planet import PlanetObject


class Player(PlanetObject):
    def __init__(self, planet):
        super().__init__(planet)

        # Temporary
        model = loader.load_model("jack")
        model.reparent_to(self.root)
        model.set_effect(core.CompassEffect.make(core.NodePath(), core.CompassEffect.P_scale))
        model.set_z(1)
        self.model = model

        self.target_pos = None

    def move_to(self, pos):
        self.target_pos = core.Vec3(*pos)
        self.target_pos.normalize()

    def update(self, dt):
        if self.target_pos:
            # Not quite correct, but probably good enough
            pos = self.get_pos()
            delta = (self.target_pos - pos)
            dist = delta.length()
            delta *= 1.0 / dist
            if (delta * dt).length() > dist:
                self.set_pos(self.target_pos)
                self.target_pos = None
            else:
                self.set_pos(pos + delta * dt)
