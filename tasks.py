import json
import os
import shutil
import sys
import tempfile
import subprocess
import requests
import io
import zipfile

from invoke import task
from invoke import Collection

import metgem.tasks

PACKAGING_DIR = os.path.dirname(__file__)
DIST = os.path.join(PACKAGING_DIR, 'dist')
BUILD = os.path.join(PACKAGING_DIR, 'build')
NAME = 'MetGem'
APPIMAGE_TOOL_URL = "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
API_MS_WIN_CORE_PATH_URL = "https://github.com/nalexandru/api-ms-win-core-path-HACK/releases/download/0.3.1/api-ms-win-core-path-blender-0.3.1.zip"
API_MS_WIN_CORE_PATH_FILENAME = "api-ms-win-core-path-l1-1-0.dll"
API_MS_WIN_CORE_PATH = f"api-ms-win-core-path-blender/x64/{API_MS_WIN_CORE_PATH_FILENAME}"


def get_git_revision_short_hash():
    short_hash = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'])
    short_hash = str(short_hash, "utf-8").strip()
    return short_hash


@task
def clean(ctx, dist=False, bytecode=False, extra=''):
    patterns = ['build']
    if dist:
        patterns.append('dist')
    if bytecode:
        patterns.append('*.pyc')
    if extra:
        patterns.append(extra)
    for pattern in patterns:
        if sys.platform.startswith('win'):
            ctx.run("del /s /q {}".format(pattern))
        else:
            ctx.run("rm -rf {}".format(pattern))


# noinspection PyShadowingNames
@task
def build(ctx, clean=False, validate_appstream=True):
    exe(ctx, clean)
    installer(ctx, validate_appstream)


# noinspection PyShadowingNames
@task
def buildpy(ctx):
    ctx.run("cd {0}/metgem && python setup.py build -b {0}/build".format(PACKAGING_DIR))

# noinspection PyShadowingNames,PyUnusedLocal
@task
def exe(ctx, clean=False, debug=False, build_py=True):
    if build_py:
        buildpy(ctx)

    switchs = ["--clean"] if clean else []
    if debug:
        switchs.append("--debug all")
    result = ctx.run("pyinstaller {0} --noconfirm {1} --distpath {2} --workpath {3}"
                     .format(os.path.join(PACKAGING_DIR, 'MetGem.spec'), " ".join(switchs), DIST, BUILD))

    if result:
        if sys.platform.startswith('win'):
            embed_manifest(ctx, debug)
            if not debug:
                com(ctx)

            # Download api-ms-win-core-path dll file modified for Windows 7
            if not os.path.exists(os.path.join(PACKAGING_DIR, "build", API_MS_WIN_CORE_PATH_FILENAME)):
                r = requests.get(API_MS_WIN_CORE_PATH_URL, allow_redirects=True)
                with zipfile.ZipFile(io.BytesIO(r.content), 'r') as zip:
                    zip_info = zip.getinfo(API_MS_WIN_CORE_PATH)
                    zip_info.filename = os.path.basename(zip_info.filename)
                    zip.extract(zip_info, os.path.join(PACKAGING_DIR, "build"))
                shutil.copy2(os.path.join(PACKAGING_DIR, "build", API_MS_WIN_CORE_PATH_FILENAME), os.path.join(DIST, NAME, API_MS_WIN_CORE_PATH_FILENAME))

            # Write build version in dist folder
            build_version = get_git_revision_short_hash()
            with open(os.path.join(DIST, NAME, "_build_version.txt"), "w") as f:
                print(build_version, file=f)
        elif sys.platform.startswith('darwin'):
            add_rpath(ctx)


# noinspection PyShadowingNames,PyUnusedLocal
@task
def add_rpath(ctx):
    webengine_process = "{0}/{1}.app/Contents/MacOS/QtWebEngineProcess".format(DIST, NAME)
    ctx.run('install_name_tool -add_rpath @executable_path/. {}'.format(webengine_process))


# noinspection PyShadowingNames,PyUnusedLocal
@task
def embed_manifest(ctx, debug):
    # noinspection PyUnresolvedReferences
    from PyInstaller.utils.win32 import winmanifest
    folder = NAME + "_debug" if debug else NAME
    exe = "{0}\{1}\{2}.exe".format(DIST, folder, NAME)

    # Embed manifest in exe
    manifest = exe + '.manifest'
    if os.path.exists(manifest):
        winmanifest.UpdateManifestResourcesFromXMLFile(exe, manifest)
        os.remove(manifest)


