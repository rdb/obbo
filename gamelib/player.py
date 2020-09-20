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
