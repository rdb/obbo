from panda3d import core

from .player import Player
from .planet import Planet
from .util import srgb_color


class Universe:
    def __init__(self):
        base.set_background_color(srgb_color(0x595961))

        self.root = base.render.attach_new_node("universe")

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
        self.player.set_pos((15, 15, 15))

        # Temporary
        base.cam.reparent_to(self.player.model)
        base.cam.set_pos((0, -15, 30))
        base.cam.look_at(self.player.model)
