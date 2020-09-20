import sys

from direct.showbase.ShowBase import ShowBase
import panda3d
import pman.shim

from gamelib.universe import Universe


panda3d.core.load_prc_file(
    panda3d.core.Filename.expand_from('$MAIN_DIR/settings.prc')
)


class GameApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        pman.shim.init(self)
        self.accept('escape', sys.exit)

        self.universe = Universe()

        self.accept('f3', self.toggle_wireframe)
        self.disable_mouse()


def main():
    app = GameApp()
    app.run()

if __name__ == '__main__':
    main()
