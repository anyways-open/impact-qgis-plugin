
Impact QGIS-plugin
==================


![staging](https://github.com/anyways-open/impact-qgis-plugin/workflows/staging/badge.svg)  

This repo contains the code for the **Impact toolbox** plugin for QGIS.

This plugin has been developed to automate accessing the [ANYWAYS](https://www.anyways.eu) Routing API and ease the subsequent routing analysis by importing all calculated routings (combined or separately) in QGIS. However, this is just the beginning of developing a fantastic toolbox that not only automates but also links our APIs to facilitate mobility-related analysis in multiple levels. Some examples of these analyses are as follows:
- Network analysis
- Accessibility analysis & assessment
- **Impact analysis** (e.g., traffic shift due to the closure of a level crossing)
- etc.



Development hints
-----------------

To load the code locally:

- Create a zip file of the 'src'-directory
- Open QGIS, Plugins -> Manage and install plugins -> Install from ZIP

For development purposes:

### In QGIS:

- The 'plugin reloader' didn't work for me
- Use 'First Aid' plugin for better debugging

Convert ui to python

`pyuic5 --import-from=. -o ImPact_toolbox_dialog_base.py ImPact_toolbox_dialog_base.ui`

OR

`cd src && pyuic5 ImPact_toolbox_dialog_base.ui -o ImPact_toolbox_dialog_base.py && cd -`

Build plugin:
Install pb_tool:

`sudo pip3 install pb_tool` or alternatively, just zip 'src' together
  
