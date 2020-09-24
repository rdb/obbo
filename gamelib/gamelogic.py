from direct.showbase.DirectObject import DirectObject

from .techtree import TechTree, TechNode


TECH_TREE_CFG = [
    TechNode('windmill', 'power', 2),
    TechNode('replicator', 'science', 3, ('windmill',)),
    TechNode('workbench', 'science', 5, ('replicator',)),
    TechNode('tent', 'trophy', 3, ('workbench',)),
    TechNode('chest', 'storage', 3, ('workbench',)),
    TechNode('solarpower', 'power', 5, ('workbench',)),
    TechNode('house', 'trophy', 7, ('solarpower',)),
    TechNode('garage', 'storage', 7, ('solarpower',)),
    TechNode('lab', 'science', 7, ('solarpower',)),
    TechNode('mansion', 'trophy', 10, ('lab',)),
    TechNode('supercomputer', 'science', 9, ('lab',)),
    TechNode('soppower', 'power', 8, ('lab',)),
    TechNode('superpower', 'power', 11, ('supercomputer', 'soppower')),
    TechNode('beacon', 'science', 11, ('supercomputer', 'superpower')),
]


class GameLogic(DirectObject):
    def __init__(self):
        super().__init__()
        self.tech_tree = TechTree(TECH_TREE_CFG)
        self.accept('built', self.built)

    def built(self, model):
        self.tech_tree.unlock(model)

    def get_unlocked(self, fltr=None):
        return self.tech_tree.get_current(fltr)


# Example usage of the TechTree:

# gl = GameLogic()
# print(f'Initial Tech Tree before unlocking anything: {gl.tech_tree.get_current()}')
# gl.tech_tree.unlock('windmill')
# print(f'After building the first windmill: {gl.tech_tree.get_current()}')
# gl.tech_tree.unlock('replicator')
# print(f'After building the first replicator: {gl.tech_tree.get_current()}')
# gl.tech_tree.unlock('workbench')
# print(f'After building the first workbench: {gl.tech_tree.get_current()}')
