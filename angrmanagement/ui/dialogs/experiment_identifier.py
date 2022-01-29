from PySide2 import QtWidgets, QtGui
from PySide2.QtCore import Qt, Slot, Signal

from angrmanagement.experiment import Experiment_manager


class OverrideView(QtWidgets.QWidget):
    """Widget to display to facilitate an override"""

    override_success = Signal()  # Emitted on a successful digest override

    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)

        self._override_text_field = QtWidgets.QLineEdit()
        self._override_btn = QtWidgets.QPushButton("Override")
        self._override_error = QtWidgets.QLabel()

        self._layout_manager = QtWidgets.QVBoxLayout(self)

        # Connect signals to slots
        self._override_btn.clicked.connect(self._on_override_click)

        self._layout_widgets()

    def _layout_widgets(self):
        info_lbl = QtWidgets.QLabel(
            "Warning! Only override the experiment digest with a previously generated digest.\n"
            "That means that this feature should only be used if angr management was closed mid-experiment."
        )
        self._override_text_field.setPlaceholderText("Previously generated digest")
        self._override_error.setStyleSheet(self.styleSheet() + "color: red;")
        self._override_error.hide()

        self._layout_manager.addWidget(info_lbl, 0, Qt.AlignCenter)
        self._layout_manager.addSpacing(7)
        self._layout_manager.addWidget(self._override_text_field)
        self._layout_manager.addSpacing(25)
        self._layout_manager.addWidget(self._override_btn)
        self._layout_manager.addWidget(self._override_error)

    @Slot()
    def _on_override_click(self):
        self._override_error.hide()

        input_digest = self._override_text_field.text()
        if Experiment_manager.validate_digest(input_digest):
            Experiment_manager.digest = input_digest
            self.override_success.emit()
        else:
            self._override_error.show()
            self._override_error.setText("Provided digest isn't properly formatted!")


class DigestView(QtWidgets.QWidget):
    """Default view for ExperimentIdentifier"""

    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)

        self._digest_text_field = QtWidgets.QLineEdit(Experiment_manager.digest)
        self._copy_btn = QtWidgets.QPushButton("Copy")
        self.done_btn = QtWidgets.QPushButton("Done")
        self._layout_manager = QtWidgets.QVBoxLayout(self)
        self._system_clipboard = QtWidgets.QApplication.clipboard()

        # Connect signals to slots
        self._copy_btn.clicked.connect(lambda: self._system_clipboard.setText(self._digest_text_field.text()))
        Experiment_manager.digest_updated.connect(lambda: self._digest_text_field.setText(Experiment_manager.digest))

        self._layout_widgets()

    def _layout_widgets(self):
        welcome_lbl = QtWidgets.QLabel("Thank you for your participation!")
        instruction_lbl = QtWidgets.QLabel("Before proceeding, please copy the following digest into the angr cloud "
                                           "survey")
        self._digest_text_field.setReadOnly(True)
        self._digest_text_field.setAlignment(Qt.AlignCenter)

        # Ensure digest is at least long enough to display text
        digest_txt = self._digest_text_field.text()
        fm = QtGui.QFontMetrics(self._digest_text_field.font())
        pixel_width = fm.width(digest_txt) + 20
        self._digest_text_field.setMinimumWidth(pixel_width)

        self._layout_manager.addWidget(welcome_lbl, 0, Qt.AlignHCenter)
        self._layout_manager.addWidget(instruction_lbl, 1, Qt.AlignHCenter)
        self._layout_manager.addSpacing(7)
        h_layout = QtWidgets.QHBoxLayout()
        h_layout.addWidget(self._digest_text_field)
        h_layout.addWidget(self._copy_btn)
        self._layout_manager.addLayout(h_layout, 1)
        self._layout_manager.addSpacing(25)
        self._layout_manager.addWidget(self.done_btn)


class ExperimentIdentifier(QtWidgets.QDialog):
    """
    Used to generate a digest presented to the user that encodes the order of studies, challenges, and group number
    Used to sync with Angr Cloud
    """
    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)
        self.setWindowTitle("Sync with angr cloud")
        self.setModal(True)

        self._default_view = DigestView(self)
        self._override_view = OverrideView(self)
        self._layout_manager = QtWidgets.QVBoxLayout(self)

        self._advanced_btn = QtWidgets.QPushButton("Advanced")
        self._go_back_btn = QtWidgets.QPushButton("Go back")

        # Connect signals to slots
        self._default_view.done_btn.clicked.connect(self.accept)
        self._override_view.override_success.connect(self.accept)
        self._advanced_btn.clicked.connect(self._on_view_switch_click)
        self._go_back_btn.clicked.connect(self._on_view_switch_click)
        self._layout_widgets()

    def _layout_widgets(self):
        self._override_view.hide()
        self._go_back_btn.hide()
        self._advanced_btn.setStyleSheet(self.styleSheet() + "color: #89CFF0; border: 0px;")
        self._go_back_btn.setStyleSheet(self.styleSheet() + "color: #89CFF0; border: 0px;")

        self._layout_manager.addWidget(self._default_view)
        self._layout_manager.addWidget(self._override_view)
        self._layout_manager.addStretch()
        self._layout_manager.addWidget(self._advanced_btn, 0, Qt.AlignRight)
        self._layout_manager.addWidget(self._go_back_btn, 0, Qt.AlignRight)

    @Slot()
    def _on_view_switch_click(self):
        self._default_view.setHidden(not self._default_view.isHidden())
        self._override_view.setHidden(not self._override_view.isHidden())
        self._advanced_btn.setHidden(not self._advanced_btn.isHidden())
        self._go_back_btn.setHidden(not self._go_back_btn.isHidden())