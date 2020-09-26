#!/usr/bin/python
# -*- coding: utf-8 -*-

# This file was created using the DirectGUI Designer

from direct.gui import DirectGuiGlobals as DGG

from direct.gui.DirectCheckBox import DirectCheckBox
from direct.gui.DirectSlider import DirectSlider
from direct.gui.DirectOptionMenu import DirectOptionMenu
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

        self.cmbResolution = DirectOptionMenu(
            items=['item1'],
            frameColor=(0.8, 0.8, 0.8, 0.0),
            frameSize=(-2.312, 2.312, -0.463, 0.463),
            hpr=LVecBase3f(0, 0, 0),
            image='./textures/ResolutionBox.png',
            pos=LPoint3f(0, 0, -0.3),
            relief=1,
            scale=LVecBase3f(0.1, 0.1, 0.1),
            text='1920x1080',
            cancelframe_frameSize=(-1, 1, -1, 1),
            cancelframe_hpr=LVecBase3f(0, 0, 0),
            cancelframe_pos=LPoint3f(0, 0, 0),
            cancelframe_relief=None,
            image_scale=LVecBase3f(2.312, 1, 0.4625),
            image_pos=LPoint3f(0, 0, 0),
            item_frameSize=(0.07500000298023224, 2.4125001430511475, -0.11250001192092896, 0.75),
            item_hpr=LVecBase3f(0, 0, 0),
            item_pos=LPoint3f(-0.075, 0, -0.75),
            item_text='item1',
            item0_text_align=TextNode.A_left,
            item0_text_scale=(1, 1),
            item0_text_pos=(0, 0),
            item0_text_fg=LVecBase4f(0, 0, 0, 1),
            item0_text_bg=LVecBase4f(0, 0, 0, 0),
            item0_text_wordwrap=None,
            popupMarker_frameSize=(-0.5, 0.5, -0.2, 0.2),
            popupMarker_hpr=LVecBase3f(0, 0, 0),
            popupMarker_pos=LPoint3f(2.7125, 0, 0.31875),
            popupMarker_relief=2,
            popupMarker_scale=LVecBase3f(0.4, 0.4, 0.4),
            popupMenu_frameSize=(0, 2.3375001400709152, -0.862500011920929, 0),
            popupMenu_hpr=LVecBase3f(0, 0, 0),
            popupMenu_pos=LPoint3f(0, 0, 0),
            popupMenu_relief='raised',
            text_align=TextNode.A_center,
            text_scale=(1, 1),
            text_pos=(-0.05, -0.25),
            text_fg=LVecBase4f(1, 1, 1, 1),
            text_bg=LVecBase4f(0, 0, 0, 0),
            text_wordwrap=None,
            parent=rootParent,
        )
        self.cmbResolution.setTransparency(2)


    def show(self):
        self.cbAudio.show()
        self.sliderVolume.show()
        self.cbFullscreen.show()
        self.cbGraphicMode.show()
        self.cmbResolution.show()

    def hide(self):
        self.cbAudio.hide()
        self.sliderVolume.hide()
        self.cbFullscreen.hide()
        self.cbGraphicMode.hide()
        self.cmbResolution.hide()

    def destroy(self):
        self.cbAudio.destroy()
        self.sliderVolume.destroy()
        self.cbFullscreen.destroy()
        self.cbGraphicMode.destroy()
        self.cmbResolution.destroy()
