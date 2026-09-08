# -*- coding: utf-8 -*-
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "resources", "lib"))

import xbmcgui
from resources.lib import apo_writer, addon_settings as settings
from resources.lib.gui import MixerWindow


def _check_config_path():
    path = settings.get_config_path()
    if not path or not os.path.isdir(os.path.dirname(path)):
        xbmcgui.Dialog().ok(
            "Audio Channel Mixer",
            "La ruta de config.txt no es valida:\n%s\n\n"
            "Configurala en Ajustes del addon." % path)
        return False
    return True


if __name__ == "__main__":
    if _check_config_path():
        window = MixerWindow()
        window.run()
        del window
