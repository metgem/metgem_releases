# -*- mode: python ; coding: utf-8 -*-
import importlib.metadata
import os
import sys
import glob

from distutils.core import run_setup
from importlib.metadata import distribution, packages_distributions

# noinspection PyUnresolvedReferences
sys.path.insert(0, os.path.join(SPECPATH, 'metgem'))
# noinspection PyUnresolvedReferences
sys.path.insert(0, os.path.join(SPECPATH, 'build', 'lib'))


# from PyInstaller.utils.hooks.qt import qt_plugins_binaries
from PyInstaller.utils.hooks import get_module_file_attribute


# noinspection PyUnresolvedReferences
def clean_datas(a: Analysis):
    # Remove unused IPython data files
    a.datas = [dat for dat in a.datas if not dat[0].startswith('IPython')]

    # Remove unused pytz data files
    a.datas = [dat for dat in a.datas if not dat[0].startswith('pytz')]

    # Remove matplotlib sample data
    a.datas = [dat for dat in a.datas if not ('sample_data' in dat[0] and dat[0].startswith('mpl-data'))]

    return a


def clean_system_libraries(a: Analysis):
    '''On anaconda, some libraries packaged in virtual environment are taken
    from system instead of environment. Make sure to use virtual environment files'''
    
    bins = {}
    for name, path, typ in a.binaries:
        if path.startswith('/lib') or path.startswith('/usr/lib'):
            venv_path = os.path.join(sys.prefix, 'lib', name)
            if os.path.exists(venv_path):
                bins[name] = (name, venv_path, typ)
    a.binaries = [(name, path, typ) for name, path, typ in a.binaries if name not in bins.keys()]
    a.binaries.extend(bins.values())
    
    return a

# https://github.com/pyinstaller/pyinstaller/wiki/Recipe-Setuptools-Entry-Point
# noinspection PyUnresolvedReferences
def Entrypoint(dist, group, name, **kwargs):
    # get toplevel packages of distribution from metadata
    def get_toplevel(dist):
        try:
            distrib = distribution(dist)
        except importlib.metadata.PackageNotFoundError:
            return [dist]
        else:
            content = distrib.read_text('top_level.txt')
            return list(content.split()) if content else [dist]

    kwargs.setdefault('hiddenimports', [])
    packages = []
    packages_distribs = packages_distributions()
    for distrib in kwargs['hiddenimports']:
        for d in packages_distribs.get(distrib, [distrib]):
            packages += get_toplevel(d)

    kwargs.setdefault('pathex', [])
    # get the entry point
    distrib = distribution(dist)
    ep, = distrib.entry_points.select(group=group, name=name)
    # insert path of the egg at the verify front of the search path
    kwargs['pathex'] = [str(ep.dist._path)] + kwargs['pathex']
    # script name must not be a valid module name to avoid name clashes on import
    script_path = os.path.join(workpath, name + '-script.py')
    print("Creating script for entry point...", dist, group, name, end=' ')
    with open(script_path, 'w') as fh:
        print("import", ep.module, file=fh)
        print("%s.%s()" % (ep.module, ep.attr), file=fh)
        for package in packages:
            print("import", package, file=fh)
    print("[OK]")

    return Analysis(
        [script_path] + kwargs.get('scripts', []),
        **kwargs
    )

# if --debug flag is passed, make a debug release
DEBUG = '--debug' in sys.argv

pathex = []
binaries = []
datas = []
hookspath = []
runtime_hooks = []
hiddenimports = ['pytest', 'pytestqt', 'pytest_mock']
excludes = []

coll_name = 'MetGem'
if DEBUG:
    coll_name += '_debug'

# Add ui_rc module in datas
datas += [(os.path.join('metgem', 'metgem', 'ui', 'ui_rc.py'), os.path.join('metgem', 'ui'))]

# Add plugins in datas
# noinspection PyUnresolvedReferences
datas += [(f, os.path.join("metgem", "plugins"))
          for f in glob.glob(os.path.join(SPECPATH, 'metgem', 'metgem', 'plugins', '*.py'))
          if os.path.basename(f) != '__init__.py']

# Add tests in datas
# noinspection PyUnresolvedReferences
datas += [(f, "tests") for f in glob.glob(os.path.join(SPECPATH, 'metgem', 'tests', '**', '*.py'))]
# noinspection PyUnresolvedReferences
datas += [(os.path.join(SPECPATH, 'metgem', 'pytest.ini'), '.')]

# Get data from setup.py
# noinspection PyUnresolvedReferences
distrib = run_setup(os.path.join(SPECPATH, "metgem", "setup.py"), stop_after="init")
for f in distrib.package_data['metgem']:
    # noinspection PyUnresolvedReferences
    path = os.path.join(workpath, "lib", "metgem", f)
    # noinspection PyUnresolvedReferences
    alt_path = os.path.join(SPECPATH, "metgem", "metgem", f)
    dest_path = os.path.join("metgem", os.path.dirname(f))
    if os.path.exists(path):
        datas.append((path, dest_path))
    else:
        datas.append((alt_path, dest_path))
        
