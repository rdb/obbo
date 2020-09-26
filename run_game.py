import math
import sys
import os

from direct.showbase.ShowBase import ShowBase
import panda3d
import pman
import pman.shim

from gamelib import renderer
from gamelib.util import srgb_color

# States
from gamelib.universe import Universe
from gamelib.mainmenu import MainMenu
from gamelib.cutscene import IntroCutscene, EndingCutscene
from gamelib.optionmenu import OptionMenu
from gamelib.endstate import EndState

GAME_STATES = {
    'Universe': Universe,
    'MainMenu': MainMenu,
    'IntroCutscene': IntroCutscene,
    'EndingCutscene': EndingCutscene,
    'OptionMenu': OptionMenu,
    'End': EndState,
}


panda3d.core.load_prc_file(
    panda3d.core.Filename.expand_from('$MAIN_DIR/settings.prc')
)

USER_CONFIG_PATH = panda3d.core.Filename.expand_from(
    '$MAIN_DIR/user.prc'
)
if USER_CONFIG_PATH.exists():
    panda3d.core.load_prc_file(USER_CONFIG_PATH)


class GameApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        pman.shim.init(self)
        potato_mode = panda3d.core.ConfigVariableBool('potato-mode', False).get_value()
        self.luttext = self.load_lut('lut.png')
        self.render_pipeline = renderer.Pipeline(
            lut_texture=self.luttext,
            enable_shadows=not potato_mode,
        )
        self.accept('escape', sys.exit)

        self.set_background_color(srgb_color(0x292931))
        self.render.set_shader_inputs(uv_shift=(0.0, 0.0))

        # Get volume levels from config
        self.musicManager.set_volume(
            panda3d.core.ConfigVariableDouble('audio-music-volume', 1.0).get_value()
        )
        self.sfxManagerList[0].set_volume(
            panda3d.core.ConfigVariableDouble('audio-sfx-volume', 1.0).get_value()
        )

        self.bgm_name = None

        self.transitions.fadeScreen(1.0)

        profile_mode = panda3d.core.ConfigVariableBool('profile-mode', False).get_value()
        if profile_mode:
            import random
            random.seed(0)

        skip_main_menu = panda3d.core.ConfigVariableBool('skip-main-menu', False).get_value()
        self.gamestate = None
        if skip_main_menu:
            self.change_state('Universe')
        else:
            self.change_state('MainMenu')

        self.accept('f1', self.screenshot)
        def save_lut_screen():
            self.screenshot(embedLUT=True)
        self.accept('f2', save_lut_screen)
        self.accept('f3', self.toggle_wireframe)
        def toggle_lut():
            if self.render_pipeline.lut_texture is None:
                self.render_pipeline.lut_texture = self.luttext
            else:
                self.render_pipeline.lut_texture = None
        self.accept('f4', toggle_lut)
        if not pman.is_frozen():
            try:
                import limeade # pylint:disable=import-outside-toplevel
                self.accept('f5', self.refresh)
            except ImportError:
                print(
                    'Warning: Could not import limeade, module hot-reload will be unavailble'
                )
        self.accept('shift-l', self.render.ls)
        self.accept('shift-a', self.render.analyze)
        self.disable_mouse()

        self.setCursor(False)
        self.accept('mouse1', self.setCursor, [True])
        self.accept('mouse1-up', self.setCursor, [False])
        self.accept('reset_cursor', self.setCursor, [False])

        self.task_mgr.add(self.__update)

    def refresh(self):
        import limeade
        limeade.refresh()

        panda3d.core.ModelPool.release_all_models()
        for root in self.render.find_all_matches("**/+ModelRoot"):
            if root.node().fullpath:
                root.node().remove_all_children()
                model = loader.load_model(root.node().fullpath)
                root.node().steal_children(model.node())

    def set_bgm(self, bgm):
        if self.bgm_name != bgm:
            self.bgm_name = bgm
            bgmpath = f'music/{bgm}.ogg'
            self.bgm_audio = self.loader.load_music(bgmpath)
            self.bgm_audio.set_loop(True)
            self.bgm_audio.play()

    def __update(self, task):
        self.gamestate.update(globalClock.dt)
        return task.cont

    def change_state(self, next_state, state_args=None):
        state_args = state_args if state_args is not None else []
        if self.gamestate:
            self.gamestate.cleanup()
        self.gamestate = GAME_STATES[next_state](*state_args)

    def load_lut(self, filename):
        path = panda3d.core.Filename(filename)
        vfs = panda3d.core.VirtualFileSystem.get_global_ptr()
        failed = (
            not vfs.resolve_filename(path, panda3d.core.get_model_path().value)
            or not path.is_regular_file()
        )
        if failed:
            raise RuntimeError('Failed to find file {}'.format(filename))

        image = panda3d.core.PNMImage(path)

        lutdim = 64
        xsize, ysize = image.get_size()
        tiles_per_row = xsize // lutdim
        num_rows = math.ceil(lutdim / tiles_per_row)
        ysize -= num_rows * lutdim

        texture = panda3d.core.Texture()
        texture.setup_3d_texture(
            lutdim, lutdim, lutdim,
            panda3d.core.Texture.T_unsigned_byte,
            panda3d.core.Texture.F_rgb8
        )

        for tileidx in range(lutdim):
            xstart = tileidx % tiles_per_row * lutdim
            ystart = tileidx // tiles_per_row * lutdim + ysize
            islice = panda3d.core.PNMImage(lutdim, lutdim, 3, 255)
            islice.copy_sub_image(image, 0, 0, xstart, ystart, lutdim, lutdim)
            # XXX should write these values out correctly when saving/embedding
            islice.flip(False, True, False)
            texture.load(islice, tileidx, 0)
        return texture

    def setCursor(self, clicked):
        if clicked:
            x11Cur = os.path.join("cursor", "cursorClick.x11")
            winCur = os.path.join("cursor", "cursorClick.cur")
        else:
            x11Cur = os.path.join("cursor", "cursorNormal.x11")
            winCur = os.path.join("cursor", "cursorNormal.cur")

        base.win.clearRejectedProperties()
        props = panda3d.core.WindowProperties()
        # check for the os and set the specific cursor file
        if sys.platform.startswith('linux'):
            props.setCursorFilename(x11Cur)
        else:
            props.setCursorFilename(winCur)
        base.win.requestProperties(props)

    def screenshot(self, *args, embedLUT=False, **kwargs): # pylint:disable=invalid-name, arguments-differ
        filename = super().screenshot(*args, **kwargs)

        if not embedLUT or not filename:
            return filename

        lutdim = 64
        stepsize = 256 // lutdim

        image = panda3d.core.PNMImage(filename)
        xsize, ysize = image.get_size()
        tiles_per_row = xsize // lutdim
        num_rows = math.ceil(lutdim / tiles_per_row)

        image.expand_border(0, 0, num_rows * 64, 0, (0, 0, 0, 1))

        steps = list(range(0, 256, stepsize))

        for tileidx, bcol in enumerate(steps):
            xbase = tileidx % tiles_per_row * lutdim
            ybase = tileidx // tiles_per_row * lutdim + ysize
            for xoff, rcol in enumerate(steps):
                xcoord = xbase + xoff
                for yoff, gcol in enumerate(steps):
                    ycoord = ybase + yoff
                    image.set_xel_val(xcoord, ycoord, (rcol, gcol, bcol))

        image.write(filename)

        return filename


def main():
    app = GameApp()
    app.run()

if __name__ == '__main__':
    main()
