import sys

import panda3d.core as p3d
from direct.showbase.DirectObject import DirectObject
from direct.interval import IntervalGlobal as intervals

from .universe import Universe
from .skybox import Skybox
from .cutscene import IntroCutscene, EndingCutscene

class MainMenu(DirectObject):
    def __init__(self):
        super().__init__()

        self.root = base.loader.load_model('models/mainMenu.bam')
        self.root.reparent_to(base.render)

        self.skybox = Skybox(self.root)

        self.traverser = p3d.CollisionTraverser()
        self.ray = p3d.CollisionRay()
        picker = p3d.CollisionNode('picker')
        picker.add_solid(self.ray)
        picker.set_from_collide_mask(1)
        picker.set_into_collide_mask(0)
        self.picker = self.root.attach_new_node(picker)
        self.picker_handler = p3d.CollisionHandlerQueue()
        self.traverser.add_collider(self.picker, self.picker_handler)

        scene_camera = self.root.find('**/-Camera')
        campos = scene_camera.get_pos(self.root)
        base.camera.set_pos(campos)
        self.picker.set_pos(campos)

        self.accept('mouse1-up', self.handle_click)

        base.transitions.fadeIn()

    def cleanup(self):
        self.root.remove_node()
        self.picker.remove_node()
        self.ignore_all()

    def handle_click(self):
        if not base.mouseWatcherNode.has_mouse():
            return

        mpos = base.mouseWatcherNode.get_mouse()
        self.ray.set_from_lens(base.cam.node(), *mpos)

        self.traverser.traverse(self.root)

        self.picker_handler.sort_entries()
        for entry in self.picker_handler.entries:
            npname = entry.getIntoNodePath().name

            if npname == 'StartSignSign':
                self.cleanup()
                ival = base.transitions.getFadeOutIval()
                def change_state():
                    base.gamestate = IntroCutscene(Universe)
                ival.append(intervals.Func(change_state))
                ival.start()
                break
            elif npname == 'OptionSignSign':
                self.cleanup()
                ival = base.transitions.getFadeOutIval()
                def change_state():
                    from .optionmenu import OptionMenu
                    base.gamestate = OptionMenu()
                ival.append(intervals.Func(change_state))
                ival.start()
                break
            elif npname == 'QuitSignSign':
                sys.exit()

    def update(self, dt):
        pass
