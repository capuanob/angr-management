
import os

from PySide2.QtGui import QIcon

from ...config import IMG_LOCATION
from .toolbar import Toolbar, ToolbarAction


class FileToolbar(Toolbar):
    def __init__(self, main_window):
        super(FileToolbar, self).__init__(main_window, 'File')

        self.actions = [
            ToolbarAction(QIcon(os.path.join(IMG_LOCATION, 'toolbar-file-open.ico')),
                          "Load Next Challenge", "Automatically load the next challenge",
                          main_window.load_next_experiment_challenge,
                          ),
            ToolbarAction(QIcon(os.path.join(IMG_LOCATION, 'toolbar-docker-open.png')),
                          "Open Docker Target", "Open a file located within a docker image for analysis",
                          main_window.open_docker_button,
                          ),
            ToolbarAction(QIcon(os.path.join(IMG_LOCATION, 'toolbar-file-save.png')),
                          "Save", "Save angr database",
                          main_window.save_database,
                          ),
        ]
