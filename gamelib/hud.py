from direct.showbase.DirectObject import DirectObject
from direct.gui.OnscreenText import OnscreenText



class HUD(DirectObject):
    def __init__(self):
        super().__init__()
        self.blocks = OnscreenText('Blocks: 0/5', pos=(0.3, -0.05), fg=(1,) * 4, parent=base.a2dTopLeft, mayChange=True)
        self.power = OnscreenText('Power: 0/0', pos=(-0.3, -0.05), fg=(1,) * 4, parent=base.a2dTopRight, mayChange=True)
        self.message = OnscreenText('...', pos=(0, -0.05), fg=(1,) * 4, parent=base.a2dTopCenter, mayChange=True)

        self.accept('update_hud', self.update_hud)

    def update_hud(self, elem, val1, val2=None):
        if elem == 'blocks':
            self.blocks.text = f'Blocks: {val1}/{val2}'
        elif elem == 'power':
            self.power.text = f'Power: {val1}/{val2}'
        elif elem == 'msg':
            self.message.text = val1
        else:
            raise ValueError(f'Unkown element "{elem}"')
