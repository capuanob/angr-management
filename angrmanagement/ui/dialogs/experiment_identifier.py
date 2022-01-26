from PySide2 import QtWidgets, QtGui
from PySide2.QtCore import Qt

from angrmanagement.experiment import Experiment_manager


class ExperimentIdentifier(QtWidgets.QDialog):
    """
    Used to generate a digest presented to the user that encodes the order of studies, challenges, and group number
    Used to sync with Angr Cloud
    """

    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)
        self.setWindowTitle("Sync with angr cloud")
        self.setModal(True)

        self._digest_text_field = QtWidgets.QLineEdit(Experiment_manager.digest)
        self._copy_btn = QtWidgets.QPushButton("Copy")
        self._done_btn = QtWidgets.QPushButton("Done")
        self._layout_manager = QtWidgets.QVBoxLayout(self)
        self._system_clipboard = QtWidgets.QApplication.clipboard()

        # Connect signals to slots
        self._done_btn.clicked.connect(self.accept)
        self._copy_btn.clicked.connect(lambda: self._system_clipboard.setText(self._digest_text_field.text()))
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
        self._layout_manager.addWidget(self._done_btn)
