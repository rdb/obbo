#!/usr/bin/python
# -*- coding: utf-8 -*-

# This file was created using the DirectGUI Designer

from direct.gui import DirectGuiGlobals as DGG

from direct.gui.DirectCheckBox import DirectCheckBox
from direct.gui.DirectSlider import DirectSlider
from panda3d.core import (
    LPoint3f,
    LVecBase3f,
    LVecBase4f,
    TextNode
)

class GUI:
    def __init__(self, rootParent=None):
        
        self.cbAudio = DirectCheckBox(
            checkedImage='textures/AudioOption_On.png',
            frameColor=(0.8, 0.8, 0.8, 0.0),
            frameSize=(-1.0, 1.0, -1.0, 1.0),
            hpr=LVecBase3f(0, 0, 0),
            image='textures/AudioOption_On.png',
            isChecked=True,
            pos=LPoint3f(0, 0, 0.59),
            relief=1,
            scale=LVecBase3f(0.1, 0.1, 0.1),
            uncheckedImage='textures/AudioOption_Off.png',
            image_scale=LVecBase3f(1, 1, 1),
            image_pos=LPoint3f(0, 0, 0),
            parent=rootParent,
        )
        self.cbAudio.setTransparency(2)

        self.sliderVolume = DirectSlider(
            frameColor=(0.678, 0.427, 0.918, 1.0),
            hpr=LVecBase3f(0, 0, 0),
            pos=LPoint3f(0, 0, 0.27),
            text='Volume: 0%',
            text_align=TextNode.A_center,
            text_scale=(0.1, 0.1),
            text_pos=(0.0, 0.1),
            text_fg=LVecBase4f(0.992, 1, 1, 1),
            text_bg=LVecBase4f(0, 0, 0, 0),
            text_wordwrap=None,
            thumb_frameColor=(0.8, 0.8, 0.8, 0.0),
            thumb_frameSize=(-0.05, 0.05, -0.08, 0.08),
            thumb_hpr=LVecBase3f(0, 0, 0),
            thumb_image='textures/sliderThumb.png',
            thumb_pos=LPoint3f(-0.95, 0, 0),
            thumb_image_scale=LVecBase3f(0.05, 1, 0.08),
            thumb_image_pos=LPoint3f(0, 0, 0),
            parent=rootParent,
        )
        self.sliderVolume.setTransparency(1)

        self.cbFullscreen = DirectCheckBox(
            checkedImage='textures/Fullscreen_On.png',
            frameColor=(0.8, 0.8, 0.8, 0.0),
            frameSize=(-1.0, 1.0, -1.0, 1.0),
            hpr=LVecBase3f(0, 0, 0),
            image='textures/Fullscreen_On.png',
            isChecked=True,
            pos=LPoint3f(-0.25, 0, 0),
            relief=1,
            scale=LVecBase3f(0.1, 0.1, 0.1),
            uncheckedImage='textures/Fullscreen_Off.png',
            image_scale=LVecBase3f(1, 1, 1),
            image_pos=LPoint3f(0, 0, 0),
            parent=rootParent,
        )
        self.cbFullscreen.setTransparency(2)

        self.cbGraphicMode = DirectCheckBox(
            checkedImage='textures/GraphicModeLow.png',
            frameColor=(0.8, 0.8, 0.8, 0.0),
            frameSize=(-1.0, 1.0, -1.0, 1.0),
            hpr=LVecBase3f(0, 0, 0),
            image='textures/GraphicModeLow.png',
            isChecked=True,
            pos=LPoint3f(0.25, 0, 0),
            relief=1,
            scale=LVecBase3f(0.1, 0.1, 0.1),
            uncheckedImage='textures/GraphicModeHigh.png',
            image_scale=LVecBase3f(1, 1, 1),
            image_pos=LPoint3f(0, 0, 0),
            parent=rootParent,
        )
        self.cbGraphicMode.setTransparency(2)


    def show(self):
        self.cbAudio.show()
        self.sliderVolume.show()
        self.cbFullscreen.show()
        self.cbGraphicMode.show()

    def hide(self):
        self.cbAudio.hide()
        self.sliderVolume.hide()
        self.cbFullscreen.hide()
        self.cbGraphicMode.hide()

    def destroy(self):
        self.cbAudio.destroy()
        self.sliderVolume.destroy()
        self.cbFullscreen.destroy()
        self.cbGraphicMode.destroy()
