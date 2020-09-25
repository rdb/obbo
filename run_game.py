import math
import sys

from direct.showbase.ShowBase import ShowBase
import panda3d
import pman
import pman.shim

from gamelib import renderer
from gamelib.universe import Universe
from gamelib.mainmenu import MainMenu


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
        self.luttext = self.load_lut('lut.png')
        self.render_pipeline = renderer.Pipeline(
            lut_texture=self.luttext
        )
        self.accept('escape', sys.exit)

        self.render.set_shader_inputs(uv_shift=(0.0, 0.0))

        bgm = base.loader.load_music('music/menu.ogg')
        bgm.set_loop(True)
        bgm.play()

        self.transitions.fadeScreen(1.0)

        profile_mode = panda3d.core.ConfigVariableBool('profile-mode', False).get_value()
        if profile_mode:
            import random
            random.seed(0)

        skip_main_menu = panda3d.core.ConfigVariableBool('skip-main-menu', False).get_value()
        if skip_main_menu:
            self.gamestate = Universe()
        else:
            self.gamestate = MainMenu()

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

    def __update(self, task):
        self.gamestate.update(globalClock.dt)
        return task.cont

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