for d, files in distrib.data_files:
    for f in files:
        # noinspection PyUnresolvedReferences
        datas.append((os.path.join(SPECPATH, "metgem", f), d if d else "."))
            
version = distrib.get_version()
print(f"VERSION FOUND FROM SETUP: {version}")

# noinspection PyUnresolvedReferences
with open(os.path.join(workpath, '.stub'), 'w') as fp: 
    pass
# noinspection PyUnresolvedReferences
datas.append((os.path.join(workpath, '.stub'), "Library/bin"))

# Encrypt files?
block_cipher = None

# Remove Tkinter: https://github.com/pyinstaller/pyinstaller/wiki/Recipe-remove-tkinter-tcl
sys.modules['FixTk'] = None
excludes.extend(['FixTk', 'tcl', 'tk', '_tkinter', 'tkinter', 'Tkinter', 'matplotlib.backends._tkagg'])

# Remove lib2to3
excludes.extend(['lib2to3'])

# Try to locate Qt base directory
qt_base_dir = os.path.join(os.path.dirname(get_module_file_attribute('PySide6')), 'Qt')
if not os.path.exists(qt_base_dir):
    qt_base_dir = os.path.join(sys.prefix, 'Library')

# Add some useful folders to path
if sys.platform.startswith('win'):
    pathex.append(os.path.join(sys.prefix, 'Lib', 'site-packages', 'scipy', 'extra-dll'))
    pathex.append(os.path.join(sys.prefix, 'Library', 'bin'))
    pathex.append(os.path.join('C:', 'Program Files', 'OpenSSL', 'bin'))

# Adds Qt OpenGL
hiddenimports.extend(['PySide6.QtOpenGL'])

# Add Qt Dbus on macOS
if sys.platform.startswith('darwin'):
    hiddenimports.extend(['PySide6.QtDBus'])
    
# Add missing modules
hiddenimports.extend(['pyarrow.vendored'])

# Add pybel
try:
    # noinspection PyPackageRequirements
    import pybel
except ImportError:
    pass
else:
    hiddenimports.extend(['pybel'])

# Add phate
try:
    # noinspection PyPackageRequirements
    import phate
except ImportError:
    pass
else:
    hiddenimports.extend(['phate'])

# Add umap
try:
    # noinspection PyPackageRequirements
    import umap
except ImportError:
    pass
else:
    hiddenimports.extend(['umap', 'pynndescent'])

# Define path for build hooks
# noinspection PyUnresolvedReferences
hookspath.extend([os.path.join(SPECPATH, "hooks")])

# Define path for runtime hooks
# noinspection PyUnresolvedReferences
runtime_hooks.extend(sorted(glob.glob(os.path.join(SPECPATH, "rthooks", "pyi_*.py"))))

kwargs = dict(pathex=pathex,
              runtime_hooks=runtime_hooks,
              excludes=excludes,
              win_no_prefer_redirects=False,
              win_private_assemblies=False,
              cipher=block_cipher,
              noarchive=False)
# noinspection PyUnresolvedReferences
gui_a = Entrypoint('metgem', 'gui_scripts', 'MetGem',
                   **kwargs,
                   hookspath=hookspath,
                   hiddenimports=hiddenimports,
                   datas=datas,
                   binaries=binaries
                   )

# noinspection PyUnresolvedReferences
cli_a = Entrypoint('metgem', 'console_scripts', 'metgem-cli',
                   **kwargs,
                   hookspath=hookspath + [os.path.join(SPECPATH, "hooks", "pre_safe_import_module")]
                   )

gui_a = clean_datas(gui_a)
gui_a = clean_system_libraries(gui_a)
cli_a = clean_datas(cli_a)
cli_a = clean_system_libraries(cli_a)

# noinspection PyUnresolvedReferences
gui_pyz = PYZ(gui_a.pure, gui_a.zipped_data, cipher=block_cipher)
# noinspection PyUnresolvedReferences
cli_pyz = PYZ(cli_a.pure, cli_a.zipped_data, cipher=block_cipher)

