from abc import ABC, abstractmethod
from typing import List, Optional
from lld_platform.domain.models import Attempt, Problem


class AttemptRepository(ABC):
    @abstractmethod
    def save(self, attempt: Attempt) -> None:
        """Persist or update an attempt."""
        pass

    @abstractmethod
    def get_by_id(self, attempt_id: str) -> Optional[Attempt]:
        """Fetch attempt by its unique id."""
        pass

    @abstractmethod
    def list_by_learner_and_problem(self, learner_id: str, problem_id: str) -> List[Attempt]:
        """Fetch all attempts for a given learner and problem in chronological order."""
        pass

    @abstractmethod
    def list_by_learner(self, learner_id: str) -> List[Attempt]:
        """Fetch all attempts for a given learner."""
        pass


class ProblemRepository(ABC):
    @abstractmethod
    def get(self, problem_id: str) -> Optional[Problem]:
        pass

    @abstractmethod
    def list_all(self) -> List[Problem]:
        pass
