from direct.showbase.DirectObject import DirectObject
from direct.gui.OnscreenText import OnscreenText
from direct.interval.IntervalGlobal import Sequence
from panda3d import core

AUTO_CLEAR_MSG = 15


class HUD(DirectObject):
    def __init__(self):
        super().__init__()

        mgr = core.TextPropertiesManager.getGlobalPtr()
        for name in ["Blocks", "Energy", "PlanetSize"]:
            cardmaker = core.CardMaker("")
            cardmaker.set_frame(-0.75, 0.75, -0.75, 0.75)

            tex = loader.load_texture("textures/{}.png".format(name))
            graphic = base.camera.attach_new_node(cardmaker.generate())
            graphic.set_texture(tex)
            graphic.set_transparency(core.TransparencyAttrib.M_binary)

            mgr.setGraphic(name, graphic)
            graphic.setZ(-0.4)

        self.blocks = OnscreenText('\5Blocks\5: 0/5', pos=(0.3, -0.1), fg=(1,) * 4, parent=base.a2dTopLeft, scale=0.055, mayChange=True)
        self.power = OnscreenText('\5Energy\5: 0/0', pos=(-0.3, -0.1), fg=(1,) * 4, parent=base.a2dTopRight, scale=0.055, mayChange=True)
        self.message = OnscreenText('...', pos=(0, -0.1), fg=(1,) * 4, parent=base.a2dTopCenter, scale=0.055, mayChange=True, align=core.TextNode.ACenter)

        self.clear_message = 0
        self.message_active = False

        self.accept('update_hud', self.update_hud)
        self.accept('shake', self.shake)
        base.taskMgr.do_method_later(1, self.update, 'hud_update')

    def hide(self):
        self.blocks.hide()
        self.power.hide()
        self.message.hide()

    def show(self):
        self.blocks.show()
        self.power.show()
        self.message.show()

    def update_hud(self, elem, val1, val2=None):
        if elem == 'blocks':
            prev = self.blocks.text
            self.blocks.text = f'\5Blocks\5: {val1}/{val2}'
            if prev != self.blocks.text:
                self.animate_item(self.blocks)
        elif elem == 'power':
            prev = self.power.text
            self.power.text = f'\5Energy\5: {val1}/{val2}'
            if prev != self.power.text:
                self.animate_item(self.power)
        elif elem == 'msg':
            self.message.text = val1
            self.animate_item(self.message)
            self.clear_message = globalClock.get_frame_time() + (val2 or AUTO_CLEAR_MSG)
            self.message_active = True
        else:
            raise ValueError(f'Unkown element "{elem}"')

    def animate_item(self, node):
        Sequence(
            node.scaleInterval(0.15, 1.05, blendType='easeInOut'),
            node.scaleInterval(0.15, 0.95, blendType='easeInOut'),
            node.scaleInterval(0.15, 1.05, blendType='easeInOut'),
            node.scaleInterval(0.15, 0.95, blendType='easeInOut'),
            node.scaleInterval(0.15, 1.05, blendType='easeInOut'),
            node.scaleInterval(0.15, 1, blendType='easeInOut'),
        ).start()

    def shake(self, elem):
        elements = {'blocks': self.blocks, 'power': self.power, 'msg':self.message}
        if elem not in elements:
            raise ValueError(f'Unknown element "{elem}"')
        self.animate_item(elements[elem])

    def update(self, task):
        if self.message_active and self.clear_message <= globalClock.get_frame_time():
            self.message.text = '...'
            self.message_active = False
        return task.again
