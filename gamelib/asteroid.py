import random

from panda3d import core
from direct.interval.LerpInterval import *

from .procgen import asteroid
from .planet import GROWTH_TIME


MIN_B = 0.4
MAX_B = 0.9
SCALE_DURATION = 0.3


class Asteroid:
    def __init__(self, planet, universe):
        self.universe = universe
        self.planet = planet

        self.root = planet.root.attach_new_node("root")
        bounds = core.Vec3(*(random.uniform(MIN_B, MAX_B) for _ in range(3)))
        radius = max(bounds)
        color1 = core.Vec3(random.uniform(0.05, 0.25))
        color2 = color1 * random.uniform(0.1, 0.5)
        node = asteroid.generate(bounds, color1, color2, random.uniform(5.2, 9.5))
        self.root.set_hpr(random.randrange(360), random.randrange(-90, 90), 0)
        self.rotation = self.root.attach_new_node('Rotation')
        self.asteroid = self.rotation.attach_new_node(node)
        self.xoff = random.uniform(1.7, 5)
        self.yoff = random.uniform(1.7, 5)
        self.update_pos(False)
        mat = core.Material()
        mat.set_roughness(1)
        self.asteroid.set_material(mat)
        self.asteroid.set_effect(core.CompassEffect.make(core.NodePath(),
                                 core.CompassEffect.P_scale))
        self.asteroid.node().set_bounds(core.OmniBoundingVolume())

        self._orbit_ival = LerpHprInterval(self.rotation, random.uniform(8, 12), (0, 360, 0))
        self._spin_ival = LerpHprInterval(self.asteroid, 3.0, (360, 360, 0))

        self._orbit_ival.loop()
        self._spin_ival.loop()

        self.collider = core.CollisionNode('asteroid')
        self.collider.add_solid(core.CollisionSphere(center=(0, 0, 0), radius=radius))
        self.collider.set_into_collide_mask(0b0100)
        self.collider.set_from_collide_mask(0b0100)
        self.collider = self.asteroid.attach_new_node(self.collider)
        self.collider.set_python_tag('asteroid', self)
        self.asteroid.set_scale(1e-9)
        self.asteroid.scaleInterval(SCALE_DURATION, 1.0, blendType='easeIn').start()

    def update_pos(self, shout=True):
        if shout:
            print(f'before {self.asteroid.get_pos(self.planet.root)} {self.planet.size}')
        self.asteroid.posInterval(GROWTH_TIME, (
            self.xoff,
            self.yoff,
            -self.planet.size * 3 - self.xoff,
            )
        ).start()
        if shout:
            print(f'after {self.asteroid.get_pos(self.planet.root)}')


    def destroy(self):
        self.collider.clear_python_tag('asteroid')
        self.collider.remove_node()
        self.asteroid.remove_node()
        self.root.remove_node()
        self.universe.asteroids.pop(self.universe.asteroids.index(self))

    def stop(self):
        self._orbit_ival.pause()
        self._spin_ival.pause()
