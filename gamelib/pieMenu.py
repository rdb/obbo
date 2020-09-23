#!/usr/bin/python
# -*- coding: utf-8 -*-

# This file was created using the DirectGUI Designer

import math

from direct.gui import DirectGuiGlobals as DGG

from direct.gui.DirectButton import DirectButton
from direct.gui.DirectGui import DirectFrame
from panda3d.core import (
    LPoint3f,
    LVecBase3f,
    LVecBase4f,
    TextNode,
    Vec3,
    Point3,
    OmniBoundingVolume
)
from direct.interval.IntervalGlobal import Parallel, Sequence, Func

from direct.showbase import DirectObject
# We need showbase to make this script directly runnable
from direct.showbase.ShowBase import ShowBase

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
        self.buildings = loader.loadModel("../.built_assets/models/buildings.bam")
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
        self.hide()

    def updateCircle(self, newItems):
        self.numItems = len(items)
        self.items = newItems

        self.menuCircle = DirectFrame(
            image="../.built_assets/textures/PieMenuCircle.png",
            frameSize=(-1,1,-1,1),
            frameColor=(0,0,0,0),
            pos=(self.menu_x, 0, self.menu_y)
        )
        self.menuCircle.setBin('gui-popup', 1)
        self.menuCircle.setTransparency(1)

        degreeSteps = 360 / self.numItems

        self.buttons = []

        i = 0
        for item in self.items:

            x = 0.75*math.cos(i*degreeSteps*math.pi/180)
            y = 0.75*math.sin(i*degreeSteps*math.pi/180)

            self.buttons.append(self.createButton(x,y,item))
            i += 1

    def createButton(self, x, y, item):
        geom = self.buildings.find("**/{}".format(item.buildingName))
        geom.setDepthWrite(True)
        geom.setDepthTest(True)
        geom.reparentTo(render)

        #smiley = loader.loadModel("smiley")
        #smiley.setR(45)
        # Now, due to the fact that button geometry  will be rendered
        # with render2d, which has z-buffering deactivated by default,
        # we need to explicitely enable it the models we want to apply
        # to the button or any other DirectGUI element.
        #smiley.setDepthWrite(True)
        #smiley.setDepthTest(True)
        #geom = smiley


        #self.buildings.setDepthWrite(True)
        #self.buildings.setDepthTest(True)
        self.buildings.setScale(1)
        #geom.setX(0)
        #geom = self.buildings


        btn = DirectButton(
            #frameColor=(0.0, 0.0, 0.0, 0.0),
            frameSize=(-1.0, 1.0, -1.0, 1.0),
            #hpr=LVecBase3f(0, 0, 0),
            pos=LPoint3f(x, 0, y),
            relief=None,#DGG.FLAT,
            scale=LVecBase3f(0.25, 0.25, 0.25),
            geom=geom,
            parent=self.menuCircle,
            pressEffect=False,
            command=base.messenger.send,
            extraArgs=item.event
        )
        btn.setBin('gui-popup', 2)
        btn.setTransparency(1)
        return btn

    def show(self, x=0, y=0):

        if base.win.getXSize() > base.win.getYSize():
            screenResMultiplier_x = base.win.getXSize() / base.win.getYSize()
            screenResMultiplier_y = 1
        else:
            screenResMultiplier_x = 1
            screenResMultiplier_y = base.win.getYSize() / base.win.getXSize()
        x = base.mouseWatcherNode.getMouseX() * screenResMultiplier_x
        y = base.mouseWatcherNode.getMouseY() * screenResMultiplier_y
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
        self.menuCircle.destroy()

# Create a ShowBase instance to make this gui directly runnable
app = ShowBase()

items = [
        PieMenuItem("Blubb 1", "bla", "tent"),
        PieMenuItem("Blubb A", "bla", "windmill"),
        PieMenuItem("Blubb B", "bla", "chest"),
        PieMenuItem("Blubb C", "bla", "replicator"),
        PieMenuItem("Blubb D", "bla", "garage")
]

menu = PieMenu(items)
do = DirectObject.DirectObject()
do.accept("mouse1", menu.show)
app.run()
