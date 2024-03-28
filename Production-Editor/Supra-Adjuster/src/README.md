# Create executable:

1. Download this folder of the repo
1. Install required packages: `pip3 install -r requirements.txt`
1. Install PyInstaller (check installation -- should have installed with requirements.txt)
1. Add the following docx2python hook to the PyInstaller package (seen in For MacOS: /Library/Frameworks/Python.framework/Versions/3.8/lib/python3.8/site-packages/PyInstaller/hooks)
```python3
#-----------------------------------------------------------------------------
# Copyright (c) 2013-2023, PyInstaller Development Team.
#
# Distributed under the terms of the GNU General Public License (version 2
# or later) with exception for distributing the bootloader.
#
# The full license is in the file COPYING.txt, distributed with this software.
#
# SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
#-----------------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# The layers to load can be configured using scapy's conf.load_layers.
#  from scapy.config import conf; print(conf.load_layers)
# I decided not to use this, but to include all layer modules. The reason is: When building the package, load_layers may
# not include all the layer modules the program will use later.

datas = collect_data_files('docx2python')
hiddenimports = collect_submodules('docx2python')
```
1. run the `setup.py` to create the spec file used for PyInstaller
	- run with `python3 setup.py`
1. run `python3 -m PyInstaller supra_adjuster.spec` inside the downloaded repo folder
1. The files created in the `dist` folder will contain the executable file

Credits: 
- icon design: <a href="https://www.flaticon.com/free-icons/sa" title="SA icons">SA icons created by NajmunNahar - Flaticon</a>