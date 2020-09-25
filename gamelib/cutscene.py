import panda3d.core as p3d

from direct.actor.Actor import Actor
from direct.showbase.DirectObject import DirectObject
from direct.interval import IntervalGlobal as intervals
from direct.gui.OnscreenText import OnscreenText

from .skybox import Skybox


class CutsceneState(DirectObject):
    def __init__(self, cutscene_name, bgm_name, next_state, state_args=None):
        super().__init__()
        state_args = [] if state_args is None else state_args

        parent = base.render
        model = base.loader.load_model(f'models/Cutscenes/{cutscene_name}.bam')
        actor = Actor(model)
        actor.reparent_to(parent)

        # Disable culling to make sure nothing clips out
        actor.node().set_bounds(p3d.OmniBoundingVolume())
        actor.node().set_final(True)

        # Setup camera animation
        camjoint = actor.expose_joint(None, 'modelRoot', 'camera')
        base.camera.set_pos((0, 0, 0))
        base.camera.reparent_to(camjoint)

        self.skybox = Skybox(camjoint)
        self.skybox.root.set_compass()


        # Match Blender camera
        prev_p= base.cam.get_p()
        base.cam.clear_transform()
        base.camera.clear_transform()
        base.cam.set_p(-90)

        prev_fov = list(base.camLens.get_fov())
        base.camLens.set_fov(90, 90)
        prev_near = base.camLens.get_near()
        base.camLens.set_near(0.1)

        # Play some background music if available
        if bgm_name:
            bgm = base.loader.load_music(f'music/{bgm_name}.ogg')
            bgm.set_loop(True)
            bgm.play()

        self.actor = actor

        self.instructions = OnscreenText(
            parent=base.aspect2d,
            text='Press space to skip',
            fg=(0.8, 0.8, 0.8, 1.0),
            pos=(0, -0.9)
        )

        dlight = p3d.DirectionalLight("light")
        dlight.color = (0.5, 0.5, 0.5, 1)
        dlight_lens = dlight.get_lens()
        dlight_lens.set_film_size(-3, 3)
        dlight_lens.set_near_far(-4, 1)
        dlight_path = self.actor.attach_new_node(dlight)
        dlight_path.look_at((1, -1, 0))
        self.actor.set_light(dlight_path)

        alight = p3d.AmbientLight("light")
        alight.color = (0.5, 0.5, 0.5, 1)
        self.actor.set_light(self.actor.attach_new_node(alight))

        def cleanup():
            # Reset camera
            base.camera.reparent_to(base.render)
            base.cam.set_p(prev_p)
            base.camLens.set_fov(*prev_fov)
            base.camLens.set_near(prev_near)

            # Cleanup the scene
            bgm.stop()
            self.instructions.remove_node()
            base.transitions.letterboxOff()
            self.actor.cleanup()
            self.actor = None

            # Transition to the next state
            print('transition')
            base.gamestate = next_state(*state_args)

        base.transitions.letterboxOn()
        base.transitions.fadeIn()
        ival = intervals.Sequence(
            actor.actor_interval('0', playRate=1.0),
            base.transitions.getFadeOutIval(),
            intervals.Func(cleanup)
        )
        ival.start()

        self.accept('space', ival.finish)

    def update(self, _dt):
        pass

class IntroCutscene(CutsceneState):
    def __init__(self, next_state, state_args=None):
        super().__init__('intro', 'intro_sequence', next_state, state_args)

        self.obbo_face = self.actor.find('**/obbo_face')
        taskMgr.doMethodLater(1050 / self.actor.get_frame_rate('0'), self.on_scare_obbo, 'scare-obbo')

    def on_scare_obbo(self, task):
        # Obbo bumps into asteroid
        self.obbo_face.set_shader_input('uv_shift', (0.5, 0.25), priority=1)

class EndingCutscene(CutsceneState):
    def __init__(self, next_state, state_args=None):
        super().__init__('ending', 'end_sequence', next_state, state_args)