# noinspection PyShadowingNames,PyUnusedLocal
@task
def com(ctx):
    # Copy generated exe to .com and change it to a console application
    # See https://www.nirsoft.net/vb/appmodechange.html
    import struct
    import winnt

    exe = "{0}\{1}\{2}.exe".format(DIST, NAME, NAME)
    com = exe.replace('.exe', '.com')
    exe = "{0}\{1}\{2}.exe".format(DIST, NAME, NAME)
    shutil.copy2(exe, com)

    with open(com, 'r+b') as f:
        assert f.read(2) == b'MZ'
        f.seek(0x3C)
        pe_location = struct.unpack('L', f.read(4))[0]
        f.seek(pe_location)
        assert f.read(2) == b'PE'
        f.seek(pe_location + 0x5C)
        subsystem = struct.unpack('B', f.read(1))[0]
        assert subsystem == winnt.IMAGE_SUBSYSTEM_WINDOWS_GUI
        f.seek(pe_location + 0x5C)
        f.write(struct.pack('B', winnt.IMAGE_SUBSYSTEM_WINDOWS_CUI))


@task
def installer(ctx, validate_appstream=True):
    if sys.platform.startswith('win'):
        iscc = shutil.which("ISCC")
        iss = os.path.join(PACKAGING_DIR, 'setup.iss')
        ctx.run(f"{iscc} {iss}")
    elif sys.platform.startswith('darwin'):
        output = os.path.join(PACKAGING_DIR, NAME + '.dmg')
        if os.path.exists(output):
            os.unlink(output)

        with tempfile.TemporaryDirectory() as tmp_dir:
            application = os.path.join(PACKAGING_DIR, 'dist', NAME + '.app')
            icon = os.path.join(PACKAGING_DIR, 'main.icns')
            source_folder = os.path.join(tmp_dir, NAME)
            tmp_application = os.path.join(source_folder, NAME + '.app')

            os.makedirs(source_folder)
            subprocess.run([os.path.join(PACKAGING_DIR, 'set_folder_icon.sh'), icon, tmp_dir, NAME],
                           shell=True)

            shutil.copytree(application, tmp_application)
            shutil.copytree(os.path.join(PACKAGING_DIR, 'metgem', 'examples'),
                            os.path.join(source_folder, 'examples'))

            appdmg_json = {'title': NAME,
                           'icon': icon,
                           'icon-size': 150,
                           'background': os.path.join(PACKAGING_DIR, 'installer_background.png'),
                           'window': {'size': {'width': 800, 'height': 400}},
                           'contents': [{'x': 525, 'y': 125, 'type': 'link', 'path': '/Applications'},
                                        {'x': 125, 'y': 125, 'type': 'file', 'path': source_folder}]}
            appdmg_json_fn = os.path.join(PACKAGING_DIR, 'appdmg.json')
            with open(appdmg_json_fn, 'w') as f:
                json.dump(appdmg_json, f)

            subprocess.run(['appdmg', appdmg_json_fn, output])
    elif sys.platform.startswith('linux'):
        if not os.path.exists('{}/appimagetool-x86_64.AppImage'.format(PACKAGING_DIR)):
            ctx.run('wget {} -P {}'.format(APPIMAGE_TOOL_URL, PACKAGING_DIR))
            ctx.run('chmod u+x {}/appimagetool-x86_64.AppImage'.format(PACKAGING_DIR))
        ctx.run('cp -r {0}/{1}/* {2}/AppDir/usr/lib/'.format(DIST, NAME, PACKAGING_DIR))
        switch = '-n' if not validate_appstream else ''
        ctx.run('cd {0} && ARCH=x86_64 ./appimagetool-x86_64.AppImage AppDir {1}'.format(PACKAGING_DIR, switch))
        ctx.run('rm -r {}/AppDir/usr/lib/*'.format(PACKAGING_DIR))
        
        

ns = Collection()
ns.add_task(metgem.tasks.rc)
ns.add_task(metgem.tasks.uic)
ns.add_task(clean)
ns.add_task(build)
ns.add_task(buildpy)
ns.add_task(exe)
ns.add_task(add_rpath)
ns.add_task(embed_manifest)
ns.add_task(com)
ns.add_task(installer)
