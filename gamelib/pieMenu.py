#!/usr/bin/python
# -*- coding: utf-8 -*-

import math

from direct.gui import DirectGuiGlobals as DGG

from direct.gui.DirectGui import DirectFrame, DirectButton
from panda3d.core import (
    LPoint3f,
    LVecBase3f,
    LVecBase4f,
    TextNode,
    NodePath,
    Vec3,
    Point3,
    OmniBoundingVolume
)
from direct.interval.IntervalGlobal import Parallel, Sequence, Func

class PieMenuItem:
    def __init__(self, name, event, buildingName):
        self.name = name
        self.event = event
        self.buildingName = buildingName

class PieMenu:
    def __init__(self, items=[]):
        self.menu_x = 0
        self.menu_y = 0
        self.menuSize = 0.5
        self.buildings = loader.loadModel("models/buildings.bam")
        #self.buildings.reparentTo(render)
        # A big screen encompassing frame to catch the cancel clicks
        self.cancelFrame = DirectFrame(
            frameSize = (base.a2dLeft, base.a2dRight, base.a2dBottom, base.a2dTop),
            frameColor=(0,0,0,0),
            state = 'normal')
        # Make sure this is on top of all the other widgets
        self.cancelFrame.setBin('gui-popup', 0)
        self.cancelFrame.node().setBounds(OmniBoundingVolume())
        self.cancelFrame.bind(DGG.B1PRESS, self.hide)

        self.updateCircle(items)

        self.menuCircle.hide()
        self.cancelFrame.hide()

    def updateCircle(self, newItems):
        self.numItems = len(newItems)
        self.items = newItems

        self.menuCircle = DirectFrame(
            image="textures/PieMenuCircle.png",
            frameSize=(-1,1,-1,1),
            frameColor=(0,0,0,0),
            pos=(self.menu_x, 0, self.menu_y)
        )
        self.menuCircle.setBin('gui-popup', 1)
        self.menuCircle.setTransparency(1)

        degreeSteps = 360 / self.numItems

        self.buttons = []

        for i, item in enumerate(self.items):

            x = 0.75*math.cos(i*degreeSteps*math.pi/180)
            y = 0.75*math.sin(i*degreeSteps*math.pi/180)

            self.buttons.append(self.createButton(x,y,item))

    def createButton(self, x, y, item):
        building = self.buildings.find("**/{}".format(item.buildingName))
        geom = NodePath("geom")
        geom.setDepthWrite(True)
        geom.setDepthTest(True)
        geom.setTransparency(0,10)
        geom.setPos(0,0,-0.5)
        geom.setHpr(-45, 15, 15)
        geom.set_texture_off(10)
        building.copy_to(geom).clear_transform()

        btn = DirectButton(
            text=item.name,
            text_scale=0.5,
            text_pos=(0,-1),
            text_fg=(1, 1, 1, 1),
            frameSize=(-1.0, 1.0, -1.0, 1.0),
            pos=LPoint3f(x, 0, y),
            relief=None,
            scale=0.25,
            geom=geom,
            geom_scale=0.25,
            parent=self.menuCircle,
            pressEffect=False,
            command=base.messenger.send,
            extraArgs=(item.event,)
        )
        btn.setBin('gui-popup', 2)
        btn.setTransparency(1)

        ival = btn["geom2_geom"].get_child(0).hprInterval(1, (360, 0, 0), (0, 0, 0))
        btn.bind(DGG.ENTER, lambda x: ival.loop())
        btn.bind(DGG.EXIT, lambda x: ival.finish())
        return btn

    def show(self, x=None, y=None):
        if not base.mouseWatcherNode.hasMouse():
            return

        if base.win.getXSize() > base.win.getYSize():
            screenResMultiplier_x = base.win.getXSize() / base.win.getYSize()
            screenResMultiplier_y = 1
        else:
            screenResMultiplier_x = 1
            screenResMultiplier_y = base.win.getYSize() / base.win.getXSize()
        x = base.mouseWatcherNode.getMouseX() * screenResMultiplier_x if x is None else x
        y = base.mouseWatcherNode.getMouseY() * screenResMultiplier_y if y is None else y
        self.menu_x = x
        self.menu_y = y
        self.cancelFrame.show()
        self.menuCircle.setPos(x, 0, y)
        self.menuCircle.show()
        interval_duration = 0.3
        Parallel(
            self.menuCircle.scaleInterval(interval_duration, self.menuSize, 0.1),
            self.menuCircle.hprInterval(interval_duration, Vec3(0, 0, -360), Vec3(0, 0, -180))).start()


    def hide(self, args=None):
        interval_duration = 0.15
        Sequence(
            Parallel(
                self.menuCircle.scaleInterval(interval_duration, 0.1, self.menuSize),
                self.menuCircle.hprInterval(interval_duration, Vec3(0, 0, -180), Vec3(0, 0, 360))),
            Func(self.menuCircle.hide)
            ).start()
        self.cancelFrame.hide()

    def destroy(self):
        self.cancelFrame.destroy()
        self.menuCircle.destroy()

'''
# We need showbase to make this script directly runnable
from direct.showbase.ShowBase import ShowBase

# Create a ShowBase instance to make this gui directly runnable
app = ShowBase()

# item contains the Name (text on the button), event to be fired on button click and the node name from within the buildings.bam file
items = [
        PieMenuItem("Tent", "build_tent", "tent"),
        PieMenuItem("Windmill", "build_windmill", "windmill"),
        PieMenuItem("Chest", "build_chest", "chest"),
        PieMenuItem("Replicator", "build_replicator", "replicator"),
        PieMenuItem("Garage", "build_garage", "garage")
]

menu = PieMenu(items)
app.accept("mouse1", menu.show)
app.run()
'''
