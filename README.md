
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

- Use 'First Aid' plugin for better debugging

`sudo pip3 install pb_tool` 

Convert ui to python

` pyrcc5 -o resources.py resources.qrc` to create 'resources.py' (needed if e.g. the icon changes)
`cd i18n && lrelease *.ts` to regenerate the compiled translations (needed if translations are added)
`pylupdate5 -verbose ImPact_toolbox_dialog.py ImPact_toolbox.py -ts i18n/ImPact_toolbox_dynamic_nl.ts i18n/ImPact_toolbox_dynamic_en.ts`

In combination with the plugin reloader: configure the plugin reloader with the following script

```
cd <write home location here>/anyways-open/impact-qgis-plugin
pb_tool compile
pb_tool zip
pb_tool deploy --no-confirm
```

## Translations

[Preliminary reading](https://doc.qt.io/qt-5/linguist-overview.html)

Dynamic strings are strings wrapped in `self.tr("text to translate")` in `ImPact_toolbox_dialog.py`
To extract them into the translation files, run:

```
pylupdate5 -verbose ImPact_toolbox_dialog.py ImPact_toolbox.py -ts i18n/ImPact_toolbox_dynamic_nl.ts i18n/ImPact_toolbox_dynamic_en.ts
```

lupdate *.ui *.py -ts i18n/test_en.ts i18n/ImPact_toolbox_dialog_nl


At last, run `cd i18n && lrelease *.ts` to convert the `.ts` files into `.qm`-files. The `.qm`-files are actually used by the application.