import sys

import panda3d.core as p3d
from direct.showbase.DirectObject import DirectObject
from direct.interval import IntervalGlobal as intervals

#from .mainmenu import MainMenu
from .skybox import Skybox
from .optionmenuGUI import GUI as OptionGUI

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
        self.picker.set_pos(campos)

        self.accept('mouse1-up', self.handle_click)

        base.transitions.fadeIn()

        self.sliderVolume.setValue(base.musicManager.getVolume())
        self.sliderVolume["command"] = self.sliderVolumeChanged

        self.cbAudio["isChecked"] = base.musicActive
        if self.cbAudio['isChecked']:
            self.cbAudio['image'] = self.cbAudio['checkedImage']
        else:
            self.cbAudio['image'] = self.cbAudio['uncheckedImage']
        self.cbAudio.setImage()
        self.cbAudio["command"] = self.cbAudioChanged

        self.cbFullscreen["isChecked"] = base.win.isFullscreen()
        if self.cbFullscreen['isChecked']:
            self.cbFullscreen['image'] = self.cbFullscreen['checkedImage']
        else:
            self.cbFullscreen['image'] = self.cbFullscreen['uncheckedImage']
        self.cbFullscreen.setImage()
        self.cbFullscreen["command"] = self.cbFullscreenChanged

        self.cbGraphicMode["isChecked"] = ConfigVariableBool('potato-mode', False).get_value()
        if self.cbGraphicMode['isChecked']:
            self.cbGraphicMode['image'] = self.cbGraphicMode['checkedImage']
        else:
            self.cbGraphicMode['image'] = self.cbGraphicMode['uncheckedImage']
        self.cbGraphicMode.setImage()
        self.cbGraphicMode["command"] = self.cbGraphicModeChanged

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
                self.writeConfig()
                self.cleanup()
                #ival = base.transitions.getFadeOutIval()
                #def change_state():
                from .mainmenu import MainMenu
                base.gamestate = MainMenu()
                #ival.append(intervals.Func(change_state))
                #ival.start()
                break

    def sliderVolumeChanged(self):
        volume = round(self.sliderVolume["value"], 2)
        self.sliderVolume["text"] = "Volume: {}%".format(int(volume * 100))
        base.musicManager.setVolume(volume)
        base.sfxManagerList[0].setVolume(volume)

    def cbAudioChanged(self, args=None):
        base.enableSoundEffects(self.cbAudio["isChecked"])
        base.enableMusic(self.cbAudio["isChecked"])

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
        ConfigVariableBool('potato-mode').setValue(self.cbGraphicMode['isChecked'])

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
            "audio-volume": str(round(base.musicManager.getVolume(), 2)),
            "audio-music-active": "#t" if self.cbAudio["isChecked"] else "#f",
            "audio-sfx-active": "#t" if self.cbAudio["isChecked"] else "#f",
            "fullscreen": "#t" if self.cbFullscreen["isChecked"] else "#f",
            "potato-mode": "#t" if ConfigVariableBool('potato-mode', False).get_value() else "#f",
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
