import os
import logging
import random
from pathlib import Path
from PySide2 import QtCore
from PySide2.QtCore import Slot
from ..config import RES_LOCATION
from typing import List, Optional
from hashlib import md5

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
    STUDY_COUNT = 2  # Number of independent studies in the experiment
    CHALLENGE_COUNT = 5  # Number of challenges per study
    GROUP_OPTIONS = ['A', 'B']  # Identifiers of groups per study

    def __init__(self, experiment_path: str):
        self._studies: List[Study] = []
        self._experiment_digest: Optional[str] = None

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

    def _generate_digest(self) -> str:
        """
        Generates an MD5 digest encoding the user's study order, group, and challenge order
        Format: <experiment ID><group char><shuffled challenge order>

        Example: If a user is assigned to perform the second study first, as group A, with the challenge order
        5 -> 4 -> 2 -> 3 -> 1, then the following is output

        MD5(1A54231)
        """
        challenge_order = [str(c) for c in range(self.CHALLENGE_COUNT)]
        random.shuffle(challenge_order)

        first_study = random.randint(0, self.STUDY_COUNT)
        group = random.choice(self.GROUP_OPTIONS)
        chall_order = ''.join(challenge_order)
        cleartext = f"{first_study}{group}{chall_order}"
        return md5(cleartext.encode()).hexdigest()

    @property
    def digest(self) -> str:
        # lazy getter
        if not self._experiment_digest:
            self._experiment_digest = self._generate_digest()
        return self._experiment_digest

    @property
    def next_chall(self) -> Optional[str]:
        """
        Returns the path to the next challenge binary, if it exists.
        """
        pass


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

    @property
    def experiment_digest(self) -> str:
        return self._experiment.digest

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
