# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ImPact_toolbox_dialog_base.ui'
#
# Created by: PyQt5 UI code generator 5.15.11
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_APIRequestDialogBase(object):
    def setupUi(self, APIRequestDialogBase):
        APIRequestDialogBase.setObjectName("APIRequestDialogBase")
        APIRequestDialogBase.setWindowModality(QtCore.Qt.ApplicationModal)
        APIRequestDialogBase.setEnabled(True)
        APIRequestDialogBase.resize(770, 719)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(APIRequestDialogBase.sizePolicy().hasHeightForWidth())
        APIRequestDialogBase.setSizePolicy(sizePolicy)
        APIRequestDialogBase.setMinimumSize(QtCore.QSize(0, 0))
        APIRequestDialogBase.setContextMenuPolicy(QtCore.Qt.DefaultContextMenu)
        APIRequestDialogBase.setStyleSheet("")
        APIRequestDialogBase.setSizeGripEnabled(False)
        APIRequestDialogBase.setModal(True)
        self.main_tab = QtWidgets.QTabWidget(APIRequestDialogBase)
        self.main_tab.setGeometry(QtCore.QRect(10, 0, 751, 721))
        self.main_tab.setObjectName("main_tab")
        self.settings_tab = QtWidgets.QWidget()
        self.settings_tab.setObjectName("settings_tab")
        self.formLayoutWidget = QtWidgets.QWidget(self.settings_tab)
        self.formLayoutWidget.setGeometry(QtCore.QRect(10, 10, 731, 661))
        self.formLayoutWidget.setObjectName("formLayoutWidget")
        self.settings_form = QtWidgets.QFormLayout(self.formLayoutWidget)
        self.settings_form.setContentsMargins(0, 0, 0, 0)
        self.settings_form.setObjectName("settings_form")
        self.label = QtWidgets.QLabel(self.formLayoutWidget)
        self.label.setObjectName("label")
        self.settings_form.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label)
        self.api_key_field = QtWidgets.QLineEdit(self.formLayoutWidget)
        self.api_key_field.setObjectName("api_key_field")
        self.settings_form.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.api_key_field)
        self.label_2 = QtWidgets.QLabel(self.formLayoutWidget)
        self.label_2.setObjectName("label_2")
        self.settings_form.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.label_2)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.settings_form.setItem(3, QtWidgets.QFormLayout.FieldRole, spacerItem)
        self.label_5 = QtWidgets.QLabel(self.formLayoutWidget)
        self.label_5.setWordWrap(True)
        self.label_5.setObjectName("label_5")
        self.settings_form.setWidget(11, QtWidgets.QFormLayout.FieldRole, self.label_5)
        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.settings_form.setItem(12, QtWidgets.QFormLayout.FieldRole, spacerItem1)
        self.label_4 = QtWidgets.QLabel(self.formLayoutWidget)
        self.label_4.setObjectName("label_4")
        self.settings_form.setWidget(13, QtWidgets.QFormLayout.LabelRole, self.label_4)
        self.project_directory = QgsFileWidget(self.formLayoutWidget)
        self.project_directory.setObjectName("project_directory")
        self.settings_form.setWidget(13, QtWidgets.QFormLayout.FieldRole, self.project_directory)
        self.label_6 = QtWidgets.QLabel(self.formLayoutWidget)
        self.label_6.setScaledContents(False)
        self.label_6.setWordWrap(True)
        self.label_6.setObjectName("label_6")
        self.settings_form.setWidget(14, QtWidgets.QFormLayout.FieldRole, self.label_6)
        spacerItem2 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.settings_form.setItem(15, QtWidgets.QFormLayout.FieldRole, spacerItem2)
        self.impact_instance_selector = QtWidgets.QComboBox(self.formLayoutWidget)
        self.impact_instance_selector.setObjectName("impact_instance_selector")
        self.settings_form.setWidget(7, QtWidgets.QFormLayout.FieldRole, self.impact_instance_selector)
        self.label_3 = QtWidgets.QLabel(self.formLayoutWidget)
        self.label_3.setObjectName("label_3")
        self.settings_form.setWidget(7, QtWidgets.QFormLayout.LabelRole, self.label_3)
        self.save_settings_button = QtWidgets.QPushButton(self.formLayoutWidget)
        self.save_settings_button.setObjectName("save_settings_button")
        self.settings_form.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.save_settings_button)
        self.save_area_outline = QtWidgets.QPushButton(self.formLayoutWidget)
        self.save_area_outline.setObjectName("save_area_outline")
        self.settings_form.setWidget(10, QtWidgets.QFormLayout.FieldRole, self.save_area_outline)
        self.impact_url_textfield = QtWidgets.QLineEdit(self.formLayoutWidget)
        self.impact_url_textfield.setObjectName("impact_url_textfield")
        self.settings_form.setWidget(8, QtWidgets.QFormLayout.FieldRole, self.impact_url_textfield)
        self.save_impact_url_button = QtWidgets.QPushButton(self.formLayoutWidget)
        self.save_impact_url_button.setObjectName("save_impact_url_button")
        self.settings_form.setWidget(9, QtWidgets.QFormLayout.FieldRole, self.save_impact_url_button)
        self.label.raise_()
        self.api_key_field.raise_()
        self.label_2.raise_()
        self.label_5.raise_()
        self.label_4.raise_()
        self.project_directory.raise_()
        self.label_6.raise_()
        self.impact_instance_selector.raise_()
        self.label_3.raise_()
        self.save_settings_button.raise_()
        self.save_area_outline.raise_()
        self.save_impact_url_button.raise_()
        self.impact_url_textfield.raise_()
        self.main_tab.addTab(self.settings_tab, "")
        self.routeplanning_tab = QtWidgets.QWidget()
        self.routeplanning_tab.setObjectName("routeplanning_tab")
        self.formLayoutWidget_2 = QtWidgets.QWidget(self.routeplanning_tab)
        self.formLayoutWidget_2.setGeometry(QtCore.QRect(0, 20, 741, 661))
        self.formLayoutWidget_2.setObjectName("formLayoutWidget_2")
        self.routeplanning_form = QtWidgets.QFormLayout(self.formLayoutWidget_2)
        self.routeplanning_form.setContentsMargins(0, 0, 0, 0)
        self.routeplanning_form.setObjectName("routeplanning_form")
        self.label_15 = QtWidgets.QLabel(self.formLayoutWidget_2)
        self.label_15.setObjectName("label_15")
        self.routeplanning_form.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.label_15)
        self.label_29 = QtWidgets.QLabel(self.formLayoutWidget_2)
        self.label_29.setObjectName("label_29")
        self.routeplanning_form.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.label_29)
        self.label_7 = QtWidgets.QLabel(self.formLayoutWidget_2)
        self.label_7.setObjectName("label_7")
        self.routeplanning_form.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.label_7)
        self.scenario_picker = QtWidgets.QComboBox(self.formLayoutWidget_2)
        self.scenario_picker.setEditable(False)
        self.scenario_picker.setCurrentText("")
        self.scenario_picker.setObjectName("scenario_picker")
        self.routeplanning_form.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.scenario_picker)
        self.label_16 = QtWidgets.QLabel(self.formLayoutWidget_2)
        self.label_16.setText("")
        self.label_16.setObjectName("label_16")
        self.routeplanning_form.setWidget(4, QtWidgets.QFormLayout.FieldRole, self.label_16)
        self.toolbox_origin_destination_or_movement = QtWidgets.QTabWidget(self.formLayoutWidget_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.toolbox_origin_destination_or_movement.sizePolicy().hasHeightForWidth())
        self.toolbox_origin_destination_or_movement.setSizePolicy(sizePolicy)
        self.toolbox_origin_destination_or_movement.setMinimumSize(QtCore.QSize(0, 210))
        self.toolbox_origin_destination_or_movement.setObjectName("toolbox_origin_destination_or_movement")
        self.tab1 = QtWidgets.QWidget()
        self.tab1.setObjectName("tab1")
        self.formLayoutWidget_4 = QtWidgets.QWidget(self.tab1)
        self.formLayoutWidget_4.setGeometry(QtCore.QRect(0, 10, 671, 260))
        self.formLayoutWidget_4.setObjectName("formLayoutWidget_4")
        self.formLayout_3 = QtWidgets.QFormLayout(self.formLayoutWidget_4)
        self.formLayout_3.setContentsMargins(0, 0, 0, 0)
        self.formLayout_3.setObjectName("formLayout_3")
        self.label_11 = QtWidgets.QLabel(self.formLayoutWidget_4)
        self.label_11.setObjectName("label_11")
        self.formLayout_3.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label_11)
        self.departure_layer_picker = QgsMapLayerComboBox(self.formLayoutWidget_4)
        self.departure_layer_picker.setObjectName("departure_layer_picker")
        self.formLayout_3.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.departure_layer_picker)
        self.label_12 = QtWidgets.QLabel(self.formLayoutWidget_4)
        self.label_12.setObjectName("label_12")
        self.formLayout_3.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.label_12)
        self.arrival_layer_picker = QgsMapLayerComboBox(self.formLayoutWidget_4)
        self.arrival_layer_picker.setObjectName("arrival_layer_picker")
        self.formLayout_3.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.arrival_layer_picker)
        self.label_13 = QtWidgets.QLabel(self.formLayoutWidget_4)
        self.label_13.setObjectName("label_13")
        self.formLayout_3.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.label_13)
        self.label_14 = QtWidgets.QLabel(self.formLayoutWidget_4)
        self.label_14.setObjectName("label_14")
        self.formLayout_3.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.label_14)
        self.toolbox_origin_destination_or_movement.addTab(self.tab1, "")
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.formLayoutWidget_3 = QtWidgets.QWidget(self.tab_2)
        self.formLayoutWidget_3.setGeometry(QtCore.QRect(0, 0, 1081, 297))
        self.formLayoutWidget_3.setObjectName("formLayoutWidget_3")
        self.formLayout_2 = QtWidgets.QFormLayout(self.formLayoutWidget_3)
        self.formLayout_2.setContentsMargins(0, 0, 0, 0)
        self.formLayout_2.setObjectName("formLayout_2")
        self.movement_pairs_layer_picker = QgsMapLayerComboBox(self.formLayoutWidget_3)
        self.movement_pairs_layer_picker.setObjectName("movement_pairs_layer_picker")
        self.formLayout_2.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.movement_pairs_layer_picker)
        self.label_17 = QtWidgets.QLabel(self.formLayoutWidget_3)
        self.label_17.setObjectName("label_17")
        self.formLayout_2.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.label_17)
        self.label_18 = QtWidgets.QLabel(self.formLayoutWidget_3)
        self.label_18.setWordWrap(True)
        self.label_18.setObjectName("label_18")
        self.formLayout_2.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.label_18)
        self.selected_layer_report = QtWidgets.QLabel(self.formLayoutWidget_3)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.selected_layer_report.sizePolicy().hasHeightForWidth())
        self.selected_layer_report.setSizePolicy(sizePolicy)
        self.selected_layer_report.setWordWrap(True)
        self.selected_layer_report.setObjectName("selected_layer_report")
        self.formLayout_2.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.selected_layer_report)
        self.toolbox_origin_destination_or_movement.addTab(self.tab_2, "")
        self.routeplanning_form.setWidget(6, QtWidgets.QFormLayout.FieldRole, self.toolbox_origin_destination_or_movement)
        self.label_9 = QtWidgets.QLabel(self.formLayoutWidget_2)
        self.label_9.setObjectName("label_9")
        self.routeplanning_form.setWidget(8, QtWidgets.QFormLayout.LabelRole, self.label_9)
        self.profile_picker = QtWidgets.QComboBox(self.formLayoutWidget_2)
        self.profile_picker.setObjectName("profile_picker")
        self.routeplanning_form.setWidget(8, QtWidgets.QFormLayout.FieldRole, self.profile_picker)
        self.label_10 = QtWidgets.QLabel(self.formLayoutWidget_2)
        self.label_10.setObjectName("label_10")
        self.routeplanning_form.setWidget(9, QtWidgets.QFormLayout.FieldRole, self.label_10)
        self.profile_explanation = QtWidgets.QLabel(self.formLayoutWidget_2)
        font = QtGui.QFont()
        font.setBold(True)
        font.setItalic(True)
        self.profile_explanation.setFont(font)
        self.profile_explanation.setObjectName("profile_explanation")
        self.routeplanning_form.setWidget(10, QtWidgets.QFormLayout.FieldRole, self.profile_explanation)
        self.perform_routeplanning_button = QtWidgets.QPushButton(self.formLayoutWidget_2)
        self.perform_routeplanning_button.setObjectName("perform_routeplanning_button")
        self.routeplanning_form.setWidget(11, QtWidgets.QFormLayout.FieldRole, self.perform_routeplanning_button)
        self.main_tab.addTab(self.routeplanning_tab, "")

        self.retranslateUi(APIRequestDialogBase)
        self.main_tab.setCurrentIndex(1)
        self.toolbox_origin_destination_or_movement.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(APIRequestDialogBase)

    def retranslateUi(self, APIRequestDialogBase):
        _translate = QtCore.QCoreApplication.translate
        APIRequestDialogBase.setWindowTitle(_translate("APIRequestDialogBase", "ImPact ToolBox"))
        self.label.setText(_translate("APIRequestDialogBase", "Api-Key"))
        self.label_2.setText(_translate("APIRequestDialogBase", "A personal string which acts as key, provided to you by ANYWAYS BV."))
        self.label_5.setText(_translate("APIRequestDialogBase", "<html><head/><body><p>The URL of one of your impact instances. Copy and paste the URL of any instance here, the tool will figure out which instances exist. You can pick any later on.</p><p/></body></html>"))
        self.label_4.setText(_translate("APIRequestDialogBase", "Project directory"))
        self.label_6.setText(_translate("APIRequestDialogBase", "<html><head/><body><p>This is the path of the current project. All intermediate files (output from routeplanning, ...) will be saved here as geoJson.</p></body></html>"))
        self.label_3.setText(_translate("APIRequestDialogBase", "ImPact URL"))
        self.save_settings_button.setText(_translate("APIRequestDialogBase", "Save settings"))
        self.save_area_outline.setText(_translate("APIRequestDialogBase", "Save the outline of this Impact instance as a layer"))
        self.save_impact_url_button.setText(_translate("APIRequestDialogBase", "Save impact instance"))
        self.main_tab.setTabText(self.main_tab.indexOf(self.settings_tab), _translate("APIRequestDialogBase", "Settings"))
        self.label_15.setText(_translate("APIRequestDialogBase", "<html><head/><body><p>Calculate routes between multiple departure points and multiple arrival points</p><p/></body></html>"))
        self.label_29.setText(_translate("APIRequestDialogBase", "All individual road segments will be grouped and counted"))
        self.label_7.setText(_translate("APIRequestDialogBase", "Scenario"))
        self.label_11.setText(_translate("APIRequestDialogBase", "Departure"))
        self.label_12.setText(_translate("APIRequestDialogBase", "<html><head/><body><p>Every point in this layer will be considered a departure point.</p><p/></body></html>"))
        self.label_13.setText(_translate("APIRequestDialogBase", "Arrival"))
        self.label_14.setText(_translate("APIRequestDialogBase", "<html><head/><body><p>Every point in this layer will be used as arrival point.</p><p>To do matrix routing, select the same as departure</p><p/></body></html>"))
        self.toolbox_origin_destination_or_movement.setTabText(self.toolbox_origin_destination_or_movement.indexOf(self.tab1), _translate("APIRequestDialogBase", "Plan routes between point layers"))
        self.label_17.setText(_translate("APIRequestDialogBase", "Select a movement layer"))
        self.label_18.setText(_translate("APIRequestDialogBase", "Use a layer with movement data (e.g. loaded from file or from the FOD). Routeplanning will be performed on every origin-destination pair, which will be weighted                                        "))
        self.selected_layer_report.setText(_translate("APIRequestDialogBase", "No layer selected. Select a layer to show information about it.\n"
"\n"
"\n"
"\n"
"\n"
"\n"
"\n"
"\n"
"\n"
"\n"
""))
        self.toolbox_origin_destination_or_movement.setTabText(self.toolbox_origin_destination_or_movement.indexOf(self.tab_2), _translate("APIRequestDialogBase", "Plan routes over a linestring layer"))
        self.label_9.setText(_translate("APIRequestDialogBase", "Profile"))
        self.label_10.setText(_translate("APIRequestDialogBase", "<html><head/><body><p>Select which vehicle to plan and it behaves. Read below how the profile behaves</p><p/></body></html>"))
        self.profile_explanation.setText(_translate("APIRequestDialogBase", "(Select a profile first. The profile info will be shown here)"))
        self.perform_routeplanning_button.setText(_translate("APIRequestDialogBase", "Perform routeplanning"))
        self.main_tab.setTabText(self.main_tab.indexOf(self.routeplanning_tab), _translate("APIRequestDialogBase", "Routeplanning"))
from qgsfilewidget import QgsFileWidget
from qgsmaplayercombobox import QgsMapLayerComboBox
