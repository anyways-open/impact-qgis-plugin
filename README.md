ANYWAYS QGIS-plugin
==================

This repo contains the code for the **ANYWAYS Plugin** for QGIS.

This plugin has been developed to automate accessing the [ANYWAYS](https://www.anyways.eu) Routing API and ease the subsequent routing analysis by importing all calculated routings (combined or separately) in QGIS. However, this is just the beginning of developing a fantastic toolbox that not only automates but also links our APIs to facilitate mobility-related analysis in multiple levels. Some examples of these analyses are as follows:
- Network analysis
- Accessibility analysis & assessment
- etc.

Installation and user documentation
-----------------------------------

The documentation for users can be found [here](https://docs.anyways.eu/qgis-plugin/)

The source of the user documentation is kept [in the anyways/docs repo](https://github.com/anyways-open/docs/tree/develop/src/qgis-plugin)

This plugin should be installed via the QGIS plugin manager. The plugin is in [the QGIS Python Plugins repository](https://plugins.qgis.org/plugins/anyways_impact_toolbox/)
The latest unstable version can be found [here](https://github.com/anyways-open/impact-qgis-plugin/releases)

The rest of this document contains technical instructions for developers.

Development hints
-----------------

To load the code locally:

- Create a zip file of the 'src'-directory
- Open QGIS, Plugins -> Manage and install plugins -> Install from ZIP

For development purposes:

### In QGIS:

- Use 'First Aid' plugin for better debugging. Note that some exception blocks will rethrow the error if the message is `FIRST AID!` in order to open the debugger.

`sudo pip3 install pb_tool` 

Note: `print`-statements will end up in the 'python console' (plugins > Python Console), log messages in the logbook (view > panels > Log Messages)

### Compilation

Convert ui to python with `pyuic5 --import-from=. -o ImPact_toolbox_dialog_base.py ImPact_toolbox_dialog_base.ui`. Do this if the UI file is changed

` pyrcc5 -o resources.py resources.qrc` to create 'resources.py' (needed if e.g. the icon changes)
`cd i18n && lrelease *.ts` to regenerate the compiled translations (needed if translations are added)
`pylupdate5 -verbose ImPact_toolbox_dialog.py ImPact_toolbox.py -ts i18n/ImPact_toolbox_dynamic_nl.ts i18n/ImPact_toolbox_dynamic_en.ts`

In combination with the plugin reloader: configure the plugin reloader with the following script

```
cd <write home location here>/anyways-open/impact-qgis-plugin
pb_tool compile && pb_tool zip && pb_tool deploy --no-confirm
```

## Translations

All string on the UI can be translated:

- The strings in .ui-files are translatable automatically
- In the source code, translatable strings are strings wrapped in `self.tr("text to translate")` in `ImPact_toolbox_dialog.py`.

The process in a nutshell:

1. Extract them into intermediate .ts-files
2. Add translations with QtLinguist 
3. Convert the .ts-files into .qm files
4. Recompile the plugin

[Extra reading](https://doc.qt.io/qt-5/linguist-overview.html)


### 1. Extract ts files

To extract the translatable string into the translation files, run:

```pylupdate5 -verbose *.ui *.py -ts i18n/ImPact_toolbox_en.ts i18n/ImPact_toolbox_nl.ts```

This will not overwrite earlier translation work, it'll only append new strings to translate.


### 2. Translate files

QT Linguist is available on the package repos.
The [windows installer can be found here](https://download.qt.io/linguist_releases/qtlinguistinstaller-5.12.2.exe.mirrorlist)

### 3.

To compile the message files, run `cd i18n && lrelease *.ts`