if sys.platform.startswith('win'):
    # noinspection PyUnresolvedReferences
    icon = os.path.join(SPECPATH, 'main.ico')

    # Write file_version_info.txt to use it in EXE
    import re
    version_file = None
    v = re.match(r"(\d)\.(\d)\.(\d)\w*(\d?)", version)
    if v is not None:
        v = ", ".join(a if a else '0' for a in v.groups())
        # noinspection PyUnresolvedReferences
        version_file = os.path.join(workpath, 'file_version_info.txt')
        with open(version_file, 'w') as f:
            f.write("# UTF-8\n")
            f.write("#\n")
            f.write("# For more details about fixed file info 'ffi' see:\n")
            f.write("#http://msdn.microsoft.com/en-us/library/ms646997.aspx\n")
            f.write("VSVersionInfo(\n")
            f.write("    ffi=FixedFileInfo(\n")
            f.write("        # filevers and prodvers should be always a tuple with four items: (1, 2, 3, 4)\n")
            f.write("        # Set not needed items to zero 0.\n")
            f.write("        filevers=({}),\n".format(v))
            f.write("        prodvers=({}),\n".format(v))
            f.write("        # Contains a bitmask that specifies the valid bits 'flags'r\n")
            f.write("        mask=0x17,\n")
            f.write("        # Contains a bitmask that specifies the Boolean attributes of the file.\n")
            f.write("        flags=0x0,\n")
            f.write("        # The operating system for which this file was designed.\n")
            f.write("        # 0x4 - NT and there is no need to change it.\n")
            f.write("        OS=0x4,\n")
            f.write("        # The general type of file.\n")
            f.write("        # 0x1 - the file is an application.\n")
            f.write("        fileType=0x1,\n")
            f.write("        # The function of the file.\n")
            f.write("        # 0x0 - the function is not defined for this fileType\n")
            f.write("        subtype=0x0,\n")
            f.write("        # Creation date and time stamp.\n")
            f.write("        date=(0, 0)\n")
            f.write("    ),\n")
            f.write("    kids=[\n")
            f.write("        StringFileInfo(\n")
            f.write("            [\n")
            f.write("                StringTable(\n")
            f.write("                    u'000004b0',\n")
            f.write("                    [StringStruct(u'Comments', u'Version {}'),\n".format(version))
            f.write("                     StringStruct(u'CompanyName', u'CNRS/ICSN'),\n")
            f.write("                     StringStruct(u'FileDescription', u'MetGem'),\n")
            f.write("                     StringStruct(u'FileVersion', u'{}'),\n".format(version))
            f.write("                     StringStruct(u'InternalName', u'MetGem'),\n")
            f.write("                     StringStruct(u'LegalCopyright', u'Copyright (C) 2018-2023'),\n")
            f.write("                     StringStruct(u'OriginalFilename', u'MetGem.exe'),\n")
            f.write("                     StringStruct(u'ProductName', u'MetGem'),\n")
            f.write("                     StringStruct(u'ProductVersion', u'{}')])\n".format(version))
            f.write("            ]),\n")
            f.write("        VarFileInfo([VarStruct(u'Translation', [0, 1200])])\n")
            f.write("    ]\n")
            f.write(")\n")
elif sys.platform.startswith('darwin'):
    # noinspection PyUnresolvedReferences
    icon = os.path.join(SPECPATH, 'main.icns')
    version_file = None
else:
    icon = None
    version_file = None

kwargs = dict(exclude_binaries=True,
              append_pkg=False,
              debug=DEBUG,
              bootloader_ignore_signals=False,
              strip=False,
              upx=True,
              version=version_file,
              icon=icon,
              disable_windowed_traceback=False,
              argv_emulation=False,
              target_arch=None,
              codesign_identity=None,
              entitlements_file=None)
# noinspection PyUnresolvedReferences
gui_exe = EXE(gui_pyz,
          gui_a.scripts,
          [],
          **kwargs, name='MetGem', console=DEBUG)
# noinspection PyUnresolvedReferences
cli_exe = EXE(cli_pyz,
          cli_a.scripts,
          [],
          **kwargs, name='metgem-cli', console=True)

# noinspection PyUnresolvedReferences
coll = COLLECT(gui_exe,
               gui_a.binaries,
               gui_a.zipfiles,
               gui_a.datas,
               cli_exe,
               cli_a.binaries,
               cli_a.zipfiles,
               cli_a.datas,
               strip=False,
               upx=False,
               upx_exclude=[],
               name=coll_name)


if sys.platform.startswith('darwin') and not DEBUG:
    # Force LSBackgroundOnly property to false
    # If set to true, menubar is hidden and spinboxes are locked
    # This property is is set to true by PyInstaller when `console=True` parameter is passed to EXE
    # As MetGem creates two EXE, and the last one is a console app, this could explain why LSBackgroundOnly is true by default
    info_plist = {
        "LSBackgroundOnly": False,
        "NSHighResolutionCapable": True,
    }
    # noinspection PyUnresolvedReferences
    app = BUNDLE(coll,
                 name='MetGem.app',
                 icon=icon,
                 bundle_identifier='fr.cnrs.metgem',
                 version=version,
                 info_plist=info_plist)
