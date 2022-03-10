import logging
import logging
import os
import pickle
import time
from collections import defaultdict
from enum import Enum
from types import SimpleNamespace
from typing import List, Optional, Dict, Tuple

from PySide2 import QtCore

from ..ui import views

_l = logging.getLogger(name=__name__)


class StudyType(Enum):
    """ Enumerates the names of the studies in the experiment"""
    PROXIMITY = 0
    DATA_DEP = 1


class StudyGroup(Enum):
    """
    Abstract base class for study groups
    """


class ProximityGroup(StudyGroup):
    """Enumerates the groups a user could be assigned to in the proximity graph study"""
    PROXIMITY = 'A'
    NO_PROXIMITY = 'B'


ProximityChallenges = ["quad", "letters", "maze"]  # Original order of challenges for proximity


class DataDepGroup(StudyGroup):
    """Enumerates the groups a user could be assigned to in the data dependency graph study"""
    DATA_DEP = 'A'
    NO_DATA_DEP = 'B'


DataDepChallenges = ["middle", "follow", "notes"]  # Original order of challenges for data_dep


class Study:
    """Defines a study in the overarching experiment and its properties"""

    def __init__(self, type_: StudyType, group: StudyGroup, challenges: List[str]):
        self.type_ = type_
        self.group = group
        self.challenges = challenges
        self.curr_chall_idx = -1  # Points to current challenge

    @property
    def curr_chall(self) -> Optional[str]:
        if 0 <= self.curr_chall_idx < len(self.challenges):
            return self.challenges[self.curr_chall_idx]
        else:
            return None

    @property
    def next_chall(self) -> Optional[str]:
        if self.is_complete():
            return None
        # Challenge is in bounds
        chall = self.challenges[self.curr_chall_idx + 1]
        return chall

    def is_complete(self) -> bool:
        # Whether there are any more challenges available for the given study
        return self.curr_chall_idx >= len(self.challenges) - 1


