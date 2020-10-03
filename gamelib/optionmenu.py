import sys

import panda3d.core as p3d
from direct.showbase.DirectObject import DirectObject
from direct.interval import IntervalGlobal as intervals

#from .mainmenu import MainMenu
from .skybox import Skybox
from .optionmenuGUI import GUI as OptionGUI
from .util import srgb_color

import os
from panda3d.core import (
    ConfigPageManager,
    OFileStream,
    loadPrcFile,
    Filename,
    ExecutionEnvironment,
    WindowProperties,
    ConfigVariableBool)

class OptionMenu(DirectObject, OptionGUI):
    def __init__(self):
        super().__init__()
        OptionGUI.__init__(self)

        self.root = base.loader.load_model('models/generalMenu.bam')
        self.root.reparent_to(base.render)
        self.root.set_y(15)

        self.skybox = Skybox(self.root)

        self.traverser = p3d.CollisionTraverser()
        self.ray = p3d.CollisionRay()
        picker = p3d.CollisionNode('picker')
        picker.add_solid(self.ray)
        picker.set_from_collide_mask(1)
        picker.set_into_collide_mask(0)
        self.picker = self.root.attach_new_node(picker)
        self.picker_handler = p3d.CollisionHandlerQueue()
        self.traverser.add_collider(self.picker, self.picker_handler)

        scene_camera = self.root.find('**/-Camera')
        campos = scene_camera.get_pos(self.root)
        base.camera.set_pos(campos)
        self.picker.reparent_to(base.camera)

        self.accept('mouse1-up', self.handle_click)

        base.transitions.fadeIn()

        ## AUDIO VOLUME
        self.sliderMusicVolume.setValue(base.musicManager.getVolume())
        self.sliderMusicVolume["command"] = self.sliderMusicVolumeChanged
        self.sliderSFXVolume.setValue(base.sfxManagerList[0].getVolume())
        self.sliderSFXVolume["command"] = self.sliderSFXVolumeChanged

        ## Music AUDIO MUTE TOGGLE
        self.cbMusicAudio["isChecked"] = base.musicActive
        if self.cbMusicAudio['isChecked']:
            self.cbMusicAudio['image'] = self.cbMusicAudio['checkedImage']
        else:
            self.cbMusicAudio['image'] = self.cbMusicAudio['uncheckedImage']
        self.cbMusicAudio.setImage()
        self.cbMusicAudio["command"] = self.cbMusicAudioChanged

        ## SFX AUDIO MUTE TOGGLE
        self.cbSFXAudio["isChecked"] = base.musicActive
        if self.cbSFXAudio['isChecked']:
            self.cbSFXAudio['image'] = self.cbSFXAudio['checkedImage']
        else:
            self.cbSFXAudio['image'] = self.cbSFXAudio['uncheckedImage']
        self.cbSFXAudio.setImage()
        self.cbSFXAudio["command"] = self.cbSFXAudioChanged

        ## FULLSCREEN
        self.cbFullscreen["isChecked"] = base.win.isFullscreen()
        if self.cbFullscreen['isChecked']:
            self.cbFullscreen['image'] = self.cbFullscreen['checkedImage']
        else:
            self.cbFullscreen['image'] = self.cbFullscreen['uncheckedImage']
        self.cbFullscreen.setImage()
        self.cbFullscreen["command"] = self.cbFullscreenChanged

        ## GRAPHICS MODE
        self.cbGraphicMode["isChecked"] = ConfigVariableBool('potato-mode', False).get_value()
        if self.cbGraphicMode['isChecked']:
            self.cbGraphicMode['image'] = self.cbGraphicMode['checkedImage']
        else:
            self.cbGraphicMode['image'] = self.cbGraphicMode['uncheckedImage']
        self.cbGraphicMode.setImage()
        self.cbGraphicMode["command"] = self.cbGraphicModeChanged

        ## SCREEN RESOLUTION
        # Setting the items like this somehow breaks the mute button...

        self.windowSizeX = base.win.getXSize()
        self.windowSizeY = base.win.getYSize()
        # get the display resolutions
        di = base.pipe.getDisplayInformation()
        sizes = []
        for index in range(di.getTotalDisplayModes()):
            tmptext = "{0}x{1}".format(
                di.getDisplayModeWidth(index),
                di.getDisplayModeHeight(index))
            # keep the sizes reasonable
            if di.getDisplayModeWidth(index) < 800: continue
            if di.getDisplayModeHeight(index) < 600: continue
            if not tmptext in sizes:
                sizes.append(tmptext)
        selected = 0
        if sizes == []:
            sizes.append("800x600")
            sizes.append("960x540")
            sizes.append("1280x720")
            sizes.append("1920x1080")
        curSize = "{}x{}".format(self.windowSizeX, self.windowSizeY)
        if curSize not in sizes:
            sizes.append(curSize)
        for i in range(len(sizes)):
            if sizes[i].split("x")[0] == str(self.windowSizeX) \
            and sizes[i].split("x")[1] == str(self.windowSizeY):
                selected = i
                break

        self.cmbResolution["frameSize"] = (-2.712, 2.712, -0.563, 0.563)
        self.cmbResolution["image_scale"]= (2.712, 1, 0.563)
        self.cmbResolution["highlightColor"] = srgb_color(0xfb4771)
        self.cmbResolution.popupMarker["frameColor"] = (0,0,0,0)
        self.cmbResolution["items"] = sizes
        self.cmbResolution.set(selected, fCommand = 0)
        self.cmbResolution["command"] = self.cmbResolutionChanged

        ## INVERT Y AXIS TOGGLE
        self.cbInvertAxis["isChecked"] = p3d.ConfigVariableBool('invert-y-axis', False)
        if self.cbInvertAxis['isChecked']:
            self.cbInvertAxis['image'] = self.cbInvertAxis['checkedImage']
        else:
            self.cbInvertAxis['image'] = self.cbInvertAxis['uncheckedImage']
        self.cbInvertAxis.setImage()
        self.cbInvertAxis["command"] = self.cbInvertAxisChanged

        base.set_bgm('credits')

        self.accept('escape', self.back)

    def cleanup(self):
        self.root.remove_node()
        self.picker.remove_node()
        self.destroy()
        self.ignore_all()

    def handle_click(self):
        if not base.mouseWatcherNode.has_mouse():
            return

        mpos = base.mouseWatcherNode.get_mouse()
        self.ray.set_from_lens(base.cam.node(), *mpos)

        self.traverser.traverse(self.root)

        self.picker_handler.sort_entries()
        for entry in self.picker_handler.entries:
            npname = entry.getIntoNodePath().name

            if npname == 'BackSignSign':
                self.back()
                break

    def back(self):
        self.ignore('escape')
        self.writeConfig()
        base.change_state('MainMenu')
        # self.cleanup()

    def sliderMusicVolumeChanged(self):
        volume = round(self.sliderMusicVolume["value"], 2)
        self.sliderMusicVolume["text"] = "Music Volume: {}%".format(int(volume * 100))
        base.musicManager.setVolume(volume)

    def sliderSFXVolumeChanged(self):
        volume = round(self.sliderSFXVolume["value"], 2)
        self.sliderSFXVolume["text"] = "SFX Volume: {}%".format(int(volume * 100))
        base.sfxManagerList[0].setVolume(volume)

    def cbMusicAudioChanged(self, args=None):
        base.enableMusic(self.cbMusicAudio["isChecked"])

    def cbSFXAudioChanged(self, args=None):
        base.enableSoundEffects(self.cbSFXAudio["isChecked"])

    def cbFullscreenChanged(self, args=None):
        # get the window properties and clear them
        props = WindowProperties()
        props.clearFullscreen()

        # are we fullscreen yet
        fullscreen = base.win.isFullscreen()
        # for clarity set a variable that determines to which state
        # we want to switch
        props.setFullscreen(not fullscreen)
        props.setUndecorated(not fullscreen)

        base.win.requestProperties(props)

    def cbGraphicModeChanged(self, args=None):
        potato_mode = self.cbGraphicMode['isChecked']
        base.set_graphics_quality(potato_mode)
        ConfigVariableBool('potato-mode').setValue(potato_mode)

    def cmbResolutionChanged(self, args):
        resx = int(args.split("x")[0])
        resy = int(args.split("x")[1])
        props = WindowProperties()

        # get the window properties and clear them
        props = WindowProperties()
        props.clear()
        props.clearSize()
        props.setSize(resx, resy)

        base.win.requestProperties(props)
        base.taskMgr.step()

    def cbInvertAxisChanged(self, args=None):
        invert = self.cbInvertAxis['isChecked']
        ConfigVariableBool('invert-y-axis').setValue(invert)

    def writeConfig(self):
        """Save current config in the prc file or if no prc file exists
        create one. The prc file is set in the prcFile variable"""
        page = None
        rootDir = ExecutionEnvironment.getEnvironmentVariable("MAIN_DIR")
        prcFile = os.path.join(rootDir, "user.prc")

        #
        #TODO: add any configuration variable names that you have added
        #      to the dictionaries in the next lines. Set the current
        #      configurations value as value in this dictionary and it's
        #      name as key.
        configVariables = {
            "audio-music-volume": str(round(base.musicManager.getVolume(), 2)),
            "audio-sfx-volume": str(round(base.sfxManagerList[0].getVolume(), 2)),
            "audio-music-active": "true" if self.cbMusicAudio["isChecked"] else "false",
            "audio-sfx-active": "true" if self.cbSFXAudio["isChecked"] else "false",
            "fullscreen": "true" if self.cbFullscreen["isChecked"] else "false",
            "win-size": "{} {}".format(base.win.getXSize(), base.win.getYSize()),
            "potato-mode": "true" if ConfigVariableBool('potato-mode', False).get_value() else "false",
            "invert-y-axis": "true" if ConfigVariableBool('invert-y-axis', False).get_value() else "false",
            }

        page = None
        # Check if we have an existing configuration file
        if os.path.exists(prcFile):
            # open the config file and change values according to current
            # application settings
            page = loadPrcFile(Filename.fromOsSpecific(prcFile))
            removeDecls = []
            for dec in range(page.getNumDeclarations()):
                # Check if our variables are given.
                # NOTE: This check has to be done to not loose our base
                #       or other manual config changes by the user
                if page.getVariableName(dec) in configVariables.keys():
                    removeDecls.append(page.modifyDeclaration(dec))
            for dec in removeDecls:
                page.deleteDeclaration(dec)
        else:
            # Create a config file and set default values
            cpMgr = ConfigPageManager.getGlobalPtr()
            page = cpMgr.makeExplicitPage("Application Config")

        # always write custom configurations
        for key, value in configVariables.items():
            page.makeDeclaration(key, value)
        # create a stream to the specified config file
        configfile = OFileStream(prcFile)
        # and now write it out
        page.write(configfile)
        # close the stream
        configfile.close()

    def update(self, dt):
        pass
