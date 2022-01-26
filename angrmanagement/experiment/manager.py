import os
import logging
import random
from pathlib import Path
from PySide2 import QtCore
from PySide2.QtCore import Slot
from ..config import RES_LOCATION
from typing import List

_l = logging.getLogger(name=__name__)


class Study:
    """
    Collection of challenges
    """
    def __init__(self, introduction_video: str, challenges: List[str]):
        self.introduction_video = introduction_video
        self.challenges = challenges
        random.shuffle(self.challenges)  # Shuffle the order of challenge presentations

class RandomizedExperiment:
    """
    Data structure used to track all the studies and their challenges in the current experiment
    """

    def __init__(self, experiment_path: str):
        self._studies: List[Study] = []

        try:
            for dirpath, _, filenames in os.walk(experiment_path):
                intro_path = ''
                challenges = []
                for fname in filenames:
                    full_path = Path(os.path.join(dirpath, fname))
                    if full_path.suffix == '.mp4':
                        intro_path = str(full_path)
                    else:
                        challenges.append(str(full_path))

                self._studies.append(Study(intro_path, challenges))
            random.shuffle(self._studies)  # Present user with studies in a randomized order
        except OSError as err:
            _l.critical("Unable to load challenge binaries")
            _l.critical(str(err))
            return

    @property
    def next_chall(self) -> Optional[str]:
        """
        Returns the path to the next challenge binary, if it exists.
        """


class ExperimentManager(QtCore.QObject):
    """
    Responsible for keeping state of the current experiment and handling the loading of binaries in the proper order
    """
    CHALLENGE_TIME = 1 * 60_000  # 10 minutes in milliseconds
    CHALLENGE_LOCATION = str(os.path.join(RES_LOCATION, 'challenges'))

    def __init__(self):
        super().__init__(None)

        self._experiment = RandomizedExperiment(self.CHALLENGE_LOCATION)
        self._timer = QtCore.QTimer(self)  # Create a timer that is triggered on the specified interval

        # Connect signals to slots
        self._timer.timeout.connect(self._on_challenge_timeout)

    def _load_next_challenge(self):
        """
        Loads the next challenge
        """

    def start(self):
        """
        Manager begins challenge phase and oversees progress
        """
        self._timer.start(self.CHALLENGE_TIME)

    @Slot()
    def _on_challenge_timeout(self):
        print("Challenge time is over!")
