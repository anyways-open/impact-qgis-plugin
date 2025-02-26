from qgis.core import (QgsMessageLog, Qgis)


class previous_state_tracker(object):

    def __init__(self, project_settings):
        self.project_settings = project_settings
        self.is_updating = False

    def pause_loading(self):
        self.is_updating = True

    def resume_loading(self):
        self.is_updating = False

    def log(self, msg):
        QgsMessageLog.logMessage(msg, MESSAGE_CATEGORY, level=Qgis.Info)

    def init_and_connect_textfield(self, id, qlineEdit):
        key = ("textfield_" + id).replace("/", "_").replace(" ", "_")

        def save():
            current_value = qlineEdit.text()
            self.project_settings.writeEntry("anyways", key, current_value)

        previous_value = self.project_settings.readEntry("anyways", key)[0]
        if previous_value is not None:
            qlineEdit.setText(previous_value)
        qlineEdit.editingFinished.connect(save)

    def init_and_connect(self, id, qcombobox, extra_state_from=None):
        """
        Saves the qcombox-state to the project file
        IF 'extra_state_from' is given, that value will be used as additional key to keep track of the settings
        :param id: 
        :param qcombobox: 
        :param extra_state_from: 
        :return: 
        """

        def searchIndex(value):
            for i in range(0, qcombobox.count()):
                text_at_i = qcombobox.itemText(i)
                if text_at_i == value:
                    return i

        def update():

            if self.is_updating:
                # We are changing values of comboboxes at the moment, saving is a bit stupid now
                return

            current_value = qcombobox.currentText()
            if (current_value is None or current_value == ""):
                return

            extra_key = ""
            if extra_state_from is not None:
                extra_key = extra_state_from.currentText()
            key = ("radiobutton_" + extra_key + "_" + id).replace("/", "_").replace(" ", "_")
            self.project_settings.writeEntry("anyways", key, current_value)

        def load_previous():
            extra_key = ""
            if extra_state_from is not None:
                extra_key = extra_state_from.currentText()
            key = ("radiobutton_" + extra_key + "_" + id).replace("/", "_").replace(" ", "_")
            previous_value = self.project_settings.readEntry("anyways", key)[0]
            i = searchIndex(previous_value)
            if i is not None:
                qcombobox.setCurrentIndex(i)

        load_previous()
        qcombobox.editTextChanged.connect(load_previous)

        qcombobox.currentTextChanged.connect(lambda: update())

        if extra_state_from is not None:
            extra_state_from.currentTextChanged.connect(load_previous)
