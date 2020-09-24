import random

from panda3d import core
from direct.showbase.DirectObject import DirectObject
from direct.gui.OnscreenText import OnscreenText
from direct.interval.IntervalGlobal import *
from direct.fsm.FSM import FSM

from .planet import Planet
from .asteroid import Asteroid
from .util import srgb_color
from .skybox import Skybox
from .playercontrol import PlayerControl


MAX_ASTEROIDS = 20
SPAWN_TIME = 1.5

INSTRUCTIONS = """
Reach for the stars Obbo!
Click with the left mouse button to move
Hold the left mouse button to ready a cast
Release the left mouse button to cast and reach for an asteroid
Holding the left mouse button will reel in the bobber
Once hooked you will automatically reel in the asteroid
"""

INSTRUCTIONS_AUTO_REMOVE_TIME = 20

class Universe(FSM, DirectObject):
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
        self.dlight.set_shadow_caster(True, 1024, 1024)
        dlight_lens = self.dlight.get_lens()
        dlight_lens.set_film_size(-3, 3)
        dlight_lens.set_near_far(-4, 1)
        dlight_path = self.planet.root.attach_new_node(self.dlight)
        dlight_path.look_at((1, 1, 0))
        self.root.set_light(dlight_path)
        #self.dlight.show_frustum()

        self.alight = core.AmbientLight("light")
        self.alight.color = (0.5, 0.5, 0.5, 1)
        self.root.set_light(self.root.attach_new_node(self.alight))

        self.asteroids = [Asteroid(self.planet, self) for _ in range(12)]
        self.last_asteroid = 0

        skip_main_menu = panda3d.core.ConfigVariableBool('skip-main-menu', False).get_value()
        if skip_main_menu:
            # If we skipped the main menu, do not show the instructions
            self.instructions = None
        else:
            self.add_instructions(INSTRUCTIONS)

        taskMgr.do_method_later(
            INSTRUCTIONS_AUTO_REMOVE_TIME,
            self.remove_instructions,
            'remove insntructions'
        )

        self.request('Universe')

    def add_instructions(self, text):
        self.instructions = OnscreenText(
            parent=base.aspect2d,
            text=text,
            fg=(0.8, 0.8, 0.8, 1.0),
        )

    def remove_instructions(self, task=None):
        if self.instructions is not None:
            Sequence(
                LerpColorScaleInterval(
                    self.instructions,
                    0.5,
                    (0, 0, 0, 0)
                ),
                Func(self.instructions.remove_node)
            ).start()
            self.instructions = None
        if task is not None:
            return task.done

    def enterUniverse(self): # pylint: disable=invalid-name
        base.transitions.fadeIn()
        def handle_left_mouse():
            self.player_control.on_mouse_down()
            self.remove_instructions()
        self.accept('mouse1', handle_left_mouse)
        self.accept('mouse1-up', self.player_control.on_mouse_up)
        self.accept('mouse3-up', self.player_control.cancel)
        self.player_control.enter()

    def exitUniverse(self): # pylint: disable=invalid-name
        base.transitions.fadeOut()
        self.ignore_all()
        self.player_control.exit()

    def update(self, dt):
        self.player_control.update(dt)
        ft = globalClock.get_frame_time()
        if ft > self.last_asteroid + SPAWN_TIME and len(self.asteroids) < MAX_ASTEROIDS:
            self.last_asteroid = ft
            self.asteroids.append(Asteroid(self.planet, self))
            print('added new asteroid')
