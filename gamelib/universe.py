import random

from panda3d import core
from direct.showbase.DirectObject import DirectObject
from direct.gui.OnscreenText import OnscreenText
from direct.interval.IntervalGlobal import *
from direct.fsm.FSM import FSM

from .planet import Planet
from .asteroid import Asteroid
from .skybox import Skybox
from .playercontrol import PlayerControl
from .gamelogic import GameLogic
from .hud import HUD
from .endstate import EndState
from .cutscene import EndingCutscene


MAX_ASTEROIDS = [6, 12, 18, 24, 30]
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

        self.root = base.render.attach_new_node("universe")

        self.skybox = Skybox(self.root)

        self.game_logic = GameLogic()
        self.hud = HUD()

        self.planet = Planet()
        self.planet.root.reparent_to(self.root)
        self.player_control = PlayerControl(self)
        self.planet_size = self.planet.size

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

        self.asteroids = [Asteroid(self.planet, self) for _ in range(6)]
        self.last_asteroid = 0

        skip_main_menu = panda3d.core.ConfigVariableBool('skip-main-menu', False).get_value()
        if skip_main_menu:
            # If we skipped the main menu, do not show the instructions
            self.instructions = None
        else:
            self.instructions = None
            #self.add_instructions(INSTRUCTIONS)

        taskMgr.do_method_later(
            INSTRUCTIONS_AUTO_REMOVE_TIME,
            self.remove_instructions,
            'remove insntructions'
        )

        self.accept('display_msg', self.display_message)
        self.request('Universe')
        base.accept('f11', self.handle_victory)
        self.accept('beacon_built', self.handle_victory)

    def display_message(self, text, duration=INSTRUCTIONS_AUTO_REMOVE_TIME):
        self.add_instructions(text)
        taskMgr.do_method_later(
            duration,
            self.remove_instructions,
            'remove insntructions'
        )

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

    def handle_victory(self):
        self.player_control.universe.hud.hide()
        self.player_control.player.root.hide()
        base.gamestate = EndingCutscene(self.planet, EndState, state_args=[self])

    def enterUniverse(self): # pylint: disable=invalid-name
        base.transitions.fadeIn()
        self.accept_once('mouse1', self.remove_instructions)
        base.set_bgm('menu')
        base.messenger.send('update_hud', ['msg', 'Click to move, hold to cast...', 45])

    def exitUniverse(self): # pylint: disable=invalid-name
        base.transitions.fadeOut()
        self.player_control.exit()

    def update(self, dt):
        self.player_control.update(dt)
        ft = globalClock.get_frame_time()
        mx_asteroids = MAX_ASTEROIDS[self.planet.size - 1]
        if ft > self.last_asteroid + SPAWN_TIME and len(self.asteroids) < mx_asteroids:
            self.last_asteroid = ft
            self.asteroids.append(Asteroid(self.planet, self))
        if self.planet_size != self.planet.size:
            self.planet_size = self.planet.size
            for i in self.asteroids:
                i.update_pos()
