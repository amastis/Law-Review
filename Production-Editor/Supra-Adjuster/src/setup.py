import os
from typing import List, Set
import pkg_resources
from importlib.metadata import requires

def spec_info(excluded_packages: List[str]) -> str:
    return f'''# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['GUI.py'],
    pathex=[],
    binaries=[],
    datas=[('upload_icon.png', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes={excluded_packages},
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Supra Adjuster.app',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='GUI',
)
app = BUNDLE(
    coll,
    name='Supra Adjuster.app',
    icon='Supra_Adjuster_icon.png',
    bundle_identifier=None,
)
'''

# https://stackoverflow.com/questions/4138851/recursive-looping-function-in-python
def collect_requirements(start: str):
    """ negative depths means unlimited recursion """
    requirement_names: List[str] = []

    def package_name(original_name: str) -> str:
        return pkg_resources.working_set.by_key[original_name]

    # recursive function that collects all the names from upper package name
    def recurse(current: str) -> None:
        requirement_names.append(current)

        _package = package_name(current)
        if required_packages := _package.requires():
            for package in required_packages:
                recurse(package.name) # recursive call for each subrequirement

    recurse(start) # starts recursion
    return requirement_names

def main() -> None:
    REQUIRED_PACKAGES: Set[str] = {}

    if os.path.isfile('requirements.txt'):
        with open('requirements.txt', 'r') as file:
            REQUIRED_PACKAGES = {item.split('==')[0].lower() for item in file.readlines()}
    else:
        REQUIRED_PACKAGES = {'tkinter', 'time', 'selenium', 'typing', 're', 'os', 'pathlib', 'docx2python', 'pandas', 'PIL', 'pillow', 'threading', 'random', 'queue', 'pyinstaller', 'openpyxl'} # TODO look at req packages

    # get required package dependencies
    # https://stackoverflow.com/questions/29751572/how-to-find-a-python-packages-dependencies
    all_required_packages: List[str] = []
    for item in REQUIRED_PACKAGES:
        all_required_packages.extend(collect_requirements(item))

    all_required_packages_set = set(all_required_packages)

    # https://www.activestate.com/resources/quick-reads/how-to-list-installed-python-packages/
    all_installed_packages = pkg_resources.working_set
    all_installed_packages_set = set(sorted([i.key for i in all_installed_packages]))

    exclude_packages_list = list(all_installed_packages_set.difference(all_required_packages_set))

    with open('supra_adjuster.spec', 'w') as file:
        file.write(spec_info(exclude_packages_list))


if __name__ == '__main__':
    main()
