import sys

from direct.showbase.ShowBase import ShowBase
import panda3d
import pman.shim
import limeade

from gamelib import renderer
from gamelib.universe import Universe


panda3d.core.load_prc_file(
    panda3d.core.Filename.expand_from('$MAIN_DIR/settings.prc')
)


class GameApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        pman.shim.init(self)
        self.render_pipeline = renderer.Pipeline()
        self.accept('escape', sys.exit)

        self.universe = Universe()

        self.accept('mouse1', self.universe.on_click)
        self.accept('f3', self.toggle_wireframe)
        self.accept('f4', self.screenshot)
        self.accept('f5', limeade.refresh)
        self.disable_mouse()

        self.task_mgr.add(self.__update)

    def __update(self, task):
        self.universe.update(globalClock.dt)
        return task.cont


def main():
    app = GameApp()
    app.run()

if __name__ == '__main__':
    main()
