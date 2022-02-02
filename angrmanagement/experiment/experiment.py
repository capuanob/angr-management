import itertools
import logging
import os
import random
from collections import defaultdict
from enum import Enum
from hashlib import md5
from typing import List, Optional, Dict, Set, Tuple
from PySide2 import QtCore

from ..config import RES_LOCATION
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


class DataDepGroup(StudyGroup):
    """Enumerates the groups a user could be assigned to in the data dependency graph study"""
    DATA_DEP = 'A'
    NO_DATA_DEP = 'B'


class Study:
    """Defines a study in the overarching experiment and its properties"""

    def __init__(self, type_: StudyType, group: StudyGroup, challenges: List[str]):
        self.type_ = type_
        self.group = group
        self.challenges = challenges
        self._curr_chall = 0  # Points to current challenge

    @property
    def next_chall(self) -> Optional[str]:
        if self.is_complete():
            return None
        # Challenge is in bounds
        chall = self.challenges[self._curr_chall]
        self._curr_chall += 1
        return chall

    def is_complete(self) -> bool:
        # Whether there are any more challenges available for the given study
        return self._curr_chall < 0 or self._curr_chall >= len(self.challenges)


def _digest_encode(first_study: int, groups: str, chall_order: str) -> str:
    """
    Encodes digest according to first_study -> groups -> chall_order
    """
    cleartext = f"{first_study}{groups}{chall_order}"
    return md5(cleartext.encode()).hexdigest()


class RandomizedExperiment(QtCore.QObject):
    """
    Data structure used to track all the studies and their challenges in the current experiment
    """
    CHALLENGE_LOCATION = str(os.path.join(RES_LOCATION, 'challenges'))
    STUDY_COUNT = 2  # Number of independent studies in the experiment
    CHALLENGE_COUNT = 5  # Number of challenges per study
    GROUP_OPTIONS = ['A', 'B']  # Identifiers of groups per study

    # Signals
    experiment_completed = QtCore.Signal()
    digest_updated = QtCore.Signal()

    def __init__(self):
        super().__init__(QtCore.QCoreApplication.instance())

        self.workspace = None
        self._rainbow_table: Set[str] = set()  # All possible digests
        self._studies: List[Study] = []  # Collection of studies, with each study consisting of series of challenges
        self._experiment_digest: Optional[str] = None  # Encodes randomness, to sync with angr cloud
        self._challenge_order: List[int] = []  # Order that challenges should be shuffled to
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

        self._build_rainbow_table()

    def _generate_digest(self):
        """
        Generates an MD5 digest encoding the user's study order, group, and challenge order
        Format: <first study num><group char><shuffled challenge order>

        Example: If a user is assigned to perform the second study first, group A in study 1 and B in study 2,
        with the challenge order 5 -> 4 -> 2 -> 3 -> 1, then the following is output

        MD5(2AB54231)
        """

        challenge_order = [str(c) for c in range(self.CHALLENGE_COUNT)]
        random.shuffle(challenge_order)
        self._challenge_order = challenge_order

        self._first_study = random.randint(0, self.STUDY_COUNT - 1)

        groups = ''
        for study_num in range(self.STUDY_COUNT):
            study_group = random.choice(self.GROUP_OPTIONS)
            groups += study_group
            study_type = StudyType(study_num)
            study_group_cls = ProximityGroup if study_type is StudyType.PROXIMITY else DataDepGroup
            self._groups[study_type] = self._groups[study_type] = study_group_cls(study_group)

        chall_order = ''.join(challenge_order)
        self._experiment_digest = _digest_encode(self._first_study, groups, chall_order)

    def _build_rainbow_table(self):
        for first_study in range(0, self.STUDY_COUNT - 1):
            for g_perm in itertools.product(self.GROUP_OPTIONS, repeat=self.STUDY_COUNT):
                groups = ''.join(g_perm)
                for cord_perm in itertools.permutations(range(self.CHALLENGE_COUNT)):
                    chall_order = ''.join(str(i) for i in cord_perm)
                    self._rainbow_table.add(_digest_encode(first_study, groups, chall_order))

    def validate_digest(self, digest: str) -> bool:
        """
        Determines whether the digest matches a possible output of the current encoding scheme
        """
        return digest in self._rainbow_table

    def _load_challenges(self):
        if self.studies:
            # Challenges have already been initialized, no need to do it again
            return

        try:
            for dirpath, _, filenames in os.walk(self.CHALLENGE_LOCATION):
                if filenames:
                    # Figure out which study's directory is currently being processed
                    dir_name = os.path.basename(dirpath)
                    study_type = StudyType[dir_name.upper()]
                    study_group = self.groups[study_type]

                    # Order challenges according to reorder defined in digest
                    challenges = sorted([os.path.join(dirpath, fname) for fname in filenames])
                    challenges = [challenges[int(i)] for i in self._challenge_order]
                    self._studies.append(Study(study_type, study_group, challenges))

            # Shuffle studies according to reorder defined in digest
            curr_first_study = self._studies[0]
            if curr_first_study.type_ is not StudyType(self._first_study):
                # Need to swap
                self._studies[0] = self._studies[1]
                self._studies[1] = curr_first_study

        except (ValueError, OSError) as err:
            _l.critical("Unable to load challenge binaries")
            _l.critical(str(err))
            return

    @property
    def studies(self) -> Optional[List[Study]]:
        study_len = len(self._studies)

        if study_len not in [0, self.STUDY_COUNT]:
            _l.warning("Length of studies isn't equal to study count!")
        return self._studies if study_len != 0 else None

    @property
    def groups(self) -> Dict[StudyType, StudyGroup]:
        if not self._groups:
            self._generate_digest()
        return self._groups

    @property
    def digest(self) -> str:
        # lazy getter
        if not self._experiment_digest:
            self._generate_digest()
        return self._experiment_digest

    @digest.setter
    def digest(self, new_digest: str):
        if self.validate_digest(new_digest):
            self._experiment_digest = new_digest
            self.digest_updated.emit()

    @property
    def curr_study(self) -> Optional[Study]:
        if 0 <= self._curr_study_idx < len(self._studies):
            return self._studies[self._curr_study_idx]
        else:
            return None

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
        curr_study = self._studies[self._curr_study_idx]
        print(f"In study {curr_study.type_} group {curr_study.group}")
        if curr_study.is_complete():
            # Need to increment to next study
            self._curr_study_idx += 1
            if self.is_complete():
                # No more studies remain, experiment is done!
                self.experiment_completed.emit()
                return None
            else:
                self.workspace.update_usable_views(self.curr_study.type_, self.curr_study.group)
                return self._studies[self._curr_study_idx].next_chall
        else:
            return curr_study.next_chall

    def is_complete(self) -> bool:
        # Whether any unfinished studies remain
        return self._curr_study_idx < 0 or self._curr_study_idx >= len(self.studies)
