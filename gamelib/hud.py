from direct.showbase.DirectObject import DirectObject
from direct.gui.OnscreenText import OnscreenText
from direct.interval.IntervalGlobal import Sequence
from panda3d import core

AUTO_CLEAR_MSG = 15


class HUD(DirectObject):
    def __init__(self):
        super().__init__()
        self.blocks = OnscreenText('Blocks: 0/5', pos=(0.3, -0.05), fg=(1,) * 4, parent=base.a2dTopLeft, scale=0.055, mayChange=True)
        self.power = OnscreenText('Power: 0/0', pos=(-0.3, -0.05), fg=(1,) * 4, parent=base.a2dTopRight, scale=0.055, mayChange=True)
        self.message = OnscreenText('...', pos=(0, -0.05), fg=(1,) * 4, parent=base.a2dTopCenter, scale=0.055, mayChange=True, align=core.TextNode.ACenter)

        self.clear_message = 0
        self.message_active = False

        self.accept('update_hud', self.update_hud)
        base.taskMgr.do_method_later(1, self.update, 'hud_update')

    def update_hud(self, elem, val1, val2=None):
        if elem == 'blocks':
            self.blocks.text = f'Blocks: {val1}/{val2}'
            self.animate_item(self.blocks)
        elif elem == 'power':
            self.power.text = f'Power: {val1}/{val2}'
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

    def update(self, task):
        if self.message_active and self.clear_message <= globalClock.get_frame_time():
            self.message.text = '...'
            self.message_active = False
        return task.again
