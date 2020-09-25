from direct.showbase.DirectObject import DirectObject

from .techtree import TechTree, TechNode


TECH_TREE_CFG = [
    TechNode('windmill', 'power', 2, 3),
    TechNode('replicator', 'science', 3, -1, ('windmill',)),
    TechNode('workbench', 'science', 5, -1, ('replicator',)),
    TechNode('tent', 'trophy', 3, 0, ('workbench',)),
    TechNode('chest', 'storage', 3, 0, ('workbench',), 10),
    TechNode('solarpower', 'power', 5, 9, ('workbench',)),
    TechNode('house', 'trophy', 7, 0, ('solarpower',)),
    TechNode('garage', 'storage', 7, 0, ('solarpower',), 25),
    TechNode('lab', 'science', 7, -10, ('solarpower',)),
    TechNode('mansion', 'trophy', 10, 0, ('lab',)),
    TechNode('supercomputer', 'science', 9, -15, ('lab',)),
    TechNode('soppower', 'power', 8, 16, ('lab',)),
    TechNode('superpower', 'power', 11, 40, ('supercomputer', 'soppower')),
    TechNode('beacon', 'science', 11, -35, ('supercomputer', 'superpower')),
]

PLANET_GROWTH_STEPS = (5, 15, 35, 75)


class GameLogic(DirectObject):
    def __init__(self):
        super().__init__()
        self.tech_tree = TechTree(TECH_TREE_CFG)

        # Game state
        self.storage_cap = 5
        self.storage_used = 0
        self.collected_total = 0
        self.grow_next = 5
        self.growth_cycle = 0
        self.power_cap = 0
        self.power_used = 0

        self.accept('built', self.built)
        self.accept('caught_asteroid', self.caught_asteroid)

    def built(self, model):
        self.tech_tree.unlock(model)
        self.storage_cap += self.tech_tree.get_capacity(model)
        self.storage_used -= self.tech_tree.get_build_cost(model)
        pwr = self.tech_tree.get_power(model)
        if pwr >= 0:
            self.power_cap += pwr
        else:
            self.power_used += abs(pwr)

        # TODO: Alert the player to build more power delivery
        if self.power_used / self.power_cap > 0.9:
            messenger.send('power_level_critical')
        messenger.send('update_hud', ['power', self.power_used, self.power_cap])

    def caught_asteroid(self):
        self.collected_total += 1
        self.storage_used += 1
        self.storage_used = min(self.storage_cap, self.storage_used)
        if self.collected_total == self.grow_next:
            messenger.send('planet_grow')
            self.growth_cycle += 1
            if self.growth_cycle >= len(PLANET_GROWTH_STEPS):
                self.grow_next = 0
            else:
                self.grow_next = PLANET_GROWTH_STEPS[self.growth_cycle]
        messenger.send('update_hud', ['blocks', self.storage_used, self.storage_cap])

    def get_unlocked(self, fltr=None):
        return self.tech_tree.get_current(fltr)

    def can_build(self, model):
        ok = self.tech_tree.get_build_cost(model) <= self.storage_used
        pwr = self.tech_tree.get_power(model)
        if pwr >= 0:
            return ok
        return ok and abs(pwr) + self.power_used <= self.power_cap


# Example usage of the TechTree:

# gl = GameLogic()
# print(f'Initial Tech Tree before unlocking anything: {gl.tech_tree.get_current()}')
# gl.tech_tree.unlock('windmill')
# print(f'After building the first windmill: {gl.tech_tree.get_current()}')
# gl.tech_tree.unlock('replicator')
# print(f'After building the first replicator: {gl.tech_tree.get_current()}')
# gl.tech_tree.unlock('workbench')
# print(f'After building the first workbench: {gl.tech_tree.get_current()}')
