import random

from panda3d import core
from direct.interval.LerpInterval import *

from .planet import PlanetObject
from .procgen import asteroid


MIN_B = 0.03
MAX_B = 0.3


class Asteroid(PlanetObject):
    def __init__(self, planet):
        super().__init__(planet)
        bounds = core.Vec3(*(random.uniform(MIN_B, MAX_B) for _ in range(3)))
        color1 = core.Vec3(random.uniform(0.05, 0.25))
        color2 = color1 * random.uniform(0.3, 0.9)
        node = asteroid.generate(bounds, color1, color2, random.uniform(5.2, 9.5))
        baserot = self.root.attach_new_node('Base Rotation')
        baserot.set_hpr(random.randrange(360), random.randrange(-90, 90), 0)
        self.rotation = baserot.attach_new_node('Rotation')
        self.rotation.set_pos(0, 0, -1)
        self.asteroid = self.rotation.attach_new_node(node)
        self.asteroid.set_pos(
            planet.size * random.uniform(1.1, 1.6),
            planet.size * random.uniform(1.1, 1.6),
            0
        )
        mat = core.Material()
        mat.set_roughness(1)
        self.asteroid.set_material(mat)
        LerpHprInterval(self.rotation, 10.0, (360, 0, 0)).loop()
        LerpHprInterval(self.asteroid, 3.0, (360, 360, 0)).loop()

        collide = core.CollisionNode('asteroid')
        collide.add_solid(core.CollisionSphere(center=(0, 0, 0), radius=0.3))
        collide = self.asteroid.attach_new_node(collide)
        collide.set_python_tag('asteroid', self)
