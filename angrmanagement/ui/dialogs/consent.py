from PySide2 import QtWidgets, QtCore
from PySide2.QtCore import Slot

from angrmanagement.experiment import Experiment_manager


class ConsentForm(QtWidgets.QDialog):
    """
    Used in experiments to display the IRB-approved consent form and prevent the participant from proceeding to the
    experiment before agreeing with the consent form
    """

    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)

        self.setModal(True)  # Can not feed input to rest of workspace until consent
        self.setWindowTitle("Consent Form")

        self._layout_manager = QtWidgets.QVBoxLayout(self)
        self._name_field = QtWidgets.QLineEdit()
        self._agree_radio = QtWidgets.QRadioButton()
        self._submit_btn = QtWidgets.QPushButton("Submit")

        # Connect signals to slots
        self._submit_btn.clicked.connect(self._on_submit_clicked)

        self._layout_widgets()

    def _layout_widgets(self):
        header_lbl = QtWidgets.QLabel("Consent Form")
        form_field = QtWidgets.QTextEdit()
        form_field.setText("""
        We are graduate students under the direction of Professor Fish Wang and Professor Adam Doupe in the School of Computing and Augmented Intelligence (SCAI) at Arizona State University.  We are conducting a research study to evaluate the effectiveness of two new angr analyses, a data dependency graph and a proximity control flow graph, that aim to aid the reverse-engineer, vulnerability analyst, and software developer in reducing task-time and elucidating program behavior.  

We are inviting your participation in two different studies in which you will go through 7 challenges in the duration of 70 minutes (10 minutes per challenge), including an introduction and survey portion. This will total to 14 challenges, 2 introductions and 2 surveys in the time frame of 3 hours (180 minutes). The two studies are categorized as 1) reverse-engineering and 2) debugging and exploitation.

Introduction Phases
For each study, the 10 minute introduction phase will include instructions for the subsequent challenge-solving phase, and an overview of the angr views you are permitted to use. 

Challenge Phases
For the reverse-engineering study, you will need to determine a given input to output the flag, confirming the challenge has been solved. For the debugging and exploitation study, you will be tasked with identifying the bugs in a set of crashing binaries and identifying vulnerabilities in various challenges.  Each challenge will be hard capped at 10 minutes forcing you to move on to subsequent challenges. However, challenges are encouraged to be completed in the least amount of time possible. In order to move on to the next challenge, you will be asked to provide a free-form “answer” to the current challenge. 

Survey Phases
In the last 10 minute survey phase, you will be asked to answer various questions about your own perceived ability, the challenges themselves, and your perspectives on the angr analyses you were allowed to utilize.  

You have the right not to answer any question, and to stop participation at any time. Your participation in this study is voluntary.  If you choose not to participate or to withdraw from the study at any time, there will be no penalty, however the $50 Amazon Gift card compensation will not be received. You must be 18 or older to participate in the study.

In addition to the compensation mentioned above ($50 Amazon Gift Card), participation will give you the opportunity to further practice and improve your skills in regards to binary analysis, reverse-engineering, and debugging. Since angr management is an experimental research platform, there is a minimal risk that something could go wrong on your computer during the experiment portion of the study. 
Additionally, since the experiment will record your computer to gather data for the experiment portion, there is a risk that private or sensitive information could be leaked to the research team. To address this risk, you should disable notifications and close any sensitive windows or other open processes before participating in the experiment. 

Your identity will only be known by the research team. This information will be confidential. The results of this study may be used in reports, presentations, or publications but your name will not be used. Results will only be shared in the aggregate form. 

This experiment will be recorded with your permission. If you do not wish to be recorded, please let the research team know prior to your participation. You are free to change your mind at any point of participation, but compensation will not be provided for your participation. 

If you have any questions concerning the research study, please contact the research team at: Bailey Capuano (bcapuano@asu.edu), Sean Smits (ssmits@asu.edu), Professor Fish Wang (fishw@asu.edu) or Professor Adam Doupe (doupe@asu.edu). If you have any questions about your rights as a subject/participant in this research, or if you feel you have been placed at risk, you can contact the Chair of the Human Subjects Institutional Review Board, through the ASU Office of Research Integrity and Assurance, at (480) 965-6788.
        """)
        form_field.setReadOnly(True)
        self._name_field.setPlaceholderText("Your name")

        sub_layout = QtWidgets.QFormLayout()
        self._layout_manager.addWidget(header_lbl, 0, QtCore.Qt.AlignHCenter)
        self._layout_manager.addWidget(form_field, 1)
        sub_layout.addRow("First and last name:", self._name_field)
        sub_layout.addRow("I hereby accept that I have read and will abide by the specification above:",
                          self._agree_radio)
        self._layout_manager.addLayout(sub_layout, 0)
        self._layout_manager.addWidget(self._submit_btn)

    def sizeHint(self) -> QtCore.QSize:
        return QtCore.QSize(600, 900)

    #
    # Slots
    #

    def reject(self):
        # Can not proceed without consent
        QtCore.QCoreApplication.quit()

    @Slot()
    def _on_submit_clicked(self):
        """
        Triggered when the submit QPushButton is clicked
        """
        if self._agree_radio.isChecked() and self._name_field.text():
            # TODO: Save this information off to the server
            Experiment_manager.start()
            self.accept()
        elif not self._agree_radio.isChecked():
            self.reject()