class RandomizedExperiment(QtCore.QObject):
    """
    Data structure used to track all the studies and their challenges in the current experiment
    """
    DOCUMENT_LOCATION = str(os.path.join(os.path.expanduser('~'), 'Documents'))
    CHALLENGE_LOCATION = str(os.path.join(os.path.expanduser('~'), 'Desktop', 'challenges'))
    PLOG_LOCATION = str(os.path.join(DOCUMENT_LOCATION, '.plog'))
    DLOG_LOCATION = str(os.path.join(DOCUMENT_LOCATION, '.dlog'))
    STUDY_COUNT = 2  # Number of independent studies in the experiment
    CHALLENGE_COUNT = 3  # Number of challenges per study
    GROUP_OPTIONS = ['A', 'B']  # Identifiers of groups per study

    # Signals
    experiment_completed = QtCore.Signal()

    def __init__(self):
        super().__init__(QtCore.QCoreApplication.instance())

        self.workspace = None
        self._studies: List[Study] = []  # Collection of studies, with each study consisting of series of challenges
        self._experiment_digest: Optional[str] = None  # Encodes randomness, to sync with angr cloud
        self._prox_challenge_order: List[int] = []  # Order of proximity challenges
        self._data_dep_challenge_order: List[int] = []  # order of data dep challenges
        self._first_study: int = 0
        self._groups: Dict[StudyType, StudyGroup] = {}  # Group user will be a member of per study
        self._curr_study_idx = 0  # Index of study currently being conducted

        # Maps study type and study group to enabled categories
        self.enabled_views: Dict[Tuple[StudyType, StudyGroup], frozenset] = {
            (StudyType.PROXIMITY, ProximityGroup.PROXIMITY): frozenset([
                'functions',
                'disassembly',
                'hex',
                'proximity',
                'strings',
                'patches',
                'symexec',
                'states',
                'interaction',
                'console',
                'log',
            ]),
            (StudyType.PROXIMITY, ProximityGroup.NO_PROXIMITY): frozenset([
                'functions',
                'disassembly',
                'hex',
                'strings',
                'patches',
                'symexec',
                'states',
                'interaction',
                'console',
                'log',
            ]),
            (StudyType.DATA_DEP, DataDepGroup.DATA_DEP): frozenset([
                'functions',
                'disassembly',
                'data_dependency',
                'hex',
                'strings',
                'patches',
                'symexec',
                'states',
                'interaction',
                'console',
                'log',
            ]),
            (StudyType.DATA_DEP, DataDepGroup.NO_DATA_DEP): frozenset([
                'functions',
                'disassembly',
                'hex',
                'strings',
                'patches',
                'symexec',
                'states',
                'interaction',
                'console',
                'log',
            ]),
        }

        # Used to save views that have been removed from the workspace for (possible) re-adding later
        self.view_cache: Dict[str, List[Tuple[views.BaseView, Optional[object]]]] = defaultdict(list)

        self._load_digest()
        self._recover_from_log_file()

    def _update_log_file(self, curr_chall_idx):
        """Maintains participant's progress in the experiment in the case of a crash"""
        if os.path.exists(self.CHALLENGE_LOCATION):
            with open(self.PLOG_LOCATION, 'wb+') as f:
                pickle.dump({
                    'chall_idx': curr_chall_idx,
                    'study_idx': self._curr_study_idx,
                    'studies': self.studies,
                }, f)
        else:
            _l.error("No challenge directory exists!")

    def _recover_from_log_file(self):
        """If a log file exists, recover experiment state using it"""
        if os.path.exists(self.PLOG_LOCATION):
            try:
                with open(self.PLOG_LOCATION, 'rb') as f:
                    log_json = SimpleNamespace(**pickle.load(f))
                    self._studies = log_json.studies
                    self._curr_study_idx = log_json.study_idx
                    self.curr_study.curr_chall_idx = max(-1, log_json.chall_idx - 1)
            except (KeyError, AttributeError):
                # Get rid of corrupt log file and let them restart experiment
                _l.error("Incorrect log file format!")
                os.unlink(self.PLOG_LOCATION)

    def _load_digest(self):
        # Loads digest from dlog (waits until file exists)
        dlog_exists = False
        while not dlog_exists:
            dlog_exists = os.path.exists(self.DLOG_LOCATION)
            if not dlog_exists:
                time.sleep(2)

        with open(self.DLOG_LOCATION, 'rb') as f:
            self._experiment_digest = pickle.load(f)

        self._first_study = int(not self._experiment_digest['is_proximity_first'])  # Convert from boolean to int
        self._groups[StudyType.PROXIMITY] = ProximityGroup.NO_PROXIMITY if self._experiment_digest[
            'is_proximity_control'] else ProximityGroup.PROXIMITY
        self._groups[StudyType.DATA_DEP] = DataDepGroup.NO_DATA_DEP if self._experiment_digest[
            'is_data_dep_control'] else DataDepGroup.DATA_DEP
        self._prox_challenge_order = self._experiment_digest['prox_challenge_order']
        self._data_dep_challenge_order = self._experiment_digest['data_dep_challenge_order']

    def _load_challenges(self):
        if self.studies:
            # Challenges have already been initialized, no need to do it again
            return

        # Align data dep and proximity challenges according to digest order
        prox_chall_paths = [os.path.join(self.CHALLENGE_LOCATION, ch) for ch in ProximityChallenges]
        data_dep_chall_paths = [os.path.join(self.CHALLENGE_LOCATION, ch) for ch in DataDepChallenges]
        prox_challs = [prox_chall_paths[i] for i in self._prox_challenge_order]
        data_dep_challs = [data_dep_chall_paths[i] for i in self._data_dep_challenge_order]

        self._studies.append(Study(StudyType.PROXIMITY, self.groups[StudyType.PROXIMITY], prox_challs))
        self._studies.append(Study(StudyType.DATA_DEP, self.groups[StudyType.DATA_DEP], data_dep_challs))

        # Shuffle studies according to reorder defined in digest
        curr_first_study = self._studies[0]
        if curr_first_study.type_ is not StudyType(self._first_study):
            # Need to swap
            self._studies[0] = self._studies[1]
            self._studies[1] = curr_first_study

    @property
    def studies(self) -> Optional[List[Study]]:
        study_len = len(self._studies)

        if study_len not in [0, self.STUDY_COUNT]:
            _l.warning("Length of studies isn't equal to study count!")
        return self._studies if study_len != 0 else None

    @property
    def groups(self) -> Dict[StudyType, StudyGroup]:
        return self._groups

    @property
    def digest(self) -> str:
        return self._experiment_digest

    @property
    def curr_study(self) -> Optional[Study]:
        if 0 <= self._curr_study_idx < len(self._studies):
            return self._studies[self._curr_study_idx]
        else:
            return None

    def increment_challenge(self):
        self.curr_study.curr_chall_idx += 1

    @property
    def next_chall(self) -> Optional[str]:
        """
        Returns the path to the next challenge binary, if it exists.
        """

        if not self.studies:
            self._load_challenges()
            if self.workspace:
                self.workspace.update_usable_views(self.curr_study.type_, self.curr_study.group)
        elif self.is_complete():
            return None

        if self.curr_study.is_complete():
            # Need to increment to next study
            self._curr_study_idx += 1
            if self.is_complete():
                # No more studies remain, experiment is done!
                if os.path.exists(self.PLOG_LOCATION):
                    os.unlink(self.PLOG_LOCATION)

                self.experiment_completed.emit()
                return None
            else:
                self.workspace.update_usable_views(self.curr_study.type_, self.curr_study.group)
                next_chall = self.curr_study.next_chall
                self._update_log_file(self.curr_study.curr_chall_idx)
                return next_chall
        else:
            next_chall = self.curr_study.next_chall
            self._update_log_file(self.curr_study.curr_chall_idx)
            return next_chall

    @property
    def trace_file(self) -> Optional[str]:
        """
        Args:
            chall_path: Challenge to get the trace file for, if it exists.

        Returns: The path to the trace file, if it exists. Otherwise, None

        """
        chall_path = self.curr_study.curr_chall
        if not chall_path:
            return None

        challenge_name = os.path.basename(chall_path).split('.')[0]
        trace_path = os.path.join(self.CHALLENGE_LOCATION, challenge_name + '.trace')
        return trace_path if os.path.exists(trace_path) else None

    def is_complete(self) -> bool:
        # Whether any unfinished studies remain
        return self._curr_study_idx < 0 or self._curr_study_idx >= len(self.studies)

    def allow_view(self, category: str) -> bool:
        # Whether or not the view should be allowed to load for the given function
        curr_study = self.curr_study
        return curr_study is not None and category in self.enabled_views[(curr_study.type_, curr_study.group)]
