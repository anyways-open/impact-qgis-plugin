from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QTextEdit, QDialogButtonBox,
    QComboBox
)


class UploadDatasetDialog(QDialog):
    def __init__(self, layer_name: str, project_name: str, profile_keys: list,
                 show_profile_picker: bool, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Upload to ANYWAYS")
        self.setMinimumWidth(400)

        layout = QVBoxLayout()

        layout.addWidget(QLabel(f"Uploading to project: <b>{project_name}</b>"))

        layout.addWidget(QLabel("Dataset name:"))
        self.name_edit = QLineEdit()
        self.name_edit.setText(layer_name)
        layout.addWidget(self.name_edit)

        layout.addWidget(QLabel("Description:"))
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(100)
        layout.addWidget(self.description_edit)

        self.profile_picker = None
        if show_profile_picker:
            layout.addWidget(QLabel("Profile:"))
            self.profile_picker = QComboBox()
            self.profile_picker.addItems(profile_keys)
            layout.addWidget(self.profile_picker)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self._validate_and_accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.setLayout(layout)

    def _validate_and_accept(self):
        if not self.name_edit.text().strip():
            self.name_edit.setFocus()
            return
        self.accept()

    def get_name(self) -> str:
        return self.name_edit.text().strip()

    def get_description(self) -> str:
        return self.description_edit.toPlainText().strip()

    def get_profile(self) -> str:
        if self.profile_picker is not None:
            return self.profile_picker.currentText()
        return ""
