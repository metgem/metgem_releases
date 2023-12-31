#-----------------------------------------------------------------------------
# Copyright (c) 2014-2021, PyInstaller Development Team.
#
# Distributed under the terms of the GNU General Public License (version 2
# or later) with exception for distributing the bootloader.
#
# The full license is in the file COPYING.txt, distributed with this software.
#
# SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
#-----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import pyside2_library_info, \
    add_qt5_dependencies, get_qt_webengine_binaries_and_data_files
from PyInstaller import compat
import os

# Ensure PyQt5 is importable before adding info depending on it.
if pyside2_library_info.version is not None:
    hiddenimports, binaries, datas = add_qt5_dependencies(__file__)

    # Include helper process executable, translations, and resources.
    webengine_binaries, webengine_datas = \
        get_qt_webengine_binaries_and_data_files(pyside2_library_info)

    if compat.is_darwin:
        webengine_datas += [(os.path.join(pyside2_library_info.location['DataPath'], 'resources'), os.curdir),
                            (os.path.join(pyside2_library_info.location['DataPath'], 'libexec', 'QtWebEngineProcess'), os.curdir)]
        webengine_datas = [(x,y) for x,y in webengine_datas if os.path.exists(x)]

    binaries += webengine_binaries
    datas += webengine_datas
