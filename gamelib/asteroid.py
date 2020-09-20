import random

from panda3d import core
from direct.interval.LerpInterval import *

from .planet import PlanetObject
from .procgen import asteroid


MIN_B = 0.05
MAX_B = 0.25


class Asteroid(PlanetObject):
    def __init__(self, planet):
        super().__init__(planet)
        bounds = core.Vec3(*(random.uniform(MIN_B, MAX_B) for _ in range(3)))
        color1 = core.Vec3(random.uniform(0.02, 0.1))
        color2 = color1 * random.uniform(0.5, 0.9)
        node = asteroid.generate(bounds, color1, color2, 1.8)
        baserot = self.root.attach_new_node('Base Rotation')
        baserot.set_hpr(random.randrange(360), random.randrange(-90, 90), 0)
        self.rotation = baserot.attach_new_node('Rotation')
        #sm = loader.load_model('smiley')
        #sm.copy_to(self.rotation)
        self.rotation.set_pos(0, 0, -1)
        self.asteroid = self.rotation.attach_new_node(node)
        self.asteroid.set_pos(planet.size * random.uniform(1.1, 1.6), planet.size * random.uniform(1.1, 1.6), 0)
        mat = core.Material()
        mat.set_roughness(2)
        self.asteroid.set_material(mat)
        LerpHprInterval(self.rotation, 10.0, (360, 0, 0)).loop()
        LerpHprInterval(self.asteroid, 3.0, (360, 360, 0)).loop()

