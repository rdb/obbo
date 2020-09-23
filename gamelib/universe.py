from panda3d import core
from direct.fsm.FSM import FSM

from .planet import Planet
from .asteroid import Asteroid
from .util import srgb_color
from .skybox import Skybox
from .playercontrol import PlayerControl


class Universe(FSM):
    def __init__(self):
        super().__init__('Universe')
        base.set_background_color(srgb_color(0x595961))

        self.root = base.render.attach_new_node("universe")

        self.skybox = Skybox(self.root)

        self.planet = Planet()
        self.planet.root.reparent_to(self.root)
        self.player_control = PlayerControl(self)

        self.dlight = core.DirectionalLight("light")
        self.dlight.color = (0.5, 0.5, 0.5, 1)
        self.dlight.direction = (1, 1, 0)
        self.root.set_light(self.root.attach_new_node(self.dlight))

        self.alight = core.AmbientLight("light")
        self.alight.color = (0.5, 0.5, 0.5, 1)
        self.root.set_light(self.root.attach_new_node(self.alight))

        self.asteroids = [Asteroid(self.planet) for _ in range(10)]

        self.request('Universe')

    def enterUniverse(self):
        base.transitions.fadeIn()
        base.accept('mouse1', self.player_control.on_down)
        base.accept('mouse1-up', self.player_control.on_click)
        self.player_control.enter()

    def exitUniverse(self):
        base.transitions.fadeOut()
        base.forget('mouse1')
        base.forget('mouse1-up')
        self.player_control.exit()


    def update(self, dt):
        self.player_control.update(dt)
