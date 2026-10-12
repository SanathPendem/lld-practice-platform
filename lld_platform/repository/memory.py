from threading import RLock
from typing import List, Optional, Dict
from lld_platform.domain.models import Attempt, Problem
from lld_platform.problems.catalog import Catalog
from lld_platform.repository.base import AttemptRepository, ProblemRepository


class InMemoryAttemptRepository(AttemptRepository):
    def __init__(self) -> None:
        self._lock = RLock()
        self._attempts: Dict[str, Attempt] = {}

    def save(self, attempt: Attempt) -> None:
        with self._lock:
            self._attempts[attempt.id] = attempt

    def get_by_id(self, attempt_id: str) -> Optional[Attempt]:
        with self._lock:
            return self._attempts.get(attempt_id)

    def list_by_learner_and_problem(self, learner_id: str, problem_id: str) -> List[Attempt]:
        with self._lock:
            matches = [
                att for att in self._attempts.values()
                if att.learner_id == learner_id and att.problem_id == problem_id
            ]
            matches.sort(key=lambda a: a.created_at)
            return matches

    def list_by_learner(self, learner_id: str) -> List[Attempt]:
        with self._lock:
            matches = [
                att for att in self._attempts.values()
                if att.learner_id == learner_id
            ]
            matches.sort(key=lambda a: a.created_at)
            return matches


class InMemoryProblemRepository(ProblemRepository):
    def __init__(self, catalog: Optional[Catalog] = None) -> None:
        self._catalog = catalog or Catalog()

    def get(self, problem_id: str) -> Optional[Problem]:
        return self._catalog.get(problem_id)

    def list_all(self) -> List[Problem]:
        return self._catalog.list_all()
